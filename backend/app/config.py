"""
统一配置管理（参考 cup-team-main 架构）
使用 pydantic-settings 从 .env 读取，类型安全 + 默认值齐全
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from pydantic import field_validator
except Exception:  # pydantic v1 兼容
    field_validator = None
    try:
        from pydantic import validator as field_validator  # type: ignore
    except Exception:
        pass

try:
    from pydantic_settings import BaseSettings
except Exception:  # 没有 pydantic-settings 时，回退到 BaseModel + 手动读
    try:
        from pydantic import BaseModel as BaseSettings  # type: ignore
    except Exception:
        BaseSettings = object  # type: ignore

try:
    import json as _json
except Exception:
    _json = None


def _find_env_file() -> Optional[str]:
    """兼容多种场景查找 .env"""
    here = Path(__file__).resolve()               # backend/app/config.py
    candidates = [
        here.parent.parent.parent / ".env",      # project 根
        here.parent.parent / ".env",             # backend
        here.parent.parent.parent / "deploy" / ".env",  # deploy 目录
    ]
    for p in candidates:
        if p.is_file():
            return str(p)
    return None


_ENV_FILE = _find_env_file()


def _parse_json_list(raw: Any) -> List[str]:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            if _json:
                return _json.loads(raw)
        except Exception:
            # 兼容逗号分隔
            return [s.strip() for s in raw.split(",") if s.strip()]
    return ["http://localhost:8000", "http://localhost:3000"]


class Settings(BaseSettings):
    # 运行环境
    ENVIRONMENT: str = "production"
    DEBUG: bool = False                 # 你业务代码使用
    APP_DEBUG: bool = False             # 队友模型代码使用，保持共存

    # API 服务
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # 安全（比赛项目默认密钥，环境变量可覆盖）
    SECRET_KEY: str = "equipai-secret-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 168  # 7 天，比赛够用

    # SQLite 数据库（相对 backend/ 目录，换盘符换系统都不炸）
    DB_FILENAME: str = "equipai.db"

    @property
    def database_url(self) -> str:
        here = Path(__file__).resolve().parent  # backend/app/
        db_path = here.parent / self.DB_FILENAME  # backend/equipai.db
        return f"sqlite:///{db_path.as_posix()}"

    # ====== 数据存储 / RAG 文档上传（按队友 .env.example 补全配置）======
    # 留空时默认使用项目根目录下 data/
    DATA_DIR: str = ""
    DATABASE_PATH: str = ""
    DOCUMENT_UPLOAD_DIR: str = ""
    MAX_DOCUMENT_UPLOAD_MB: int = 100
    AUTO_IMPORT_KNOWLEDGE: bool = True
    BUILTIN_KNOWLEDGE_DIR: str = ""

    @property
    def data_dir_path(self) -> Path:
        if self.DATA_DIR:
            return Path(self.DATA_DIR).expanduser().resolve()
        return Path(__file__).resolve().parent.parent.parent / "data"

    @property
    def upload_dir_path(self) -> Path:
        if self.DOCUMENT_UPLOAD_DIR:
            return Path(self.DOCUMENT_UPLOAD_DIR).expanduser().resolve()
        return self.data_dir_path / "uploads" / "documents"

    @property
    def builtin_knowledge_dir_path(self) -> Path:
        if self.BUILTIN_KNOWLEDGE_DIR:
            return Path(self.BUILTIN_KNOWLEDGE_DIR).expanduser().resolve()
        return Path(__file__).resolve().parent.parent.parent / "knowledge"

    # ====== 知识检索向量（按队友 .env.example 补全配置）======
    EMBEDDING_BACKEND: str = "local_hash"          # local_hash / api
    LOCAL_EMBEDDING_DIMENSION: int = 384
    EMBEDDING_MODEL: str = "local-char-ngram-v1"
    EMBEDDING_API_URL: str = ""
    EMBEDDING_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: Any = '["http://localhost:8000","http://localhost:3000","http://localhost:5173","http://localhost:5174","http://localhost:5175","http://localhost:5176","http://localhost:5177"]'

    # LLM 通用
    LLM_BACKEND: str = "qwen"  # longcat / ollama / qwen
    LLM_TEMPERATURE: float = 0.3
    LLM_TIMEOUT: int = 180

    # LongCat 云端
    LONGCAT_API_KEY: str = ""
    LONGCAT_API_URL: str = "https://api.longcat.chat/openai"
    LONGCAT_MODEL: str = "longcat-2.0"

    # ====== 阿里云百炼（队友新增，原样复制）======
    QWEN_API_KEY: str = ""
    QWEN_API_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL: str = ""
    QWEN_TEXT_MODEL: str = ""
    QWEN_VISION_MODEL: str = "qwen3-vl-plus"
    SAFETY_MODEL: str = "qwen-plus"
    MAX_IMAGE_UPLOAD_MB: int = 10

    # Ollama 本地
    OLLAMA_API_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "qwen2.5:7b"

    # ---- 计算属性 ----
    @property
    def cors_origin_list(self) -> List[str]:
        return _parse_json_list(self.CORS_ORIGINS)

    @property
    def machine_arch(self) -> str:
        return os.uname().machine if hasattr(os, "uname") else "unknown"

    @property
    def is_loongarch(self) -> bool:
        return self.machine_arch.lower().startswith("loongarch")

    if field_validator:
        # 并集：LONGCAT + OLLAMA + QWEN_API_URL 一起校验 URL 末尾斜杠
        @field_validator("LONGCAT_API_URL", "OLLAMA_API_URL", "QWEN_API_URL")
        @classmethod
        def _norm_url(cls, v: str) -> str:
            v = (v or "").strip()
            return v.rstrip("/") if v else v

    model_config = {
        "env_file": _ENV_FILE or ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    } if BaseSettings is not object else {}


# 兼容没有 pydantic-settings 的最小降级（字段列表双方并集）
def _fallback_settings() -> Settings:
    from dotenv import load_dotenv
    if _ENV_FILE:
        load_dotenv(_ENV_FILE, override=False)
    s = Settings()
    for fld in [
        # ====== 你原有字段（含补漏 JWT_ALGORITHM / DB_FILENAME）======
        "ENVIRONMENT", "DEBUG", "API_HOST", "API_PORT",
        "SECRET_KEY", "JWT_ALGORITHM", "ACCESS_TOKEN_EXPIRE_HOURS",
        "DB_FILENAME", "CORS_ORIGINS",
        "LLM_BACKEND", "LLM_TEMPERATURE", "LLM_TIMEOUT",
        "LONGCAT_API_KEY", "LONGCAT_API_URL", "LONGCAT_MODEL",
        "OLLAMA_API_URL", "OLLAMA_MODEL",
        # ====== 队友新增：APP_DEBUG ======
        "APP_DEBUG",
        # ====== 队友新增：数据存储 6 个 ======
        "DATA_DIR", "DATABASE_PATH", "DOCUMENT_UPLOAD_DIR", "MAX_DOCUMENT_UPLOAD_MB",
        "AUTO_IMPORT_KNOWLEDGE", "BUILTIN_KNOWLEDGE_DIR",
        # ====== 队友新增：知识检索向量 5 个 ======
        "EMBEDDING_BACKEND", "LOCAL_EMBEDDING_DIMENSION", "EMBEDDING_MODEL",
        "EMBEDDING_API_URL", "EMBEDDING_API_KEY",
        # ====== 队友新增：百炼 QWEN 6 个 ======
        "QWEN_API_KEY", "QWEN_API_URL", "QWEN_MODEL", "QWEN_TEXT_MODEL", "QWEN_VISION_MODEL",
        "MAX_IMAGE_UPLOAD_MB", "SAFETY_MODEL",
    ]:
        env_v = os.getenv(fld)
        if env_v is None:
            continue
        try:
            import ast
            cur_type = type(getattr(s, fld, ""))
            if cur_type is bool:
                setattr(s, fld, env_v.lower() in ("1", "true", "yes", "on"))
            elif cur_type is int:
                setattr(s, fld, int(env_v))
            elif cur_type is float:
                setattr(s, fld, float(env_v))
            else:
                setattr(s, fld, env_v)
        except Exception:
            setattr(s, fld, env_v)
    return s


try:
    settings: Settings = Settings()
except Exception:
    settings = _fallback_settings()
