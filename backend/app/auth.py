"""
鉴权核心：密码哈希 + JWT + get_current_user 依赖
- 全链路多层降级，避免龙芯/无网环境第三方库装不上就崩
"""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User
from .users import ROLE_LABELS, ROLE_MANAGER, ROLE_SYSADMIN


# ============================================================
# 1. 密码哈希（passlib 优先 → pbkdf2 纯 Python 兜底）
# ============================================================
_PWD_CONTEXT = None
_PWD_METHOD = None

try:
    from passlib.context import CryptContext
    # bcrypt 优先，pbkdf2_sha256 兜底（纯 Python，龙芯 100% 能跑）
    _PWD_CONTEXT = CryptContext(
        schemes=["pbkdf2_sha256", "bcrypt"],
        deprecated="auto",
        bcrypt__rounds=10,
        pbkdf2_sha256__default_rounds=100_000,
    )
    # 健康检查：新版 bcrypt + passlib 的 detect_wrap_bug 会在 hash 时抛 ValueError，
    # 这里提前试一次，失败就直接放弃 passlib 走纯 Python pbkdf2
    try:
        _test = _PWD_CONTEXT.hash("healthcheck_pwd_123")
        if not _test:
            raise RuntimeError("empty hash")
        _PWD_METHOD = "passlib"
    except Exception:
        _PWD_CONTEXT = None
        _PWD_METHOD = "pbkdf2-raw"
except Exception:
    _PWD_CONTEXT = None
    _PWD_METHOD = "pbkdf2-raw"


def hash_password(raw: str) -> str:
    if not raw:
        raise ValueError("密码不能为空")
    if _PWD_CONTEXT is not None and _PWD_METHOD == "passlib":
        return _PWD_CONTEXT.hash(raw)
    # 纯 Python pbkdf2 兜底：sha256 + 100k 迭代 + 16 字节随机盐
    import hashlib
    import os
    import base64
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", raw.encode("utf-8"), salt, 100_000)
    # 存格式：pbkdf2-sha256$100000${salt_b64}${hash_b64}
    salt_b64 = base64.b64encode(salt).decode("ascii")
    dk_b64 = base64.b64encode(dk).decode("ascii")
    return f"pbkdf2-sha256$100000${salt_b64}${dk_b64}"


def verify_password(raw: str, hashed: str) -> bool:
    if not raw or not hashed:
        return False
    try:
        if _PWD_CONTEXT is not None and (
            hashed.startswith("$2") or hashed.startswith("$pbkdf2")
        ):
            return bool(_PWD_CONTEXT.verify(raw, hashed))
    except Exception:
        pass
    # 兜底：解析 pbkdf2-sha256 格式自己验证
    try:
        if hashed.startswith("pbkdf2-sha256$"):
            import hashlib
            import base64
            parts = hashed.split("$")
            if len(parts) != 4:
                return False
            _, iters_str, salt_b64, dk_b64 = parts
            iters = int(iters_str)
            salt = base64.b64decode(salt_b64)
            expected = base64.b64decode(dk_b64)
            dk = hashlib.pbkdf2_hmac("sha256", raw.encode("utf-8"), salt, iters)
            # 恒定时间比较，避免时序攻击
            if len(dk) != len(expected):
                return False
            acc = 0
            for a, b in zip(dk, expected):
                acc |= a ^ b
            return acc == 0
    except Exception:
        pass
    return False


# ============================================================
# 2. JWT（jose 优先 → 手写 HMAC 兜底）
# ============================================================
_JWT_METHOD = "jose"
try:
    from jose import JWTError, jwt as _jose_jwt
except Exception:
    _jose_jwt = None  # type: ignore
    JWTError = Exception  # type: ignore
    _JWT_METHOD = "hmac-raw"


def _payload_expire() -> int:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    return int(exp.timestamp())


def create_access_token(username: str, role: str, extra: Optional[dict] = None) -> tuple[str, int]:
    """返回 (token, expires_in_hours)"""
    payload = {
        "sub": username,
        "role": role,
        "exp": _payload_expire(),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    if extra:
        payload.update(extra)

    if _jose_jwt is not None and _JWT_METHOD == "jose":
        token = _jose_jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token, settings.ACCESS_TOKEN_EXPIRE_HOURS

    # 纯 Python HMAC-SHA256 手写 JWT（jose 装不上时兜底，够用比赛）
    import json, hmac, hashlib, base64
    def _b64url(obj_bytes: bytes) -> str:
        return base64.urlsafe_b64encode(obj_bytes).rstrip(b"=").decode("ascii")
    header = {"alg": "HS256", "typ": "JWT"}
    h_b = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p_b = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing = f"{h_b}.{p_b}".encode("utf-8")
    sig = hmac.new(
        settings.SECRET_KEY.encode("utf-8"), signing, hashlib.sha256
    ).digest()
    s_b = _b64url(sig)
    return f"{h_b}.{p_b}.{s_b}", settings.ACCESS_TOKEN_EXPIRE_HOURS


def decode_access_token(token: str) -> Optional[dict]:
    """解析失败返回 None，不抛异常"""
    if not token:
        return None
    try:
        if _jose_jwt is not None and _JWT_METHOD == "jose":
            payload = _jose_jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
    except Exception:
        # 尝试走手写 HMAC 兜底
        pass
    try:
        import json, hmac, hashlib, base64
        parts = token.split(".")
        if len(parts) != 3:
            return None
        def _b64url_decode(s: str) -> bytes:
            pad = "=" * ((4 - len(s) % 4) % 4)
            return base64.urlsafe_b64decode((s + pad).encode("ascii"))
        header = json.loads(_b64url_decode(parts[0]))
        alg = (header or {}).get("alg", "")
        if alg != "HS256":
            return None
        payload = json.loads(_b64url_decode(parts[1]))
        # 验签
        signing = f"{parts[0]}.{parts[1]}".encode("utf-8")
        exp_sig = hmac.new(
            settings.SECRET_KEY.encode("utf-8"), signing, hashlib.sha256
        ).digest()
        actual_sig = _b64url_decode(parts[2])
        if len(exp_sig) != len(actual_sig):
            return None
        acc = 0
        for a, b in zip(exp_sig, actual_sig):
            acc |= a ^ b
        if acc != 0:
            return None
        # 过期判断
        exp = payload.get("exp")
        if exp and int(exp) < int(datetime.now(timezone.utc).timestamp()):
            return None
        return payload
    except Exception:
        return None


# ============================================================
# 3. FastAPI 依赖：get_current_user
# ============================================================
class OptionalHTTPBearer(HTTPBearer):
    """即使用户没带 Authorization 也别直接 403，交给下游判断"""
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        try:
            return await super().__call__(request)
        except HTTPException:
            return None


_bearer = OptionalHTTPBearer(auto_error=False)


_UNAUTH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="登录已过期或未登录",
    headers={"WWW-Authenticate": "Bearer"},
)


def role_label_of(role: str) -> str:
    return ROLE_LABELS.get(role, role or "未知角色")


def is_admin_role(role: str) -> bool:
    return role in (ROLE_MANAGER, ROLE_SYSADMIN)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """依赖：必须登录。未登录或 token 无效直接 401"""
    if not credentials or not credentials.scheme.lower() == "bearer" or not credentials.credentials:
        raise _UNAUTH
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise _UNAUTH
    username = str(payload["sub"])
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise _UNAUTH
    exp = payload.get("exp")
    if exp and int(exp) < int(datetime.now(timezone.utc).timestamp()):
        raise _UNAUTH
    return user


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """依赖：可选登录。token 对就返回 User，不对或没有就返回 None（方便公开接口）"""
    if not credentials or not credentials.scheme.lower() == "bearer" or not credentials.credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    username = str(payload["sub"])
    user = db.query(User).filter(User.username == username).first()
    return user


def require_admin(user: User) -> None:
    """校验管理员，否则 403"""
    if not is_admin_role(user.role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="该操作需要维修管理员权限",
        )
