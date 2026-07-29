"""
FastAPI 主入口
- 启动：创建 SQLite 表 + 空库自动 seed 初始数据
- 统一响应：所有 /api/* 返回 { code, msg, data }，异常自动包装
- 双模式 LLM：SDK 优先 + requests 兜底（龙芯/openai SDK 缺失时不崩）
- 自动托管前端 dist（存在时），SPA 404 都走 index.html
"""

from __future__ import annotations

import os
import json
import time
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, List, Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status, Depends, HTTPException, Body
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import func as sqlalchemy_func, text
from sqlalchemy.orm import Session


def _utcnow():
    return datetime.now(timezone.utc)


APP_TIMEZONE = timezone(timedelta(hours=8))

# ===== 配置 =====
# 显式加载 .env（修复 pydantic-settings 读 UTF-8 BOM 编码 .env 失败导致 key_len=0 的问题）
_load_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _load_env_path.is_file():
    load_dotenv(str(_load_env_path), override=True)
del _load_env_path

from .config import settings as _settings
import typing

# pydantic-settings 解析 UTF-8 BOM 的 .env 失败 → 强制从 os.environ 回读
settings = _settings
for _fld in ("QWEN_API_KEY", "QWEN_TEXT_MODEL", "QWEN_VISION_MODEL",
             "LONGCAT_API_KEY", "LONGCAT_MODEL", "QWEN_API_URL", "LONGCAT_API_URL"):
    _env_val = os.getenv(_fld)
    if _env_val and not getattr(settings, _fld, None):
        try:
            setattr(settings, _fld, _env_val)
        except Exception:
            pass
del _settings, _fld, _env_val
from .database import Base, engine, get_db, init_database
from .models import User, Device, Ticket, KnowledgeReport, Case, Guide, Notification, AIFeedback, \
    TicketAttachment, DeviceFaultAttachment, ReportAttachment, GuideExecution, \
    FEEDBACK_STATUS_PENDING, FEEDBACK_STATUS_REVIEWED, FEEDBACK_STATUS_INCORPORATED, \
    NOTIFY_TYPE_REPORT_SUBMITTED, NOTIFY_TYPE_REPORT_APPROVED, NOTIFY_TYPE_REPORT_REJECTED, \
    NOTIFY_TYPE_REPORT_SYNCED, NOTIFY_TYPE_TICKET_ASSIGNED, NOTIFY_TYPE_TICKET_CREATED, \
    NOTIFY_TYPE_DEVICE_FAULT, NOTIFY_TYPE_SYSTEM, \
    DEVICE_STATUS_NORMAL, DEVICE_STATUS_REPAIRING, DEVICE_STATUS_DOWN, \
    EXEC_STATUS_IN_PROGRESS, EXEC_STATUS_COMPLETED, EXEC_STATUS_ABANDONED, \
    TICKET_PENDING, TICKET_ASSIGNED, TICKET_DOING, TICKET_OVER
# ===== 模型接入：RAG 路由 + 内置知识导入 =====
from .services.knowledge_bootstrap import bootstrap_builtin_knowledge
from .services.knowledge_graph import save_case, build_graph_from_db
from .services.retrieval_service import embed_texts
from .routers.documents import router as documents_router
from .routers.search import router as search_router
from .routers.rag import router as rag_router
from .routers.images import router as images_router

# ===== 鉴权 + DTO =====
from .auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_current_user_optional,
    role_label_of, is_admin_role, require_admin,
)
from .schemas import (
    LoginReq, UserInfo, LoginResp, ApiResp, ok, fail,
    PageReq, PageResp, page_wrap,
    DeviceCreate, DeviceUpdate, DeviceInfo,
    TicketCreate, TicketAssign, TicketComplete, TicketInfo,
    ReportCreate, ReportReview, ReportInfo,
    CaseInfo, GuideInfo, GuideStep,
    GuideExecutionCreate, GuideExecutionUpdate, GuideExecutionInfo,
    UserCreate, UserUpdate, UserPwdChange, UserFullInfo,
    UserProfileUpdate, NotificationInfo, NotificationMarkReadReq,
    AIFeedbackSubmit, AIFeedbackInfo, AIFeedbackReview,
)
from .users import ROLE_LABELS, ROLE_MANAGER, ROLE_WORKER, ROLE_SYSADMIN, verify_user as verify_user_fallback
from .seed import seed_if_empty

# ===== LLM 可选 SDK 导入 =====
_HAS_OPENAI_SDK = False
try:
    from openai import OpenAI  # type: ignore
    _HAS_OPENAI_SDK = True
except Exception:
    OpenAI = None  # type: ignore
    _HAS_OPENAI_SDK = False


# ============================================================
# FastAPI app 初始化
# ============================================================
app = FastAPI(
    title="EQUIPAI · 设备检修智能系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ===== 统一异常处理（包装成 {code,msg,data}） =====
@app.exception_handler(RequestValidationError)
async def _validation_handler(request: Request, exc: RequestValidationError):
    msg = "请求参数错误：" + "; ".join(
        [f"{'/'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in exc.errors()]
    )
    return JSONResponse(status_code=200, content=fail(msg, 400).model_dump())


@app.exception_handler(HTTPException)
async def _http_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return JSONResponse(status_code=200,
                            content=fail(exc.detail or "未登录或登录已过期", 401).model_dump())
    if exc.status_code == 403:
        return JSONResponse(status_code=200,
                            content=fail(exc.detail or "无权限", 403).model_dump())
    if 200 <= exc.status_code < 300:
        return JSONResponse(status_code=exc.status_code,
                            content=ok(exc.detail).model_dump())
    return JSONResponse(status_code=200,
                        content=fail(exc.detail or "服务异常", exc.status_code).model_dump())


@app.exception_handler(Exception)
async def _general_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        msg = f"服务器异常：{exc}\n{traceback.format_exc()}"
    else:
        msg = "服务器内部错误，请联系维修管理员"
    return JSONResponse(status_code=200,
                        content=fail(msg, 500).model_dump())


# ===== CORS（开发阶段 Vite 代理 + 5173~5179 系列直接访问） =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 模型接入：注册 4 个 RAG 路由（文档 / 检索 / RAG问答 / 多模态图片） =====
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(rag_router)
app.include_router(images_router)


# ============================================================
# LLM 上下文（双模式：SDK 或 requests）
# ============================================================
LLM_BACKEND = settings.LLM_BACKEND


def _resolve_qwen_key():
    """优先从 os.environ 读取，绕开 pydantic-settings 解析 UTF-8 BOM .env 失败的问题。"""
    return os.getenv("QWEN_API_KEY") or settings.QWEN_API_KEY or ""


def _build_llm_ctx():
    if LLM_BACKEND == "ollama":
        base_url = settings.OLLAMA_API_URL or "http://localhost:11434/v1"
        api_key = "ollama"
        model = settings.OLLAMA_MODEL or "qwen2.5:7b"
    elif _resolve_qwen_key() or LLM_BACKEND == "qwen":
        api_key = _resolve_qwen_key()
        model = settings.QWEN_TEXT_MODEL or settings.QWEN_MODEL or "qwen-plus"
        # 百炼域名区分国内 / 海外，通过域名自动补齐兼容前缀
        raw = (settings.QWEN_API_URL or "https://dashscope.aliyuncs.com/compatible-mode/v1").rstrip("/")
        if "dashscope.aliyuncs.com" in raw and "/compatible-mode" not in raw:
            base_url = raw + "/compatible-mode/v1"
        else:
            base_url = raw
    else:
        base_url = settings.LONGCAT_API_URL or "https://api.longcat.chat/openai"
        if not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"
        api_key = os.getenv("LONGCAT_API_KEY") or settings.LONGCAT_API_KEY or ""
        model = settings.LONGCAT_MODEL or "longcat-2.0"
    temperature = settings.LLM_TEMPERATURE or 0.3
    return base_url, api_key, model, temperature


_LLM_BASE, _LLM_KEY, LLM_MODEL, LLM_TEMPERATURE = _build_llm_ctx()

client = None
if _HAS_OPENAI_SDK and OpenAI is not None:
    try:
        client = OpenAI(base_url=_LLM_BASE, api_key=_LLM_KEY)
    except Exception:
        client = None


# ============================================================
# 生命周期：启动建表 + 空库自动 seed + RAG 知识库初始化
# ============================================================
@app.on_event("startup")
def _on_startup():
    # 1. 创建所有表（幂等，已有表不会覆盖）
    Base.metadata.create_all(bind=engine)
    # 2. 补齐旧表迁移列（profile + guide 新字段）
    _ensure_profile_columns(engine)
    _ensure_guide_columns(engine)
    ticket_category_added = _ensure_ticket_category_column(engine)
    _ensure_device_commission_column(engine)
    _ensure_case_submitter_columns(engine)
    _ensure_report_fault_column(engine)
    # 3. 只有 users 为空才 seed，避免重复插入
    from .database import SessionLocal
    db = SessionLocal()
    try:
        seed_if_empty(db)
        _reseed_guides(db)
        _backfill_notification_history_if_empty(db)
        # 兼容上一版本：已指定维修工但仍为 pending 的工单迁入”待处理”。
        assigned_status_migrated = db.query(Ticket).filter(
            Ticket.status == TICKET_PENDING,
            Ticket.assignee_id.isnot(None),
        ).update({Ticket.status: TICKET_ASSIGNED}, synchronize_session=False)
        categorized_tickets = 0
        if ticket_category_added:
            category_map = {
                "机械动力": "机械",
                "电气控制": "电气",
                "安全保护": "安全",
                "工业仪表": "仪表",
                "液压执行": "液压",
            }
            devices_by_id = {d.id: d for d in db.query(Device).all()}
            for ticket in db.query(Ticket).all():
                device = devices_by_id.get(ticket.device_id)
                ticket.category = category_map.get(
                    device.tag if device else None, "机械"
                )
                categorized_tickets += 1
        # 旧版演示数据把北京时间小时误当成 UTC 保存，可能产生未来工单。
        # 将未来的提交时间逐日回退，保留原有时分与相对排序。
        now_utc_naive = _utcnow().replace(tzinfo=None)
        future_tickets = db.query(Ticket).filter(
            Ticket.submit_time > now_utc_naive
        ).all()
        for ticket in future_tickets:
            while ticket.submit_time and ticket.submit_time > now_utc_naive:
                ticket.submit_time -= timedelta(days=1)
        # 旧版派维修只保存了“设备编号 设备名称”，补齐缺失的 device_id。
        linked_tickets = 0
        legacy_tickets = db.query(Ticket).filter(
            Ticket.device_id.is_(None),
            Ticket.device_name.isnot(None),
        ).all()
        for ticket in legacy_tickets:
            device_code = (ticket.device_name or "").strip().split(maxsplit=1)[0]
            if not device_code:
                continue
            device = db.query(Device).filter(Device.code == device_code).first()
            if device:
                ticket.device_id = device.id
                linked_tickets += 1
        # 已进入处理流程的工单，其关联设备应处于“维修中”。
        active_device_ids = [
            row[0] for row in db.query(Ticket.device_id).filter(
                Ticket.device_id.isnot(None),
                Ticket.status.in_([TICKET_DOING, TICKET_OVER]),
            ).distinct().all()
        ]
        repairing_devices = 0
        for device_id in active_device_ids:
            device = db.query(Device).filter(Device.id == device_id).first()
            if device and device.status == DEVICE_STATUS_DOWN:
                device.status = DEVICE_STATUS_REPAIRING
                repairing_devices += 1
        # 旧版初始化数据只标记了“故障停机”，没有故障报告内容。
        # 为这些演示设备补齐上报信息；真实故障上报已有的数据不会被覆盖。
        default_reporter = (
            db.query(User).filter(User.username == "worker3").first()
            or db.query(User).filter(User.username == "admin").first()
        )
        completed_fault_reports = 0
        missing_fault_devices = db.query(Device).filter(
            Device.status == DEVICE_STATUS_DOWN,
            Device.fault_desc.is_(None),
            Device.fault_time.is_(None),
            Device.fault_reporter_id.is_(None),
        ).all()
        for device in missing_fault_devices:
            prefix = (device.code or "").split("-", 1)[0].upper()
            if not device.fault_desc:
                if prefix == "P":
                    device.fault_desc = (
                        "巡检发现离心泵运行异响，出口压力持续波动且振动值超过报警阈值；"
                        "现场已执行停机隔离，等待维修人员进一步检查轴承、联轴器及汽蚀情况。"
                    )
                elif prefix == "VA":
                    device.fault_desc = (
                        "巡检发现比例阀组响应异常、阀芯中位漂移，执行机构动作不稳定；"
                        "复位后故障仍存在，现场已停机并等待检修。"
                    )
                else:
                    device.fault_desc = (
                        f"巡检发现{device.name}运行参数异常并触发故障停机，"
                        "现场已完成安全隔离，具体故障原因待维修人员进一步诊断。"
                    )
            if not device.fault_reporter_id and default_reporter:
                device.fault_reporter_id = default_reporter.id
            if not device.fault_time:
                device.fault_time = _utcnow() - timedelta(hours=(device.id % 8) + 1)
            completed_fault_reports += 1
        # 标签迁移：旧版设备标签 → 新版简称
        _tag_map = {"智能制造": "综合", "机械动力": "机械", "电气控制": "电气",
                     "液压执行": "液压", "工业仪表": "仪表", "安全保护": "安全"}
        tag_migrated = 0
        for _old_tag, _new_tag in _tag_map.items():
            _changed = db.query(Device).filter(Device.tag == _old_tag).update(
                {Device.tag: _new_tag}, synchronize_session=False
            )
            if _changed:
                tag_migrated += _changed
        if (
            assigned_status_migrated or future_tickets or linked_tickets or repairing_devices
            or completed_fault_reports or categorized_tickets or tag_migrated
        ):
            db.commit()

    finally:
        db.close()
    # 4. 模型接入：RAG 知识库表初始化 + 内置知识文档自动导入（幂等）
    init_database()
    app.state.knowledge_bootstrap = bootstrap_builtin_knowledge()


_PROFILE_COLS = {
    'emp_no': 'TEXT', 'dept': 'TEXT', 'position': 'TEXT',
    'join_date': 'TEXT', 'mobile': 'TEXT', 'email': 'TEXT',
    'tel': 'TEXT', 'office': 'TEXT',
}


_GUIDE_COLS = {
    'scope': 'TEXT',
    'preparation_json': 'TEXT',
    'safety_control_json': 'TEXT',
    'acceptance_criteria_json': 'TEXT',
    'stop_conditions_json': 'TEXT',
}

def _ensure_guide_columns(engine) -> None:
    """为已有的 guides 表补齐新字段。"""
    try:
        with engine.connect() as conn:
            existing = {r[1] for r in conn.execute(
                text("PRAGMA table_info(guides)")
            ).fetchall()}
    except Exception:
        return
    for col, typ in _GUIDE_COLS.items():
        if col in existing:
            continue
        try:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE guides ADD COLUMN {col} {typ}"))
                conn.commit()
        except Exception:
            pass


def _ensure_device_commission_column(engine) -> None:
    """为已有 devices 表补齐 commission_date 列。"""
    try:
        with engine.connect() as conn:
            existing = {r[1] for r in conn.execute(
                text("PRAGMA table_info(devices)")
            ).fetchall()}
    except Exception:
        return
    if "commission_date" not in existing:
        try:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE devices ADD COLUMN commission_date TEXT"))
                conn.commit()
        except Exception:
            pass


def _ensure_case_submitter_columns(engine) -> None:
    """为已有 cases 表补齐 submitter_id / submitter_role 列。"""
    try:
        with engine.connect() as conn:
            existing = {r[1] for r in conn.execute(
                text("PRAGMA table_info(cases)")
            ).fetchall()}
    except Exception:
        return
    for col, typ in {"submitter_id": "INTEGER", "submitter_role": "TEXT"}.items():
        if col not in existing:
            try:
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE cases ADD COLUMN {col} {typ}"))
                    conn.commit()
            except Exception:
                pass


def _ensure_report_fault_column(engine) -> None:
    """为已有 knowledge_reports 表补齐 fault 列。"""
    try:
        with engine.connect() as conn:
            existing = {r[1] for r in conn.execute(
                text("PRAGMA table_info(knowledge_reports)")
            ).fetchall()}
    except Exception:
        return
    if "fault" not in existing:
        try:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE knowledge_reports ADD COLUMN fault TEXT"))
                conn.commit()
        except Exception:
            pass


def _ensure_profile_columns(engine) -> None:
    """为已有的 SQLite users 表补齐 profile 列（demo 用，不引入迁移框架）"""
    try:
        with engine.connect() as conn:
            existing = {r[1] for r in conn.execute(
                text("PRAGMA table_info(users)")
            ).fetchall()}
    except Exception:
        return
    for col, typ in _PROFILE_COLS.items():
        if col in existing:
            continue
        try:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {typ}"))
                conn.commit()
        except Exception:
            pass


def _ensure_ticket_category_column(engine) -> bool:
    """为旧版 SQLite 工单表增加类别字段，返回本次是否新增。"""
    try:
        with engine.connect() as conn:
            existing = {r[1] for r in conn.execute(
                text("PRAGMA table_info(tickets)")
            ).fetchall()}
        if "category" in existing:
            return False
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE tickets ADD COLUMN category TEXT NOT NULL DEFAULT '机械'"
            ))
            conn.commit()
        return True
    except Exception:
        return False


# ============================================================
# 健康检查
# ============================================================
@app.get("/health")
def health():
    return {"status": "ok", "time": int(time.time()),
            "llm_backend": LLM_BACKEND, "llm_model": LLM_MODEL}


@app.get("/health/ready")
def readiness():
    checks: dict[str, Any] = {"api": True, "db": False, "llm": False}
    # DB
    try:
        db = next(get_db())
        checks["db"] = db.execute("SELECT 1").scalar() == 1
    except Exception:
        checks["db"] = False
    # LLM（兼容 LongCat / Ollama / QWEN 三个后端）
    try:
        if LLM_BACKEND == "ollama":
            base = (settings.OLLAMA_API_URL or "http://localhost:11434/v1").rstrip("/").replace("/v1", "")
            resp = requests.get(f"{base}/api/tags", timeout=5)
            checks["llm"] = resp.status_code == 200
        else:
            checks["llm"] = bool(os.getenv("QWEN_API_KEY") or os.getenv("LONGCAT_API_KEY") or settings.QWEN_API_KEY or settings.LONGCAT_API_KEY)
    except Exception:
        checks["llm"] = False
    all_ready = all(v for k, v in checks.items() if k != "time")
    return {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
        "knowledge_bootstrap": getattr(app.state, "knowledge_bootstrap", None),
    }


# ============================================================
# LLM 辅助
# ============================================================
def _llm_chat_request(prompt: str, user_text: str):
    messages = [
        {"role": "system", "content": "你是工业设备检修专家，请严格按结构回答问题"},
        {"role": "user", "content": prompt},
    ]
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": LLM_TEMPERATURE,
    }
    if client is not None:
        try:
            resp = client.chat.completions.create(**payload)  # type: ignore[union-attr]
            return resp.choices[0].message.content, "openai-sdk"
        except Exception:
            pass
    base = _LLM_BASE.rstrip("/")
    url = f"{base}/chat/completions"
    headers = {"Authorization": f"Bearer {_LLM_KEY}", "Content-Type": "application/json"}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=settings.LLM_TIMEOUT or 180)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"], "requests-fallback"
    except Exception as e:
        return None, f"error: {e}"


# ============================================================
# DTO：AI 请求
# ============================================================
class AIRequest(BaseModel):
    text: str


# ============================================================
# 用户工具函数：User → UserInfo DTO
# ============================================================
def _to_userinfo(u: User) -> UserInfo:
    # join_date 是 YYYY-MM-DD 字符串，转 ts 方便前端图表
    join_ts = None
    if u.join_date:
        try:
            join_ts = int(datetime.strptime(u.join_date, "%Y-%m-%d").replace(
                tzinfo=timezone.utc).timestamp())
        except Exception:
            join_ts = None
    return UserInfo(
        id=u.id,
        username=u.username,
        fullname=u.fullname,
        role=u.role,
        role_label=role_label_of(u.role),
        avatar_preset=u.avatar_preset,
        avatar=None,
        created_at=u.created_at,
        emp_no=u.emp_no,
        dept=u.dept,
        position=u.position,
        join_date=u.join_date,
        join_date_ts=join_ts,
        mobile=u.mobile,
        email=u.email,
        tel=u.tel,
        office=u.office,
    )


# ============================================================
# 消息通知工具函数
# ============================================================
def _push_notify(db: Session, user_ids: list[int], type: str,
                 title: str, content: str = "", related_id: int | None = None) -> None:
    """批量插入消息通知（失败不影响主流程，try-catch 吞掉）"""
    if not user_ids:
        return
    try:
        now = _utcnow()
        for uid in set(user_ids):
            if not uid:
                continue
            db.add(Notification(
                user_id=uid, type=type,
                title=title[:255], content=(content or "")[:4000],
                related_id=related_id, is_read=0, created_at=now,
            ))
        db.commit()
    except Exception:
        db.rollback()


def _admin_ids(db: Session) -> list[int]:
    rows = db.query(User.id).filter(
        User.role.in_([ROLE_SYSADMIN, ROLE_MANAGER])
    ).all()
    return [r[0] for r in rows]


def _map_device_status(s: str) -> str:
    """中文状态 → 代码"""
    s = (s or '').strip()
    if s in ('down', 'repairing', 'normal'):
        return s
    if '停机' in s or '故障' in s or '损坏' in s:
        return 'down'
    if '维修' in s or '检修' in s:
        return 'repairing'
    if '正常' in s or '运行' in s:
        return 'normal'
    return 'down'


def _ts(dt) -> int | None:
    if dt is None:
        return None
    try:
        if dt.tzinfo is None:
            import calendar
            return int(calendar.timegm(dt.timetuple()))
        return int(dt.timestamp())
    except Exception:
        return None


def _to_notification_info(n: Notification) -> NotificationInfo:
    return NotificationInfo(
        id=n.id, type=n.type, title=n.title, content=n.content,
        related_id=n.related_id, is_read=bool(n.is_read),
        created_at_ts=_ts(n.created_at),
    )


# ============================================================
# ============ ============ 业务 API ============ ============
# ============================================================

# ---------- 登录 ----------
@app.post("/api/login", response_model=ApiResp[LoginResp])
def login(form: LoginReq, db: Session = Depends(get_db)):
    username = (form.username or "").strip()
    password = form.password or ""
    role = (form.role or "").strip()
    if not username or not password:
        return fail("请输入账号和密码", 400)

    def role_matches(actual_role: str) -> bool:
        # 前端将 sysadmin 和 manager 统一展示为“维修管理员”。
        if not role:
            return True
        if role == ROLE_MANAGER:
            return actual_role in (ROLE_MANAGER, ROLE_SYSADMIN)
        return role == actual_role

    # 1) 查数据库用户（阶段 A 后所有账号都在这里）
    user = db.query(User).filter(User.username == username).first()
    if user:
        if verify_password(password, user.password_hash):
            if not role_matches(user.role):
                return fail("所选登录身份与该账号角色不一致", 403)
            token, hours = create_access_token(user.username, user.role)
            return ok(LoginResp(
                token=token, token_type="bearer",
                expires_hours=hours, user=_to_userinfo(user),
            ))
        # 数据库里已有该用户但密码错误 → 直接返回失败，禁止用 fallback/比赛后门绕过
        return fail("账号或密码错误", 401)

    # 2) 兜底：如果数据库还没装成功（极端情况），走 users.py 的 fake_users 保证能登录
    u_fb = verify_user_fallback(username, password)
    if u_fb:
        if not role_matches(u_fb["role"]):
            return fail("所选登录身份与该账号角色不一致", 403)
        token, hours = create_access_token(u_fb["username"], u_fb["role"])
        return ok(LoginResp(
            token=token, token_type="bearer",
            expires_hours=hours,
            user=UserInfo(
                id=0, username=u_fb["username"], fullname=u_fb["fullname"],
                role=u_fb["role"], role_label=u_fb.get("role_label") or role_label_of(u_fb["role"]),
            ),
        ))

    # 3) 比赛用后门：当密码是 123456 但数据库没该用户时，自动创建一个对应角色的用户
    #    role 未传时根据账号后缀 / 默认角色推断：含"主任/管/admin/manager"走管理员，其余走维修工
    if password == "123456":
        if role not in (ROLE_MANAGER, ROLE_SYSADMIN, ROLE_WORKER):
            u_lower = username.lower()
            if any(k in u_lower for k in ("admin", "manager", "guanli", "zhuren", "mgr")) or \
               any(k in username for k in ("主任", "管", "管理员")):
                role = ROLE_MANAGER
            else:
                role = ROLE_WORKER
        suffix = "主任" if role in (ROLE_MANAGER, ROLE_SYSADMIN) else "师傅"
        fullname = username if any(username.endswith(s) for s in ("主任", "师傅", "工", "员", "经理")) else (username + suffix)
        _newly_created = False
        try:
            new_user = User(
                username=username, password_hash=hash_password("123456"),
                fullname=fullname, role=role,
                created_at=_utcnow(),
            )
            db.add(new_user); db.commit(); db.refresh(new_user)
            _newly_created = True
        except Exception:
            db.rollback()
            new_user = db.query(User).filter(User.username == username).first()
            if not new_user:
                return fail("账号或密码错误", 401)
        token, hours = create_access_token(new_user.username, new_user.role)
        return ok(LoginResp(token=token, token_type="bearer", expires_hours=hours, user=_to_userinfo(new_user)))

    return fail("账号或密码错误", 401)


# ---------- 当前用户信息 ----------
@app.get("/api/me", response_model=ApiResp[UserInfo])
def api_me(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 刷新一次以防数据库改了角色
    db.refresh(current)
    return ok(_to_userinfo(current))


# ---------- 当前用户修改自己的 profile ----------
@app.put("/api/me", response_model=ApiResp[UserInfo])
def update_me(form: UserProfileUpdate,
              current: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    """当前登录用户修改自己的 profile（不含账号 / 密码 / 角色）"""
    db.refresh(current)
    if form.fullname is not None:
        v = form.fullname.strip()
        current.fullname = v if v else current.fullname or current.username
    if form.emp_no is not None:
        current.emp_no = form.emp_no.strip() or None
    if form.dept is not None:
        current.dept = form.dept.strip() or None
    if form.position is not None:
        current.position = form.position.strip() or None
    if form.join_date is not None:
        current.join_date = form.join_date or None
    if form.mobile is not None:
        current.mobile = form.mobile.strip() or None
    if form.email is not None:
        v = form.email.strip().lower()
        current.email = v if v else None
    if form.tel is not None:
        current.tel = form.tel.strip() or None
    if form.office is not None:
        current.office = form.office.strip() or None
    db.commit(); db.refresh(current)
    return ok(_to_userinfo(current), "个人信息已更新")


# ---------- Dashboard 基础接口（阶段 B 扩展：真实统计）----------
@app.get("/api/dashboard/overview", response_model=ApiResp)
def dashboard_overview(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 阶段 A 先返回空结构占位，阶段 B 再按真表 count，保证前端不会 404
    from .models import (
        DEVICE_STATUS_NORMAL, DEVICE_STATUS_REPAIRING, DEVICE_STATUS_DOWN,
        TICKET_PENDING, TICKET_ASSIGNED, TICKET_DOING, TICKET_DONE, TICKET_OVER,
    )
    def cnt(model, *conds):
        q = db.query(model)
        for c in conds:
            q = q.filter(c)
        return q.count()

    data = {
        "devices": {
            "total": cnt(Device),
            "ok": cnt(Device, Device.status == DEVICE_STATUS_NORMAL),
            "repair": cnt(Device, Device.status == DEVICE_STATUS_REPAIRING),
            "down": cnt(Device, Device.status == DEVICE_STATUS_DOWN),
        },
        "tickets": {
            "pending": cnt(Ticket, Ticket.status == TICKET_PENDING),
            "assigned": cnt(Ticket, Ticket.status == TICKET_ASSIGNED),
            "doing": cnt(Ticket, Ticket.status == TICKET_DOING),
            "done": cnt(Ticket, Ticket.status == TICKET_DONE),
            "over": cnt(Ticket, Ticket.status == TICKET_OVER),
        },
        "reports": {
            "total": cnt(KnowledgeReport),
            "pending": cnt(KnowledgeReport, KnowledgeReport.status == "pending"),
            "approved": cnt(
                KnowledgeReport,
                KnowledgeReport.status.in_(["approved", "synced_case", "synced_guide"]),
            ),
            "rejected": cnt(KnowledgeReport, KnowledgeReport.status == "rejected"),
            "synced": cnt(
                KnowledgeReport,
                KnowledgeReport.status.in_(["synced_case", "synced_guide"]),
            ),
        },
        "ai_feedback": {
            "total": cnt(AIFeedback),
            "pending": cnt(AIFeedback, AIFeedback.status == FEEDBACK_STATUS_PENDING),
            "reviewed": cnt(AIFeedback, AIFeedback.status == FEEDBACK_STATUS_REVIEWED),
            "incorporated": cnt(AIFeedback, AIFeedback.status == FEEDBACK_STATUS_INCORPORATED),
        },
        "timestamp": int(time.time()),
    }
    # 饼图 = 设备状态分布（ok / repair / down），颜色统一工业色板
    data["pie"] = [
        {"name": "正常运行", "value": data["devices"]["ok"],     "color": "#2563eb"},
        {"name": "维修中",   "value": data["devices"]["repair"],  "color": "#06b6d4"},
        {"name": "故障停机", "value": data["devices"]["down"],    "color": "#ef4444"},
    ]
    # 折线图：近 30 天新增工单数
    now_local = datetime.now(APP_TIMEZONE)
    trend = []
    for i in range(29, -1, -1):
        day_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        t_label = f"{day_start.month}/{day_start.day}"
        day_tickets = db.query(Ticket).filter(
            Ticket.submit_time >= day_start.astimezone(timezone.utc),
            Ticket.submit_time < day_end.astimezone(timezone.utc),
        ).count()
        trend.append({"label": t_label, "v": day_tickets})
    data["trend"] = trend

    # 当前近 7 天之前紧邻的 7 天，用于 7 天视图的“前 7 天”对比。
    # 当前序列最后 7 项是今天至前 6 天；对比序列为前 7 天至前 13 天。
    trend_prev = []
    for i in range(13, 6, -1):
        day_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        t_label = f"{day_start.month}/{day_start.day}"
        day_tickets = db.query(Ticket).filter(
            Ticket.submit_time >= day_start.astimezone(timezone.utc),
            Ticket.submit_time < day_end.astimezone(timezone.utc),
        ).count()
        trend_prev.append({"label": t_label, "v": day_tickets})
    data["trend_prev"] = trend_prev

    # 最近事件（home 首页时间线替代）—— 工单+报告混合，≤10 条
    events: list[dict] = []
    for t in db.query(Ticket).order_by(Ticket.submit_time.desc()).limit(8).all():
        when = int(t.submit_time.timestamp()) if t.submit_time else int(time.time())
        status_label = {"pending": "待派单", "assigned": "待处理", "doing": "处理中", "done": "已完成", "over": "超时"}.get(t.status, t.status)
        events.append({"time": when, "title": t.title, "type": "ticket",
                       "status": t.status, "status_label": status_label,
                       "device": t.device_name, "user": "系统"})
    for r in db.query(KnowledgeReport).order_by(KnowledgeReport.submit_time.desc()).limit(4).all():
        when = int(r.submit_time.timestamp()) if r.submit_time else int(time.time())
        events.append({"time": when, "title": r.title, "type": "report",
                       "status": r.status, "status_label": r.status,
                       "device": r.device, "user": r.submitter_name})
    events.sort(key=lambda x: x["time"], reverse=True)
    data["recent_events"] = events[:10]
    return ok(data)


# ---------- 知识贡献排行榜（激励机制）----------
@app.get("/api/leaderboard/contributions", response_model=ApiResp)
def contribution_leaderboard(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """返回知识贡献排行榜：统计每位员工已通过审核的知识报告和案例贡献。"""
    # 统计已审核通过的知识报告
    approved_reports = (
        db.query(
            KnowledgeReport.submitter_id,
            KnowledgeReport.submitter_name,
            sqlalchemy_func.count(KnowledgeReport.id).label("report_count"),
        )
        .filter(
            KnowledgeReport.status.in_(["approved", "synced_case", "synced_guide"]),
        )
        .group_by(KnowledgeReport.submitter_id, KnowledgeReport.submitter_name)
        .all()
    )

    # 统计案例库中的贡献者
    case_contributions = (
        db.query(
            Case.submitter_id,
            Case.contributor_name,
            sqlalchemy_func.count(Case.id).label("case_count"),
            Case.submitter_role,
        )
        .filter(Case.submitter_id.isnot(None))
        .group_by(Case.submitter_id, Case.contributor_name, Case.submitter_role)
        .all()
    )

    # 合并数据
    contributor_map: dict[int, dict] = {}
    for rid, rname, rcnt in approved_reports:
        uid = rid or 0
        if uid not in contributor_map:
            contributor_map[uid] = {
                "user_id": uid,
                "name": rname or "未知",
                "reports_approved": 0,
                "cases_contributed": 0,
                "total_score": 0,
            }
        contributor_map[uid]["reports_approved"] = rcnt

    for sid, cname, ccnt, srole in case_contributions:
        uid = sid or 0
        if uid not in contributor_map:
            contributor_map[uid] = {
                "user_id": uid,
                "name": cname or "未知",
                "reports_approved": 0,
                "cases_contributed": 0,
                "total_score": 0,
            }
        contributor_map[uid]["cases_contributed"] = ccnt

    # 总积分 = 审核通过报告数 * 10 + 入库案例数 * 20
    for uid, info in contributor_map.items():
        info["total_score"] = info["reports_approved"] * 10 + info["cases_contributed"] * 20

    # 排序
    ranking = sorted(contributor_map.values(), key=lambda x: (-x["total_score"], -x["reports_approved"]))
    for idx, entry in enumerate(ranking, 1):
        entry["rank"] = idx
        entry["is_me"] = entry["user_id"] == current.id
        # 等级称号
        score = entry["total_score"]
        if score >= 100:
            entry["title"] = "🏆 金牌贡献者"
        elif score >= 50:
            entry["title"] = "🥈 银牌贡献者"
        elif score >= 20:
            entry["title"] = "🥉 铜牌贡献者"
        elif score > 0:
            entry["title"] = "⭐ 初级贡献者"
        else:
            entry["title"] = "🌱 待贡献"

    return ok({
        "ranking": ranking,
        "my_rank": next((e for e in ranking if e["is_me"]), None),
        "total_contributors": len(ranking),
    })


# ---------- AI 检索（双模式：有 LLM 用 LLM；无 LLM 返回本地知识库 top5）----------
@app.post("/api/ai/ask", response_model=ApiResp)
def ai_ask(req: AIRequest,
           current: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    q = (req.text or "").strip()
    if not q:
        return fail("请输入问题描述", 400)

    # 1) 先查本地知识库（永远执行，即使有 LLM 也塞 RAG 上下文）
    keywords = [k for k in q.split() if len(k) >= 2]
    local_refs: list[dict] = []

    def _search_model(model, fields, limit=5):
        q_db = db.query(model)
        if keywords:
            from sqlalchemy import or_
            conds = []
            for kw in keywords:
                for fld in fields:
                    conds.append(fld.ilike(f"%{kw}%"))
            q_db = q_db.filter(or_(*conds))
        return q_db.order_by(model.created_at.desc()
                             if hasattr(model, "created_at") else model.id.desc()).limit(limit).all()

    case_fields = [Case.title, Case.device, Case.fault, Case.solution, Case.summary]
    guide_fields = [Guide.title, Guide.device_type, Guide.tag, Guide.risk_note]
    report_fields = [KnowledgeReport.title, KnowledgeReport.device,
                     KnowledgeReport.question, KnowledgeReport.solution]
    cases_top = _search_model(Case, case_fields, 5)
    guides_top = _search_model(Guide, guide_fields, 3)
    reports_top = _search_model(KnowledgeReport, report_fields, 3)

    refs_section_parts = []
    for i, c in enumerate(cases_top, 1):
        local_refs.append({"kind": "case", "id": c.id, "title": c.title,
                           "device": c.device, "solution": c.solution})
        refs_section_parts.append(
            f"【本地案例 {i}】设备：{c.device or '通用'}\n问题：{c.fault}\n方案：{c.solution}"
        )
    for i, g in enumerate(guides_top, 1):
        steps_text = g.steps_json or "[]"
        try:
            steps = json.loads(steps_text)
            steps_text = "\n".join(f"- S{s['step']}: {s['content']}" for s in steps[:5])
        except Exception:
            pass
        local_refs.append({"kind": "guide", "id": g.id, "title": g.title,
                           "device_type": g.device_type, "risk": g.risk_note})
        refs_section_parts.append(
            f"【本地作业指导 {i}】{g.title}（{g.device_type}）\n步骤：\n{steps_text}"
        )
    for i, r in enumerate(reports_top, 1):
        local_refs.append({"kind": "report", "id": r.id, "title": r.title,
                           "submitter": r.submitter_name, "solution": r.solution})
        refs_section_parts.append(
            f"【员工实践方案 {i}】{r.submitter_name} 提交：{r.title}\n方案：{r.solution}"
        )

    # 2) 有可用 LLM（或兜底 requests），调用后把本地 refs 塞入上下文 + 附在结果里
    prompt_parts = []
    if refs_section_parts:
        prompt_parts.append("【参考资料：内部知识库 + 员工实践（如果与用户问题相关，请优先采纳并注明来源）】\n" +
                            "\n\n".join(refs_section_parts) + "\n")
    prompt_parts.append(f"你是工业设备检修AI，请按结构回答：\n【故障现象】\n【原因分析】\n【处理步骤】\n【风险提示】\n\n用户问题：\n{q}")
    prompt = "\n".join(prompt_parts)

    result, via = _llm_chat_request(prompt, q)
    has_llm = result is not None

    if has_llm:
        answer = result
    else:
        # 离线兜底：无 LLM 时直接返回本地 refs 格式化答案
        lines = ["【故障现象】", q, "", "【原因分析】"]
        if refs_section_parts:
            lines.append("参考内部知识库条目如下（未调用 LLM，仅供现场参考）：")
            lines.extend(refs_section_parts)
        else:
            lines.append("（暂无匹配的内部知识库条目，请联系维修管理员处理，并建议在 AI 回答后提交您的实践方案）")
        lines.extend(["", "【处理步骤】", "1. 停机断电挂安全锁，挂牌；",
                      "2. 按设备 SOP 排查上述可能原因；",
                      "3. 如需 AI 深度分析，请确保服务器联网并在 .env 中配置 LLM_BACKEND 对应的 API Key；",
                      "4. 排查完成后填写工单并考虑将方案贡献入知识库。",
                      "", "【风险提示】",
                      "• 本回答来自本地知识库，未经过 LLM 优化；",
                      "• 高压/旋转/高温设备务必执行断电上锁挂牌流程；",
                      "• 拿不准请立即联系维修管理员。"])
        answer = "\n".join(lines)
        via = "offline-local-knowledge"

    return ok({
        "answer": answer,
        "refs": local_refs,
        "llm_via": via,
        "offline": not has_llm,
    })


# ---------- 基础 hello（保留） ----------
@app.get("/api/hello")
def hello():
    llm_via = "openai-sdk" if (client is not None) else "requests-fallback"
    return ok({
        "msg": "设备检修智能系统 FastAPI 后端服务运行正常",
        "llm_backend": LLM_BACKEND,
        "llm_via": llm_via,
        "llm_model": LLM_MODEL,
        "has_openai_sdk": _HAS_OPENAI_SDK,
        "db_url": settings.database_url,
    }, "success")


# ============================================================
# ============ ============ 阶段 B：6 组业务 API ============ ============
# ============================================================

# ---------- 通用小工具 ----------
def _ts(dt) -> Optional[int]:
    """datetime → 秒级时间戳，None 安全；naive 按 UTC 处理"""
    if dt is None:
        return None
    try:
        if dt.tzinfo is None:
            import calendar
            return int(calendar.timegm(dt.timetuple()))
        return int(dt.timestamp())
    except Exception:
        return None


DEVICE_STATUS_LABELS = {
    "normal": "正常运行",
    "repairing": "维修中",
    "down": "故障停机",
}

TICKET_STATUS_LABELS = {
    "pending": "待派单",
    "assigned": "待处理",
    "doing": "进行中",
    "done": "已完成",
    "over": "超时",
    "cancelled": "已驳回",
}

TICKET_LEVEL_LABELS = {
    "low": "低",
    "mid": "中",
    "high": "高",
    "critical": "高",
}

REPORT_STATUS_LABELS = {
    "pending": "待审核",
    "approved": "审核通过（待入库）",
    "rejected": "已驳回",
    "synced_case": "已入库案例",
    "synced_guide": "已入库指南",
}

LEVEL_LABELS = {"low": "低", "mid": "中", "high": "高"}
SOURCE_LABELS = {
    "search": "AI 检索场景",
    "ticket": "工单场景",
    "manual": "手工提交",
}
TYPE_LABELS = {"case": "案例", "guide": "作业指导"}


def _load_fault_data(db: Session, devices: list[Device]):
    """批量预加载故障上报信息，返回 (reporters_map, attachments_map)"""
    reporters, attachments = {}, {}
    down = [d for d in devices if d.status == DEVICE_STATUS_DOWN]
    if not down:
        return reporters, attachments
    reporter_ids = {d.fault_reporter_id for d in down if d.fault_reporter_id}
    if reporter_ids:
        reps = db.query(User.id, User.fullname, User.username) \
                 .filter(User.id.in_(reporter_ids)).all()
        reporters = {r[0]: (r[1] or r[2]) for r in reps}
    atts = db.query(DeviceFaultAttachment).filter(
        DeviceFaultAttachment.device_id.in_([d.id for d in down])).all()
    for a in atts:
        attachments.setdefault(a.device_id, []).append(a)
    return reporters, attachments


def _to_device_info(d: Device, db: Session,
                    _fault_reporters: dict = None,
                    _fault_attachments: dict = None) -> DeviceInfo:
    health = 100
    if d.status == DEVICE_STATUS_REPAIRING:
        health = 50
    elif d.status == DEVICE_STATUS_DOWN:
        health = 0
    # 故障停机时附带故障上报信息（从预加载映射中取，避免 N+1 查询）
    fault_desc = None
    fault_reporter_name = None
    fault_time_ts = None
    fault_attachments = None
    if d.status == DEVICE_STATUS_DOWN:
        fault_desc = d.fault_desc
        if _fault_reporters is not None:
            fault_reporter_name = _fault_reporters.get(d.fault_reporter_id)
        fault_time_ts = _ts(d.fault_time)
        if _fault_attachments is not None:
            fas = _fault_attachments.get(d.id, [])
            fault_attachments = [
                {"id": a.id, "filename": a.filename, "size": a.file_size,
                 "mime_type": a.mime_type, "uploaded_at_ts": _ts(a.uploaded_at)}
                for a in fas]
    return DeviceInfo(
        id=d.id, code=d.code, name=d.name, tag=d.tag or "机械",
        location=d.location, status=d.status,
        status_label=DEVICE_STATUS_LABELS.get(d.status, d.status),
        health=health,
        commission_date=d.commission_date,
        last_repair_at=d.last_repair_at,
        fault_desc=fault_desc,
        fault_reporter_name=fault_reporter_name,
        fault_time_ts=fault_time_ts,
        fault_attachments=fault_attachments,
    )


def _to_ticket_info(t: Ticket, db: Session) -> TicketInfo:
    sub_name = None
    if t.submitter_id:
        u = db.query(User).filter(User.id == t.submitter_id).first()
        sub_name = u.fullname if u else None
    asg_name = None
    if t.assignee_id:
        u = db.query(User).filter(User.id == t.assignee_id).first()
        asg_name = u.fullname if u else None
    status_label = TICKET_STATUS_LABELS.get(t.status, t.status)
    remark = None
    if t.extra:
        try:
            extra_data = json.loads(t.extra)
            if isinstance(extra_data, dict):
                remark = extra_data.get("dispatch_remark")
        except (TypeError, ValueError):
            pass
    return TicketInfo(
        id=t.id, code=t.code, title=t.title,
        device_id=t.device_id, device_name=t.device_name,
        category=t.category or "机械",
        level=t.level, level_label=TICKET_LEVEL_LABELS.get(t.level, t.level),
        status=t.status, status_label=status_label,
        submitter_name=sub_name, assignee_name=asg_name, assignee_id=t.assignee_id,
        problem=t.problem, solution=t.solution, remark=remark,
        submit_time_ts=_ts(t.submit_time), finish_time_ts=_ts(t.finish_time),
    )


def _to_report_info(r: KnowledgeReport) -> ReportInfo:
    return ReportInfo(
        id=r.id, rid=r.rid, title=r.title, device=r.device,
        type=r.type, source=r.source, level=r.level, tag=r.tag,
        question=r.question, fault=r.fault, cause=r.cause, solution=r.solution,
        repair_process=r.repair_process, technical_measures=r.technical_measures,
        repair_result=r.repair_result, summary=r.summary,
        ticket_id=r.ticket_id,
        status=r.status, status_label=REPORT_STATUS_LABELS.get(r.status, r.status),
        submitter_id=r.submitter_id, submitter_name=r.submitter_name,
        submit_time_ts=_ts(r.submit_time),
        reviewer_name=r.reviewer_name, review_remark=r.review_remark,
        review_time_ts=_ts(r.review_time), sync_time_ts=_ts(r.sync_time),
        attachments=[
            {"id": a.id, "filename": a.filename, "size": a.file_size,
             "mime_type": a.mime_type, "uploaded_at_ts": _ts(a.uploaded_at)}
            for a in (r.attachments or [])
        ],
    )


def _to_case_info(c: Case) -> CaseInfo:
    # 员工贡献 = 有贡献者且角色是 worker
    is_employee = bool(c.source_report_id or c.contributor_name) and c.submitter_role == "worker"
    return CaseInfo(
        id=c.id, title=c.title, device=c.device, tag=c.tag,
        fault=c.fault, cause=c.cause, solution=c.solution, summary=c.summary,
        level=c.level, contributor_name=c.contributor_name,
        is_employee_contribution=is_employee,
        source_report_id=c.source_report_id,
        submitter_id=c.submitter_id,
        submitter_role=c.submitter_role,
        created_at_ts=_ts(c.created_at),
    )


def _parse_guide_steps(raw: Optional[str]) -> List[GuideStep]:
    if not raw:
        return []
    try:
        arr = json.loads(raw)
        return [GuideStep(step=int(s.get("step", i + 1)),
                          content=str(s.get("content", "")),
                          tip=s.get("tip"))
                for i, s in enumerate(arr)]
    except Exception:
        return []


def _parse_tools(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    try:
        arr = json.loads(raw)
        return [str(t) for t in arr] if isinstance(arr, list) else []
    except Exception:
        return []


def _parse_checklist(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    try:
        arr = json.loads(raw)
        return [str(item) for item in arr] if isinstance(arr, list) else []
    except Exception:
        return []


def _parse_preparation(raw: Optional[str]) -> list[dict]:
    if not raw:
        return []
    try:
        arr = json.loads(raw)
        return arr if isinstance(arr, list) else []
    except Exception:
        return []

def _reseed_guides(db: Session) -> None:
    """启动时从 guides.json 重新导入作业指导（清空旧数据后重建）。"""
    import json as _json
    from pathlib import Path as _Path
    guides_file = _Path(__file__).resolve().parent.parent.parent / "knowledge" / "data" / "guides.json"
    if not guides_file.is_file():
        return
    # 清空旧执行记录和指导
    db.query(GuideExecution).delete()
    db.query(Guide).delete()
    db.flush()
    with open(guides_file, "r", encoding="utf-8") as f:
        specs = _json.load(f)
    for spec in specs:
        steps_obj = [
            {"step": s.get("step", i + 1), "content": s.get("content", ""), "tip": s.get("tip", "")}
            for i, s in enumerate(spec.get("steps", []))
        ]
        checklist = spec.get("checklist", [])
        prep = spec.get("preparation", [])
        safety = spec.get("safety_control", [])
        accept = spec.get("acceptance_criteria", [])
        stop = spec.get("stop_conditions", [])
        g = Guide(
            title=spec.get("title", ""),
            device_type=spec.get("device_type", "机械"),
            tag=spec.get("tag"),
            steps_json=_json.dumps(steps_obj, ensure_ascii=False),
            risk_note=spec.get("risk_note"),
            duration_min=spec.get("duration_min"),
            difficulty=spec.get("difficulty"),
            tools_json=_json.dumps(spec.get("required_tools", []), ensure_ascii=False) if spec.get("required_tools") else None,
            applicable_devices=spec.get("applicable_devices"),
            scope=spec.get("scope"),
            maintenance_level=spec.get("maintenance_level"),
            checklist_json=_json.dumps(checklist, ensure_ascii=False) if checklist else None,
            preparation_json=_json.dumps(prep, ensure_ascii=False) if prep else None,
            safety_control_json=_json.dumps(safety, ensure_ascii=False) if safety else None,
            acceptance_criteria_json=_json.dumps(accept, ensure_ascii=False) if accept else None,
            stop_conditions_json=_json.dumps(stop, ensure_ascii=False) if stop else None,
        )
        db.add(g)
    db.commit()


def _to_guide_info(g: Guide) -> GuideInfo:
    steps = _parse_guide_steps(g.steps_json)
    tools = _parse_tools(g.tools_json)
    checklist = _parse_checklist(g.checklist_json)
    preparation = _parse_preparation(g.preparation_json)
    safety_control = _parse_checklist(g.safety_control_json)
    acceptance_criteria = _parse_checklist(g.acceptance_criteria_json)
    stop_conditions = _parse_checklist(g.stop_conditions_json)
    contrib = bool(g.source_report_id or g.contributor_name)
    return GuideInfo(
        id=g.id, title=g.title, device_type=g.device_type, tag=g.tag,
        steps=steps, steps_json=g.steps_json, risk_note=g.risk_note,
        duration_min=g.duration_min, difficulty=g.difficulty,
        tools=tools, applicable_devices=g.applicable_devices,
        scope=g.scope,
        maintenance_level=g.maintenance_level,
        checklist=checklist,
        preparation=preparation,
        safety_control=safety_control,
        acceptance_criteria=acceptance_criteria,
        stop_conditions=stop_conditions,
        contributor_name=g.contributor_name,
        is_employee_contribution=contrib,
        created_at_ts=_ts(g.created_at),
    )


def _to_user_full(u: User, db: Session) -> UserFullInfo:
    done = db.query(Ticket).filter(Ticket.assignee_id == u.id, Ticket.status == "done").count()
    doing = db.query(Ticket).filter(Ticket.assignee_id == u.id, Ticket.status == "doing").count()
    over = db.query(Ticket).filter(Ticket.assignee_id == u.id, Ticket.status == "over").count()
    return UserFullInfo(
        id=u.id, username=u.username, fullname=u.fullname,
        role=u.role, role_label=role_label_of(u.role),
        avatar_preset=u.avatar_preset, created_at_ts=_ts(u.created_at),
        ticket_stats={"done": done, "doing": doing, "over": over},
    )


# ============================================================
# B-1. 设备管理 API
# ============================================================

@app.get("/api/devices", response_model=ApiResp[PageResp[DeviceInfo]])
def list_devices(
    page: int = 1, size: int = 20, keyword: Optional[str] = None,
    tag: Optional[str] = None, status: Optional[str] = None,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Device)
    if tag:
        q = q.filter(Device.tag == tag)
    if status:
        q = q.filter(Device.status == status)
    if keyword:
        kw = f"%{keyword.strip()}%"
        from sqlalchemy import or_
        q = q.filter(or_(
            Device.code.ilike(kw), Device.name.ilike(kw),
            Device.location.ilike(kw),
        ))
    total = q.count()
    devices = q.order_by(Device.tag.asc(), Device.code.asc()) \
                .offset((page - 1) * size).limit(size).all()
    # 批量预加载故障上报信息，避免 N+1 查询
    _fault_reporters, _fault_attachments = _load_fault_data(db, devices)
    items = [_to_device_info(d, db, _fault_reporters, _fault_attachments) for d in devices]
    return ok(page_wrap(page, size, total, items))


@app.get("/api/devices/stats", response_model=ApiResp)
def devices_stats(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = db.query(Device).count()
    rows = db.query(Device.status, sqlalchemy_func.count(Device.id)) \
        .group_by(Device.status).all()
    by_status = {s: c for s, c in rows}
    tags = db.query(Device.tag, sqlalchemy_func.count(Device.id)) \
        .group_by(Device.tag).all()
    by_tag = [{t: c} for t, c in tags]
    return ok({
        "total": total,
        "by_status": {
            DEVICE_STATUS_LABELS.get(k, k): v for k, v in by_status.items()
        },
        "by_tag": by_tag,
    })


@app.get("/api/devices/{device_id}", response_model=ApiResp[DeviceInfo])
def get_device(device_id: int, current: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    d = db.query(Device).filter(Device.id == device_id).first()
    if not d:
        return fail("设备不存在", 404)
    _reporters, _attachments = _load_fault_data(db, [d])
    return ok(_to_device_info(d, db, _reporters, _attachments))




@app.post("/api/devices", response_model=ApiResp[DeviceInfo])
def create_device(form: DeviceCreate, current: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    require_admin(current)
    if db.query(Device).filter(Device.code == form.code.strip()).first():
        return fail("设备编号已存在", 400)
    d = Device(
        code=form.code.strip(), name=form.name.strip(),
        tag=form.tag or "机械", location=form.location,
        status=form.status or "normal",
        commission_date=form.commission_date,
    )
    db.add(d); db.commit(); db.refresh(d)
    return ok(_to_device_info(d, db), "设备创建成功")


@app.put("/api/devices/{device_id}", response_model=ApiResp[DeviceInfo])
def update_device(device_id: int, form: DeviceUpdate,
                  current: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    require_admin(current)
    d = db.query(Device).filter(Device.id == device_id).first()
    if not d:
        return fail("设备不存在", 404)
    if form.name is not None:
        d.name = form.name.strip()
    if form.tag is not None:
        d.tag = form.tag
    if form.location is not None:
        d.location = form.location
    if form.commission_date is not None:
        d.commission_date = form.commission_date
    if form.status is not None:
        d.status = form.status
        if form.status in ("repairing", "down"):
            d.last_repair_at = _utcnow()
    db.commit(); db.refresh(d)
    return ok(_to_device_info(d, db), "设备信息已更新")


@app.delete("/api/devices/{device_id}", response_model=ApiResp)
def delete_device(device_id: int, current: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    require_admin(current)
    d = db.query(Device).filter(Device.id == device_id).first()
    if not d:
        return fail("设备不存在", 404)
    # 清理故障附件物理文件（DB 记录由 relationship cascade 级联删除）
    for att in (d.fault_attachments or []):
        try:
            Path(att.file_path).unlink(missing_ok=True)
        except Exception:
            pass
    db.delete(d); db.commit()
    return ok(None, "设备已删除")


# ============================================================
# B-2. 工单管理 API
# ============================================================

@app.get("/api/tickets/team-ranking", response_model=ApiResp)
def get_team_ranking(current: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """Return this month's real completed-ticket ranking for all workers."""
    now = _utcnow()
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    completed = dict(
        db.query(Ticket.assignee_id, sqlalchemy_func.count(Ticket.id))
        .filter(
            Ticket.status == "done",
            Ticket.assignee_id.isnot(None),
            Ticket.finish_time >= month_start,
        )
        .group_by(Ticket.assignee_id)
        .all()
    )
    workers = db.query(User).filter(User.role == ROLE_WORKER).all()
    rows = []
    for worker in workers:
        skill = " / ".join(v for v in (worker.dept, worker.position) if v) or "设备维护"
        rows.append({
            "user_id": worker.id,
            "username": worker.username,
            "name": worker.fullname or worker.username,
            "skill": skill,
            "done": int(completed.get(worker.id, 0)),
            "me": worker.id == current.id,
        })
    rows.sort(key=lambda row: (-row["done"], row["user_id"]))
    for index, row in enumerate(rows):
        row["rank"] = index + 1
    return ok(rows)


@app.get("/api/tickets", response_model=ApiResp[PageResp[TicketInfo]])
def list_tickets(
    page: int = 1, size: int = 20, keyword: Optional[str] = None,
    status: Optional[str] = None, level: Optional[str] = None,
    scope: str = "all",   # all / mine / assigned / submitted
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Ticket)
    if status:
        q = q.filter(Ticket.status == status)
    if level:
        q = q.filter(Ticket.level == level)
    if scope == "mine":
        q = q.filter(
            (Ticket.assignee_id == current.id) |
            (Ticket.submitter_id == current.id)
        )
    elif scope == "assigned":
        require_admin(current)
        q = q.filter(Ticket.assignee_id.isnot(None))
    elif scope == "submitted":
        q = q.filter(Ticket.submitter_id == current.id)
    if keyword:
        kw = f"%{keyword.strip()}%"
        from sqlalchemy import or_
        q = q.filter(or_(
            Ticket.title.ilike(kw), Ticket.code.ilike(kw),
            Ticket.device_name.ilike(kw), Ticket.problem.ilike(kw),
        ))
    total = q.count()
    rows = q.order_by(Ticket.submit_time.desc()) \
        .offset((page - 1) * size).limit(size).all()
    items = [_to_ticket_info(t, db) for t in rows]
    return ok(page_wrap(page, size, total, items))


@app.get("/api/tickets/{ticket_id}", response_model=ApiResp[TicketInfo])
def get_ticket(ticket_id: int, current: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    t = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not t:
        return fail("工单不存在", 404)
    return ok(_to_ticket_info(t, db))


@app.post("/api/tickets", response_model=ApiResp[TicketInfo])
def create_ticket(form: TicketCreate, current: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    dev_name = form.device_name
    device = None
    if form.device_id:
        device = db.query(Device).filter(Device.id == form.device_id).first()
    elif dev_name:
        # 兼容旧前端：从“设备编号 设备名称”中识别设备编号。
        device_code = dev_name.strip().split(maxsplit=1)[0]
        device = db.query(Device).filter(Device.code == device_code).first()
        if not device:
            device = db.query(Device).filter(Device.name == dev_name.strip()).first()
    if device and not dev_name:
        dev_name = f"{device.code} {device.name}"
    now = _utcnow()
    code_date = now.astimezone(APP_TIMEZONE).strftime("%Y%m%d")
    existing_codes = [r[0] for r in db.query(Ticket.code).filter(Ticket.code.like(f"TK-{code_date}-%")).all()]
    seq = len(existing_codes) + 1
    while f"TK-{code_date}-{seq:03d}" in existing_codes:
        seq += 1
    code = f"TK-{code_date}-{seq:03d}"
    assignee_id = form.assignee_id
    assigned_user = None
    # 即使创建时已指定维修工，也必须由维修工确认接单后才进入“进行中”。
    status = TICKET_ASSIGNED if assignee_id else TICKET_PENDING
    if assignee_id:
        assigned_user = db.query(User).filter(User.id == assignee_id).first()
        if not assigned_user or assigned_user.role not in (ROLE_WORKER, ROLE_MANAGER, ROLE_SYSADMIN):
            return fail("派单目标用户不存在或不是维修人员", 400)
    t = Ticket(
        code=code, title=form.title.strip(),
        device_id=device.id if device else form.device_id, device_name=dev_name,
        category=form.category,
        level=form.level or "mid", status=status,
        submitter_id=current.id, assignee_id=assignee_id,
        problem=form.problem.strip(), submit_time=now,
        extra=(
            json.dumps(
                {"dispatch_remark": form.remark.strip()},
                ensure_ascii=False,
            )
            if form.remark and form.remark.strip()
            else None
        ),
    )
    db.add(t); db.commit(); db.refresh(t)

    # 通知管理员有新工单待处理
    admins = db.query(User).filter(User.role.in_(["sysadmin", "manager"])).all()
    _push_notify(
        db, user_ids=[a.id for a in admins],
        type=NOTIFY_TYPE_TICKET_CREATED,
        title=f"🎫 新工单待处理：{form.title.strip()}",
        content=f"提交人：{current.fullname or current.username}，设备：{dev_name}，等级：{form.level or 'mid'}",
        related_id=t.id,
    )
    if assigned_user:
        _push_notify(
            db, user_ids=[assigned_user.id],
            type=NOTIFY_TYPE_TICKET_ASSIGNED,
            title="🎫 新工单已派发给您",
            content=(
                f"管理员【{current.fullname or current.username}】将工单《{t.title}》"
                "派发给您，请确认接单并及时处理。"
            ),
            related_id=t.id,
        )

    return ok(_to_ticket_info(t, db), "工单创建成功" + ("并已派单" if assignee_id else "，等待派单"))


@app.post("/api/tickets/{ticket_id}/assign", response_model=ApiResp[TicketInfo])
def assign_ticket(ticket_id: int, form: TicketAssign,
                  current: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    require_admin(current)
    t = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not t:
        return fail("工单不存在", 404)
    u = db.query(User).filter(User.id == form.assignee_id).first()
    if not u or u.role == ROLE_SYSADMIN and False:  # sysadmin 也允许接单
        pass
    if not u:
        return fail("目标维修员不存在", 400)
    t.assignee_id = u.id
    # 派单只指定负责人，维修工确认前仍属于待处理状态。
    if t.status not in (TICKET_PENDING, TICKET_ASSIGNED):
        return fail("只有待派单或待处理工单可以派单", 400)
    t.status = TICKET_ASSIGNED
    if form.level and form.level in ("low", "mid", "high"):
        t.level = form.level
    if form.remark and form.remark.strip():
        extra_data = {}
        if t.extra:
            try:
                parsed = json.loads(t.extra)
                if isinstance(parsed, dict):
                    extra_data = parsed
            except (TypeError, ValueError):
                pass
        extra_data["dispatch_remark"] = form.remark.strip()
        t.extra = json.dumps(extra_data, ensure_ascii=False)
    db.commit(); db.refresh(t)
    _push_notify(
        db, user_ids=[u.id],
        type=NOTIFY_TYPE_TICKET_ASSIGNED,
        title=f"🎫 新工单已派发给您",
        content=f"管理员【{current.fullname}】将工单《{t.title}》派发给您，请确认接单并及时处理。",
        related_id=t.id,
    )
    return ok(_to_ticket_info(t, db), f"已派单给 {u.fullname}")


@app.post("/api/tickets/{ticket_id}/accept", response_model=ApiResp[TicketInfo])
def accept_ticket(ticket_id: int, current: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    t = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not t:
        return fail("工单不存在", 404)
    if not t.assignee_id:
        return fail("该工单尚未派单，无法确认接单", 400)
    if t.assignee_id != current.id:
        return fail("该工单已指派给其他人，您无法接单", 403)
    if t.status != TICKET_ASSIGNED:
        return fail("该工单已确认或无法接单", 400)
    t.status = TICKET_DOING
    if t.device_id:
        device = db.query(Device).filter(Device.id == t.device_id).first()
        if device and device.status == DEVICE_STATUS_DOWN:
            device.status = DEVICE_STATUS_REPAIRING
    db.commit(); db.refresh(t)
    return ok(_to_ticket_info(t, db), "接单成功")


@app.post("/api/tickets/{ticket_id}/complete", response_model=ApiResp[TicketInfo])
def complete_ticket(ticket_id: int, form: TicketComplete,
                    current: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    t = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not t:
        return fail("工单不存在", 404)
    if t.assignee_id != current.id and not is_admin_role(current.role):
        return fail("只有接单人或管理员可以提交完成", 403)
    t.solution = form.solution.strip()
    t.status = "done"
    t.finish_time = _utcnow()
    if t.device_id:
        d = db.query(Device).filter(Device.id == t.device_id).first()
        if d and d.status in ("repairing", "down"):
            d.status = "normal"
            d.last_repair_at = t.finish_time
    db.commit(); db.refresh(t)
    return ok(_to_ticket_info(t, db), "维修报告已提交，工单完成")


@app.post("/api/tickets/{ticket_id}/mark_overdue", response_model=ApiResp[TicketInfo])
def mark_ticket_overdue(ticket_id: int, current: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    require_admin(current)
    t = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not t:
        return fail("工单不存在", 404)
    t.status = "over"
    db.commit(); db.refresh(t)
    return ok(_to_ticket_info(t, db), "已标记为超时工单")


@app.delete("/api/tickets/{ticket_id}", response_model=ApiResp)
def delete_ticket(ticket_id: int, current: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    require_admin(current)
    t = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not t:
        return fail("工单不存在", 404)
    db.delete(t)
    db.commit()
    return ok(None, "工单已删除")


@app.post("/api/tickets/{ticket_id}/recommend-guides", response_model=ApiResp)
def recommend_guides_for_ticket(
    ticket_id: int,
    current: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """根据工单的设备类型+检修等级+故障描述+适用设备，加权匹配最相关的作业指导。"""

    # ── 权重配置 ──
    W_DEVICE_TYPE = 30      # 设备类型匹配（硬过滤后全部获得）
    W_SEMANTIC = 40         # 故障/任务语义匹配
    W_LEVEL = 20            # 检修等级匹配
    W_SCOPE = 10            # 适用范围/关键词匹配
    TOTAL = W_DEVICE_TYPE + W_SEMANTIC + W_LEVEL + W_SCOPE

    t = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not t:
        return fail("工单不存在", 404)

    # 设备标签 → Guide.device_type 映射
    _TAG_TO_DEVICE_TYPE = {
        "机械动力": "机械", "综合": "综合", "机械传动": "机械", "机加工": "机械",
        "电气控制": "电气",
        "液压执行": "液压",
        "工业仪表": "仪表",
        "安全保护": "安全",
    }

    device_type = "机械"
    if t.device_id:
        d = db.query(Device).filter(Device.id == t.device_id).first()
        if d and d.tag:
            device_type = _TAG_TO_DEVICE_TYPE.get(d.tag, d.tag)
    if device_type not in ("机械", "电气", "液压", "仪表", "安全"):
        device_type = "机械"

    level = t.level
    device_name = (t.device_name or "").strip()

    # ── 第一层：设备类型硬过滤（只取同类型设备） ──
    candidates = db.query(Guide).filter(
        Guide.device_type == device_type
    ).order_by(Guide.difficulty.asc().nullslast()).all()

    # 如果该类型一条指导都没有，返回空
    if not candidates:
        return ok({"recommended": []})

    # 提取设备名称中的关键词（供后续适用设备匹配用）
    import re as _re
    name_tokens = set()
    if device_name:
        _stop_words = {"设备", "系统", "站", "柜", "机", "器"}
        name_tokens = set(
            w for w in _re.split(r"[\s\-、，/]", device_name)
            if len(w) >= 2 and w not in _stop_words
        )

    # ── 为每条候选指导计算各维度分数 ──
    # 1) 设备类型分（全部 30 分，因为已硬过滤）
    # 2) 语义分（后面统一算）
    # 3) 等级分
    # 4) 适用设备/关键词分

    # 先算语义分（需要一次 embed）
    semantic_scores = {}
    problem = (t.problem or "").strip()
    if problem:
        try:
            guide_texts = []
            for g in candidates:
                steps_text = ""
                try:
                    steps = json.loads(g.steps_json) if g.steps_json else []
                    steps_text = " ".join(s.get("content", "") for s in steps)
                except Exception:
                    pass
                guide_texts.append(f"{g.title} {steps_text} {g.risk_note or ''}")
            all_texts = [problem] + guide_texts
            vectors = embed_texts(all_texts)
            if len(vectors) == len(all_texts):
                query_vec = vectors[0]
                for idx, g in enumerate(candidates):
                    guide_vec = vectors[idx + 1]
                    dot = sum(a * b for a, b in zip(query_vec, guide_vec))
                    semantic_scores[g.id] = max(0, dot)  # 截断到 [0,1]
        except Exception:
            pass

    # 逐条算总分
    scored = []
    for g in candidates:
        # 等级分 (0-20)
        if g.maintenance_level == level:
            level_score = W_LEVEL
        elif g.maintenance_level:
            level_score = W_LEVEL * 0.5  # 等级不同，拿一半分
        else:
            level_score = 0

        # 适用范围/关键词分 (0-10)
        scope_score = 0
        if device_name and g.applicable_devices:
            if device_name in g.applicable_devices:
                scope_score = W_SCOPE
            elif name_tokens:
                # 关键词部分命中
                dev_text = (g.applicable_devices or "")
                hits = sum(1 for tk in name_tokens if tk in dev_text)
                if hits >= 2:
                    scope_score = W_SCOPE
                elif hits == 1:
                    scope_score = W_SCOPE * 0.5

        # 语义分 (0-40)
        sem_score = semantic_scores.get(g.id, 0) * W_SEMANTIC

        # 设备类型分（30，硬过滤已通过）
        type_score = W_DEVICE_TYPE

        total = type_score + sem_score + level_score + scope_score
        scored.append((total, g, level_score, scope_score, sem_score))

    # 按总分降序排列
    scored.sort(key=lambda x: x[0], reverse=True)
    top_score = scored[0][0] if scored else TOTAL

    # 构造返回结果
    results = []
    for total, g, lv_score, sc_score, sem_score_raw in scored:
        guide_info = _to_guide_info(g)

        # 匹配理由
        parts = []
        if g.device_type == device_type:
            parts.append("设备类型匹配")
        if g.maintenance_level == level:
            parts.append("等级匹配")
        elif g.maintenance_level:
            parts.append("等级不同")
        if sc_score > 0:
            parts.append("适用设备匹配")
        match_reason = " + ".join(parts)

        # 归一化匹配度（展示用）
        match_pct = round(total / TOTAL * 100)

        results.append({
            "guide": guide_info.model_dump() if hasattr(guide_info, "model_dump") else guide_info.dict(),
            "match_reason": match_reason,
            "match_score": match_pct,
        })

    # ---- 动态流程生成：当所有预置指南匹配度均低于阈值时，调用 LLM 自适应生成 ----
    DYNAMIC_THRESHOLD = 40  # 最高分低于此阈值时触发动态生成
    dynamic_guide = None
    if results and results[0]["match_score"] < DYNAMIC_THRESHOLD and problem:
        try:
            device_tag = device_type or "机械"
            gen_prompt = (
                f"你是工业设备检修专家。请为以下维修任务生成结构化的检修作业步骤。\n"
                f"设备类型：{device_tag}\n"
                f"检修等级：{level}\n"
                f"设备名称：{device_name or '未指定'}\n"
                f"故障描述：{problem}\n\n"
                f"请严格按照 JSON 格式输出（不要使用 Markdown 代码围栏）：\n"
                f"{{\n"
                f'  "title": "检修步骤标题",\n'
                f'  "steps": [\n'
                f'    {{"step": 1, "content": "具体操作步骤", "tip": "注意事项"}}\n'
                f"  ],\n"
                f'  "risk_note": "总体风险提醒",\n'
                f'  "required_tools": ["工具1", "工具2"],\n'
                f'  "estimated_duration_min": 60\n'
                f"}}\n"
                f"要求：步骤必须专业、可操作、安全合规。涉及高压/旋转/高温必须给出安全提醒。"
            )
            gen_result, gen_via = _llm_chat_request(gen_prompt, problem)
            if gen_result:
                import json as _json
                try:
                    gen_data = _json.loads(gen_result)
                    if isinstance(gen_data, dict) and "steps" in gen_data:
                        dynamic_guide = {
                            "title": gen_data.get("title", f"{device_tag}设备 {level}级检修"),
                            "steps": gen_data.get("steps", []),
                            "risk_note": gen_data.get("risk_note", ""),
                            "required_tools": gen_data.get("required_tools", []),
                            "estimated_duration_min": gen_data.get("estimated_duration_min", 60),
                            "generated": True,
                        }
                except _json.JSONDecodeError:
                    pass
        except Exception:
            dynamic_guide = None

    response_data = {
        "recommended": results,
        "device_type": device_type,
        "level": level,
    }
    if dynamic_guide:
        response_data["dynamic_guide"] = dynamic_guide
        response_data["dynamic_guide_note"] = "未能匹配到完全合适的预置作业指导，已由 AI 根据故障描述动态生成，请现场核对后使用"

    return ok(response_data)

# ============================================================
# 工单附件 API
# ============================================================
import os
import uuid
from pathlib import Path
from fastapi import File, Form, UploadFile
from fastapi.responses import FileResponse

ATTACHMENT_DIR = Path(__file__).resolve().parent.parent / "data" / "attachments"
ATTACHMENT_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_ATTACH_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_ATTACH_SIZE = 10 * 1024 * 1024  # 10MB


@app.post("/api/devices/report-fault", response_model=ApiResp)
async def report_device_fault(device_id: Optional[str] = Form(None),
                              code: str = Form(""), name: str = Form(""),
                              tag: str = Form("机械"), location: str = Form(""),
                              spec: str = Form(""),
                              desc: str = Form(...),
                              files: list[UploadFile] = File(default=[]),
                              current: User = Depends(get_current_user),
                              db: Session = Depends(get_db)):
    try:
        if not name.strip():
            return fail("请填写设备名称", 400)
        # 已有设备
        if device_id and device_id != "__other__":
            dev = db.query(Device).filter(Device.id == int(device_id)).first()
            if not dev:
                return fail("设备不存在", 404)
            dev.status = DEVICE_STATUS_DOWN
            dev.fault_desc = desc.strip()[:2000]
            dev.fault_reporter_id = current.id
            dev.fault_time = _utcnow()
        else:
            # 手动输入新设备（code 用 uuid 避免同秒重复提交冲突）
            dev = Device(code=code.strip() or f"MANUAL-{uuid.uuid4().hex[:10].upper()}",
                         name=name.strip(), tag=tag, location=location.strip(),
                         spec=spec.strip(), status=DEVICE_STATUS_DOWN,
                         fault_desc=desc.strip()[:2000], fault_reporter_id=current.id, fault_time=_utcnow())
            db.add(dev); db.flush()
        db.commit(); db.refresh(dev)
        # 处理多附件（写入设备故障附件表，避免外键错配 tickets.id）
        attach_list = []
        for file in files:
            if not file.filename:
                continue
            mime = (file.content_type or "").lower()
            if mime not in ALLOWED_ATTACH_TYPES:
                continue
            content = await file.read(MAX_ATTACH_SIZE + 1)
            await file.close()
            if len(content) > MAX_ATTACH_SIZE or not content:
                continue
            orig_name = file.filename or "upload"
            suffix = Path(orig_name).suffix.lower()
            if suffix not in (".jpg", ".jpeg", ".png", ".webp", ".pdf"):
                suffix = ""
            safe_name = f"{uuid.uuid4().hex}{suffix}"
            save_path = ATTACHMENT_DIR / safe_name
            with open(save_path, "wb") as f:
                f.write(content)
            att = DeviceFaultAttachment(device_id=dev.id, filename=orig_name[:255],
                                        file_path=str(save_path), file_size=len(content), mime_type=mime)
            db.add(att)
            attach_list.append({"filename": att.filename, "size": att.file_size})
        db.commit()
        # 通知管理员
        admins = db.query(User).filter(User.role.in_([ROLE_SYSADMIN, ROLE_MANAGER])).all()
        _push_notify(db, user_ids=[a.id for a in admins], type=NOTIFY_TYPE_DEVICE_FAULT,
                     title=f"⚠️ 设备故障上报：{dev.code} {dev.name}",
                     content=f"上报人：{current.fullname or current.username}，描述：{desc[:100]}",
                     related_id=dev.id)
        return ok({"device_id": dev.id, "status": dev.status, "attachments": attach_list},
                  "故障已上报，已通知管理员")
    except Exception as e:
        db.rollback()
        return fail(f"上报失败：{str(e)[:200]}", 400)


@app.post("/api/tickets/{ticket_id}/attachments", response_model=ApiResp)
async def upload_attachment(ticket_id: int, file: UploadFile = File(...),
                      current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not t:
        return fail("工单不存在", 404)
    # 权限：仅提交人或管理员可上传
    if current.id != t.submitter_id and current.role not in ("sysadmin", "manager"):
        return fail("无权操作此工单", 403)
    # 文件类型校验
    mime = (file.content_type or "").lower()
    if mime not in ALLOWED_ATTACH_TYPES:
        return fail("仅支持 JPG/PNG/WebP/PDF 文件", 400)
    # 文件大小校验
    content = await file.read(MAX_ATTACH_SIZE + 1)
    await file.close()
    if len(content) > MAX_ATTACH_SIZE:
        return fail(f"文件不能超过 {MAX_ATTACH_SIZE // 1024 // 1024}MB", 413)
    if not content:
        return fail("上传文件为空", 400)
    # UUID 命名 + 保留原始后缀
    orig_name = file.filename or "upload"
    suffix = Path(orig_name).suffix.lower()
    if suffix not in (".jpg", ".jpeg", ".png", ".webp", ".pdf"):
        suffix = ""
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    save_path = ATTACHMENT_DIR / safe_name
    with open(save_path, "wb") as f:
        f.write(content)
    # DB 记录
    att = TicketAttachment(ticket_id=ticket_id, filename=orig_name[:255],
                           file_path=str(save_path), file_size=len(content),
                           mime_type=mime)
    db.add(att); db.commit(); db.refresh(att)
    return ok({"id": att.id, "filename": att.filename, "size": att.file_size,
               "mime_type": att.mime_type, "uploaded_at_ts": _ts(att.uploaded_at)},
              "附件上传成功")


@app.get("/api/tickets/{ticket_id}/attachments", response_model=ApiResp)
def list_attachments(ticket_id: int, current: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    t = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not t:
        return fail("工单不存在", 404)
    if current.id != t.submitter_id and current.role not in ("sysadmin", "manager"):
        return fail("无权操作此工单", 403)
    items = db.query(TicketAttachment).filter(TicketAttachment.ticket_id == ticket_id).all()
    return ok([{"id": a.id, "filename": a.filename, "size": a.file_size,
                "mime_type": a.mime_type, "uploaded_at_ts": _ts(a.uploaded_at)}
               for a in items])


@app.delete("/api/tickets/{ticket_id}/attachments/{attachment_id}", response_model=ApiResp)
def delete_attachment(ticket_id: int, attachment_id: int,
                      current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not t:
        return fail("工单不存在", 404)
    if current.id != t.submitter_id and current.role not in ("sysadmin", "manager"):
        return fail("无权操作此工单", 403)
    att = db.query(TicketAttachment).filter(
        TicketAttachment.id == attachment_id, TicketAttachment.ticket_id == ticket_id).first()
    if not att:
        return fail("附件不存在", 404)
    # 删除物理文件
    try:
        Path(att.file_path).unlink(missing_ok=True)
    except Exception:
        pass
    db.delete(att); db.commit()
    return ok(None, "附件已删除")


def _backfill_notification_history_if_empty(db: Session) -> None:
    """Fill missing historical notifications without duplicating existing rows."""
    existing = {
        (row.user_id, row.type, row.related_id)
        for row in db.query(Notification).all()
    }
    rows = []
    admins = _admin_ids(db)
    tickets = db.query(Ticket).all()
    for ticket in tickets:
        key = (ticket.assignee_id, NOTIFY_TYPE_TICKET_ASSIGNED, ticket.id)
        if ticket.assignee_id and key not in existing:
            rows.append(Notification(
                user_id=ticket.assignee_id,
                type=NOTIFY_TYPE_TICKET_ASSIGNED,
                title=f"维修工单已派发：{ticket.code or ticket.title}",
                content=ticket.problem or ticket.title or "",
                related_id=ticket.id,
                is_read=1,
                created_at=ticket.submit_time,
            ))
        for admin_id in admins:
            admin_key = (admin_id, NOTIFY_TYPE_TICKET_CREATED, ticket.id)
            if admin_key in existing:
                continue
            rows.append(Notification(
                user_id=admin_id,
                type=NOTIFY_TYPE_TICKET_CREATED,
                title=f"历史维修工单：{ticket.code or ticket.title}",
                content=ticket.problem or ticket.title or "",
                related_id=ticket.id,
                is_read=1,
                created_at=ticket.submit_time,
            ))

    fault_devices = db.query(Device).filter(Device.fault_time.isnot(None)).all()
    for device in fault_devices:
        for admin_id in admins:
            key = (admin_id, NOTIFY_TYPE_DEVICE_FAULT, device.id)
            if key in existing:
                continue
            rows.append(Notification(
                user_id=admin_id,
                type=NOTIFY_TYPE_DEVICE_FAULT,
                title=f"设备故障上报：{device.code} {device.name}",
                content=device.fault_desc or "",
                related_id=device.id,
                is_read=1,
                created_at=device.fault_time,
            ))

    reports = db.query(KnowledgeReport).all()
    for report in reports:
        for admin_id in admins:
            key = (admin_id, NOTIFY_TYPE_REPORT_SUBMITTED, report.id)
            if key in existing:
                continue
            rows.append(Notification(
                user_id=admin_id,
                type=NOTIFY_TYPE_REPORT_SUBMITTED,
                title=f"员工贡献方案待审核：{report.submitter_name} 提交了《{report.title}》",
                content=report.summary or report.solution or "",
                related_id=report.id,
                is_read=1,
                created_at=report.submit_time,
            ))

    report_types = {
        "approved": (NOTIFY_TYPE_REPORT_APPROVED, "贡献方案审核通过"),
        "rejected": (NOTIFY_TYPE_REPORT_REJECTED, "贡献方案被驳回"),
        "synced_case": (NOTIFY_TYPE_REPORT_SYNCED, "贡献方案已入库"),
        "synced_guide": (NOTIFY_TYPE_REPORT_SYNCED, "贡献方案已入库"),
    }
    for report in reports:
        if report.status == "pending":
            continue
        notify_type, prefix = report_types.get(
            report.status, (NOTIFY_TYPE_SYSTEM, "贡献方案状态更新")
        )
        key = (report.submitter_id, notify_type, report.id)
        if key in existing:
            continue
        rows.append(Notification(
            user_id=report.submitter_id,
            type=notify_type,
            title=f"{prefix}：《{report.title}》",
            content=report.review_remark or report.summary or "",
            related_id=report.id,
            is_read=1,
            created_at=report.review_time or report.submit_time,
        ))

    if rows:
        db.add_all(rows)
        db.commit()



@app.get("/api/attachments/{attachment_id}")
def download_attachment(attachment_id: int, current: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    att = db.query(TicketAttachment).filter(TicketAttachment.id == attachment_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="附件不存在")
    t = db.query(Ticket).filter(Ticket.id == att.ticket_id).first()
    if not t or (current.id != t.submitter_id and current.role not in ("sysadmin", "manager")):
        raise HTTPException(status_code=403, detail="无权访问")
    return FileResponse(
        att.file_path,
        media_type=att.mime_type or "application/octet-stream",
        filename=att.filename,
        content_disposition_type="inline",
    )


# ============================================================
# 设备故障附件 API
# ============================================================
@app.get("/api/devices/{device_id}/fault-attachments/{attachment_id}")
def download_device_fault_attachment(device_id: int, attachment_id: int,
                                     current: User = Depends(get_current_user),
                                     db: Session = Depends(get_db)):
    att = db.query(DeviceFaultAttachment).filter(
        DeviceFaultAttachment.id == attachment_id,
        DeviceFaultAttachment.device_id == device_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="附件不存在")
    if current.role not in (ROLE_SYSADMIN, ROLE_MANAGER):
        raise HTTPException(status_code=403, detail="无权访问")
    return FileResponse(
        att.file_path,
        media_type=att.mime_type or "application/octet-stream",
        filename=att.filename,
        content_disposition_type="inline",
    )


@app.delete("/api/devices/{device_id}/fault-attachments/{attachment_id}", response_model=ApiResp)
def delete_device_fault_attachment(device_id: int, attachment_id: int,
                                   current: User = Depends(get_current_user),
                                   db: Session = Depends(get_db)):
    require_admin(current)
    att = db.query(DeviceFaultAttachment).filter(
        DeviceFaultAttachment.id == attachment_id,
        DeviceFaultAttachment.device_id == device_id).first()
    if not att:
        return fail("附件不存在", 404)
    try:
        Path(att.file_path).unlink(missing_ok=True)
    except Exception:
        pass
    db.delete(att); db.commit()
    return ok(None, "附件已删除")


# ============================================================
# B-3. 知识报告 API
# ============================================================

@app.get("/api/reports", response_model=ApiResp[PageResp[ReportInfo]])
def list_reports(
    page: int = 1, size: int = 20, keyword: Optional[str] = None,
    status: Optional[str] = None, type: Optional[str] = None,
    scope: str = "all",   # all / mine / pending
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(KnowledgeReport)
    if status:
        q = q.filter(KnowledgeReport.status == status)
    if type:
        q = q.filter(KnowledgeReport.type == type)
    if scope == "mine":
        q = q.filter(KnowledgeReport.submitter_id == current.id)
    elif scope == "pending" and not is_admin_role(current.role):
        q = q.filter(KnowledgeReport.submitter_id == current.id,
                     KnowledgeReport.status == "pending")
    if keyword:
        kw = f"%{keyword.strip()}%"
        from sqlalchemy import or_
        q = q.filter(or_(
            KnowledgeReport.title.ilike(kw), KnowledgeReport.rid.ilike(kw),
            KnowledgeReport.device.ilike(kw),
            KnowledgeReport.question.ilike(kw),
            KnowledgeReport.solution.ilike(kw),
        ))
    total = q.count()
    rows = q.order_by(KnowledgeReport.submit_time.desc()) \
        .offset((page - 1) * size).limit(size).all()
    items = [_to_report_info(r) for r in rows]
    return ok(page_wrap(page, size, total, items))


@app.get("/api/reports/{report_id}", response_model=ApiResp[ReportInfo])
def get_report(report_id: int, current: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    r = db.query(KnowledgeReport).filter(KnowledgeReport.id == report_id).first()
    if not r:
        return fail("报告不存在", 404)
    return ok(_to_report_info(r))


@app.post("/api/reports", response_model=ApiResp[ReportInfo])
def create_report(form: ReportCreate, current: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    now = _utcnow()
    idx = db.query(KnowledgeReport).count() + 1
    rid = f"KR-{now.strftime('%Y%m%d')}-{idx:03d}"
    r = KnowledgeReport(
        rid=rid, title=form.title.strip(), device=form.device,
        type=form.type or "case", source=form.source or "manual",
        level=form.level, tag=form.tag,
        question=form.question.strip(), fault=form.fault,
        cause=form.cause, solution=form.solution.strip(),
        repair_process=form.repair_process,
        technical_measures=form.technical_measures,
        repair_result=form.repair_result,
        summary=form.summary or (form.solution[:80] + ("…" if len(form.solution) > 80 else "")),
        ticket_id=form.ticket_id,
        status="pending",
        submitter_id=current.id, submitter_name=current.fullname,
        submit_time=now,
    )
    db.add(r); db.commit(); db.refresh(r)
    # 给所有管理员发通知：有新的实践报告待审核
    _push_notify(
        db, user_ids=_admin_ids(db),
        type=NOTIFY_TYPE_REPORT_SUBMITTED,
        title=f"📝 新实践报告待审核：{r.submitter_name} 提交了《{r.title}》",
        content=r.summary or (r.solution[:80] + ("…" if len(r.solution) > 80 else "")),
        related_id=r.id,
    )
    return ok(_to_report_info(r), "方案报告已提交，等待管理员审核")


@app.post("/api/reports/{report_id}/attachments", response_model=ApiResp)
async def upload_report_attachment(report_id: int, file: UploadFile = File(...),
                                   current: User = Depends(get_current_user),
                                   db: Session = Depends(get_db)):
    report = db.query(KnowledgeReport).filter(KnowledgeReport.id == report_id).first()
    if not report:
        return fail("报告不存在", 404)
    if report.submitter_id != current.id and not is_admin_role(current.role):
        return fail("无权操作此报告", 403)
    mime = (file.content_type or "").lower()
    if mime not in ALLOWED_ATTACH_TYPES:
        return fail("仅支持 JPG/PNG/WebP/PDF 文件", 400)
    content = await file.read(MAX_ATTACH_SIZE + 1)
    await file.close()
    if len(content) > MAX_ATTACH_SIZE:
        return fail(f"文件不能超过 {MAX_ATTACH_SIZE // 1024 // 1024}MB", 413)
    if not content:
        return fail("上传文件为空", 400)
    orig_name = file.filename or "upload"
    suffix = Path(orig_name).suffix.lower()
    if suffix not in (".jpg", ".jpeg", ".png", ".webp", ".pdf"):
        suffix = ""
    save_path = ATTACHMENT_DIR / f"{uuid.uuid4().hex}{suffix}"
    with open(save_path, "wb") as out:
        out.write(content)
    att = ReportAttachment(
        report_id=report.id, filename=orig_name[:255], file_path=str(save_path),
        file_size=len(content), mime_type=mime
    )
    db.add(att); db.commit(); db.refresh(att)
    return ok({"id": att.id, "filename": att.filename, "size": att.file_size,
               "mime_type": att.mime_type, "uploaded_at_ts": _ts(att.uploaded_at)},
              "附件上传成功")


@app.get("/api/reports/{report_id}/attachments/{attachment_id}")
def view_report_attachment(report_id: int, attachment_id: int,
                           current: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    report = db.query(KnowledgeReport).filter(KnowledgeReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    if report.submitter_id != current.id and not is_admin_role(current.role):
        raise HTTPException(status_code=403, detail="无权访问")
    att = db.query(ReportAttachment).filter(
        ReportAttachment.id == attachment_id,
        ReportAttachment.report_id == report_id
    ).first()
    if not att:
        raise HTTPException(status_code=404, detail="附件不存在")
    return FileResponse(
        att.file_path,
        media_type=att.mime_type or "application/octet-stream",
        filename=att.filename,
        content_disposition_type="inline",
    )


@app.post("/api/reports/{report_id}/review", response_model=ApiResp[ReportInfo])
def review_report(report_id: int, form: ReportReview,
                  current: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    require_admin(current)
    r = db.query(KnowledgeReport).filter(KnowledgeReport.id == report_id).first()
    if not r:
        return fail("报告不存在", 404)
    action = (form.action or "").strip().lower()
    now = _utcnow()
    r.reviewer_id = current.id
    r.reviewer_name = current.fullname
    r.review_time = now
    r.review_remark = form.remark or ""

    if action == "reject":
        if not (form.remark or "").strip():
            return fail("驳回必须填写审核意见", 400)
        r.status = "rejected"
        db.commit(); db.refresh(r)
        _push_notify(
            db, user_ids=[r.submitter_id],
            type=NOTIFY_TYPE_REPORT_REJECTED,
            title=f"❌ 您的实践报告《{r.title}》被驳回",
            content=f"管理员【{r.reviewer_name or current.fullname}】意见：{r.review_remark}。仅知识实践报告被驳回，关联维修工单状态不受影响。",
            related_id=r.id,
        )
        return ok(_to_report_info(r), "已驳回该报告")

    if action == "approve":
        r.status = "approved"
        db.commit(); db.refresh(r)
        _push_notify(
            db, user_ids=[r.submitter_id],
            type=NOTIFY_TYPE_REPORT_APPROVED,
            title=f"✅ 您的实践报告《{r.title}》审核通过（待入库）",
            content=(r.review_remark or f"管理员【{r.reviewer_name or current.fullname}】已审核通过，稍后将同步入库。"),
            related_id=r.id,
        )
        return ok(_to_report_info(r), "审核通过（尚未入库，请使用 sync_case / sync_guide 操作入库）")

    if action == "sync_case":
        if r.status == "synced_case":
            return fail("该报告已同步为案例，请勿重复操作", 400)
        # 若已存在对应 case 则更新，否则新增
        existing = db.query(Case).filter(Case.source_report_id == r.id).first()
        # 获取提交者角色
        _submitter_role = None
        if r.submitter_id:
            _u = db.query(User).filter(User.id == r.submitter_id).first()
            _submitter_role = _u.role if _u else None
        if existing:
            existing.title = r.title
            existing.device = r.device
            existing.tag = r.tag or "综合"
            existing.fault = r.fault or r.question
            existing.cause = r.cause
            existing.solution = r.solution
            existing.summary = r.summary
            existing.level = r.level or "mid"
            existing.contributor_name = r.submitter_name
            existing.submitter_id = r.submitter_id
            existing.submitter_role = _submitter_role
        else:
            c = Case(
                title=r.title, device=r.device, tag=r.tag or "综合",
                fault=r.fault or r.question, cause=r.cause, solution=r.solution,
                summary=r.summary, level=r.level or "mid",
                source_report_id=r.id, contributor_name=r.submitter_name,
                submitter_id=r.submitter_id,
                submitter_role=_submitter_role,
                created_at=now,
            )
            db.add(c)
        r.status = "synced_case"
        r.sync_time = now
        if not r.review_remark:
            r.review_remark = "管理员审核通过，已同步入库案例库，感谢贡献！"
        db.commit(); db.refresh(r)
        
        saved_case = db.query(Case).filter(Case.source_report_id == r.id).first()
        if saved_case:
            save_case({
                "case_id": f"CASE-{saved_case.id:04d}",
                "source_report_id": saved_case.source_report_id,
                "title": saved_case.title,
                "device": saved_case.device or "",
                "fault": saved_case.fault or "",
                "reason": saved_case.cause or "",
                "solution": saved_case.solution or "",
                "experience": saved_case.summary or "",
                "author": saved_case.contributor_name or "",
                "create_time": str(saved_case.created_at) if saved_case.created_at else ""
            })
        
        _push_notify(
            db, user_ids=[r.submitter_id],
            type=NOTIFY_TYPE_REPORT_SYNCED,
            title=f"📚 您的实践报告《{r.title}》已同步入库【案例库】",
            content=r.review_remark,
            related_id=r.id,
        )
        return ok(_to_report_info(r), "已同步入库案例库，全车间可见")

    if action == "sync_guide":
        if r.status == "synced_guide":
            return fail("该报告已同步为作业指导，请勿重复操作", 400)
        # 把 solution 拆成若干步骤：按换行分；少于 2 段就兜底 1 步
        raw_steps = []
        parts = [p.strip() for p in (r.solution or "").split("\n") if p.strip()]
        if not parts:
            parts = ["按报告方案执行"]
        for i, p in enumerate(parts, 1):
            raw_steps.append({"step": i, "content": p, "tip": r.cause if i == 1 else ""})
        steps_json = json.dumps(raw_steps, ensure_ascii=False)
        # 难度：从报告的 level 字段映射（low=2, mid=3, high=4）
        difficulty_map = {"low": 2, "mid": 3, "high": 4}
        difficulty = difficulty_map.get((r.level or "mid").lower(), 3)
        applicable_devices = r.device or ""

        existing = db.query(Guide).filter(Guide.source_report_id == r.id).first()
        if existing:
            existing.title = r.title
            existing.device_type = r.tag or "机械"
            existing.tag = r.tag
            existing.steps_json = steps_json
            existing.risk_note = r.cause
            existing.duration_min = existing.duration_min or 30
            existing.difficulty = difficulty
            existing.applicable_devices = applicable_devices
            existing.contributor_name = r.submitter_name
        else:
            g = Guide(
                title=r.title, device_type=r.tag or "机械", tag=r.tag,
                steps_json=steps_json, risk_note=r.cause,
                duration_min=30, difficulty=difficulty,
                applicable_devices=applicable_devices,
                source_report_id=r.id,
                contributor_name=r.submitter_name, created_at=now,
            )
            db.add(g)
        r.status = "synced_guide"
        r.sync_time = now
        if not r.review_remark:
            r.review_remark = "管理员审核通过，已同步入库作业指导，感谢您的实践补充！"
        db.commit(); db.refresh(r)
        _push_notify(
            db, user_ids=[r.submitter_id],
            type=NOTIFY_TYPE_REPORT_SYNCED,
            title=f"📘 您的实践报告《{r.title}》已同步入库【作业指导库】",
            content=r.review_remark,
            related_id=r.id,
        )
        return ok(_to_report_info(r), "已同步入库作业指导库，全车间可见")

    return fail(f"未知审核操作：{action}，请使用 approve / reject / sync_case / sync_guide", 400)


# ============================================================
# B-3.5 AI 回答反馈与审核 API
# ============================================================
FEEDBACK_LABELS = {
    FEEDBACK_STATUS_PENDING: "待审核",
    FEEDBACK_STATUS_REVIEWED: "已查看",
    FEEDBACK_STATUS_INCORPORATED: "已采纳",
}


def _to_ai_feedback_info(fb: AIFeedback) -> dict:
    return {
        "id": fb.id,
        "feedback_id": fb.feedback_id,
        "user_name": fb.user_name,
        "question": fb.question,
        "answer": fb.answer,
        "rating": fb.rating,
        "correction_text": fb.correction_text,
        "llm_via": fb.llm_via,
        "fault_domain": fb.fault_domain,
        "device_model": fb.device_model,
        "status": fb.status,
        "status_label": FEEDBACK_LABELS.get(fb.status, fb.status),
        "admin_remark": fb.admin_remark,
        "created_at_ts": int(fb.created_at.timestamp()) if fb.created_at else None,
    }


@app.post("/api/ai/feedback", response_model=ApiResp)
def submit_ai_feedback(
    form: AIFeedbackSubmit,
    db: Session = Depends(get_db),
    current: Optional[User] = Depends(get_current_user_optional),
):
    """用户提交 AI 回答评分与修正。"""
    existing = db.query(AIFeedback).filter(AIFeedback.feedback_id == form.feedback_id).first()
    if existing:
        return ok(_to_ai_feedback_info(existing), "反馈已存在，跳过重复提交")
    fb = AIFeedback(
        feedback_id=form.feedback_id,
        user_name=current.fullname if current else "",
        question=form.question,
        answer=form.answer,
        rating=form.rating,
        correction_text=form.correction_text,
        llm_via=form.llm_via,
        fault_domain=form.fault_domain,
        device_model=form.device_model,
        status=FEEDBACK_STATUS_PENDING,
        created_at=_utcnow(),
    )
    db.add(fb)
    try:
        db.commit()
        db.refresh(fb)
        return ok(_to_ai_feedback_info(fb), "反馈提交成功")
    except Exception as e:
        db.rollback()
        return fail("反馈提交失败：" + str(e), 500)


@app.get("/api/ai/feedback", response_model=ApiResp)
def list_ai_feedback(
    page: int = 1,
    size: int = 20,
    status: Optional[str] = None,
    rating: Optional[str] = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """管理员获取 AI 反馈列表。"""
    require_admin(current)
    q = db.query(AIFeedback)
    if status:
        q = q.filter(AIFeedback.status == status)
    if rating:
        q = q.filter(AIFeedback.rating == rating)
    total = q.count()
    items = q.order_by(AIFeedback.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return ok(page_wrap(page, size, total, [_to_ai_feedback_info(fb) for fb in items]))


@app.get("/api/ai/feedback/stats", response_model=ApiResp)
def ai_feedback_stats(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """管理员获取 AI 反馈统计。"""
    require_admin(current)
    all_count = db.query(AIFeedback).count()
    pending = db.query(AIFeedback).filter(AIFeedback.status == FEEDBACK_STATUS_PENDING).count()
    reviewed = db.query(AIFeedback).filter(AIFeedback.status == FEEDBACK_STATUS_REVIEWED).count()
    incorporated = db.query(AIFeedback).filter(AIFeedback.status == FEEDBACK_STATUS_INCORPORATED).count()
    return ok({
        "total": all_count,
        "pending": pending,
        "reviewed": reviewed,
        "incorporated": incorporated,
    })


@app.put("/api/ai/feedback/{feedback_id}", response_model=ApiResp)
def review_ai_feedback(
    feedback_id: int,
    form: AIFeedbackReview,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """管理员审核 AI 反馈：标记为已查看(reviewed)或已采纳(incorporated)。"""
    require_admin(current)
    fb = db.query(AIFeedback).filter(AIFeedback.id == feedback_id).first()
    if not fb:
        return fail("反馈记录不存在", 404)
    if form.status not in (FEEDBACK_STATUS_REVIEWED, FEEDBACK_STATUS_INCORPORATED):
        return fail("状态值无效，请使用 reviewed 或 incorporated", 400)
    fb.status = form.status
    fb.admin_remark = form.remark or fb.admin_remark
    fb.review_time = _utcnow()
    db.commit()
    db.refresh(fb)
    label = FEEDBACK_LABELS.get(form.status, form.status)
    return ok(_to_ai_feedback_info(fb), f"已标记为「{label}」")


# ============================================================
# B-3.6 知识图谱 API
# ============================================================
@app.get("/api/knowledge/cases", response_model=ApiResp)
def list_knowledge_cases(
    current: User = Depends(get_current_user),
):
    from .services.knowledge_graph import get_cases
    cases = get_cases()
    return ok(cases)


@app.get("/api/knowledge/graph", response_model=ApiResp)
def get_knowledge_graph_api(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    tag: str = "all",
):
    from .services.knowledge_graph import get_knowledge_graph, build_graph_from_db
    graph = get_knowledge_graph(tag=tag)
    # 仅在请求"all"且图为空时触 lazily 构建
    if tag == "all" and not graph.get("nodes"):
        db_cases = db.query(Case).all()
        if db_cases:
            graph = build_graph_from_db(db_cases)
            # build_graph_from_db 返回完整分图结构，需要取出 all
            graph = graph.get("all", graph)
    return ok(graph)


@app.get("/api/knowledge/graph/stats", response_model=ApiResp)
def knowledge_graph_stats(
    current: User = Depends(get_current_user),
):
    """返回各 tag 子图的案例数（供前端 tab 上显示数字）"""
    from .services.knowledge_graph import get_all_graph_stats
    stats = get_all_graph_stats()
    return ok(stats)


@app.post("/api/knowledge/graph/rebuild", response_model=ApiResp)
def rebuild_knowledge_graph(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(current)
    from .services.knowledge_graph import build_graph_from_db
    db_cases = db.query(Case).all()
    graph = build_graph_from_db(db_cases)
    return ok(graph.get("all", graph), "知识图谱已重建（按分类重建完成）")


# ============================================================
# B-3.5 消息通知 API
# ============================================================
@app.get("/api/notifications", response_model=ApiResp)
def list_notifications(
    size: int = 20, unread_only: int = 0,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的消息通知（按最新时间倒序），同时返回未读总数"""
    q = db.query(Notification).filter(Notification.user_id == current.id)
    if unread_only:
        q = q.filter(Notification.is_read == 0)
    items_q = q.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(max(1, min(100, size)))
    items = [_to_notification_info(n) for n in items_q.all()]
    unread_count = db.query(Notification).filter(
        Notification.user_id == current.id, Notification.is_read == 0
    ).count()
    return ok({"items": items, "unread_count": unread_count})


@app.post("/api/notifications/read", response_model=ApiResp)
def mark_notifications_read(
    form: NotificationMarkReadReq,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """通知标为已读：ids 指定具体 ID；为空则当前用户全部标为已读"""
    q = db.query(Notification).filter(
        Notification.user_id == current.id, Notification.is_read == 0
    )
    if form.ids:
        q = q.filter(Notification.id.in_(list(form.ids)))
    updated = q.update({Notification.is_read: 1}, synchronize_session=False)
    db.commit()
    unread_count = db.query(Notification).filter(
        Notification.user_id == current.id, Notification.is_read == 0
    ).count()
    return ok({"read": updated, "unread_count": unread_count})


@app.delete("/api/notifications", response_model=ApiResp)
def delete_notifications(
    form: Optional[NotificationMarkReadReq] = Body(None),
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除通知：ids 指定具体 ID；为空则删除当前用户全部通知"""
    q = db.query(Notification).filter(Notification.user_id == current.id)
    if form and form.ids:
        q = q.filter(Notification.id.in_(list(form.ids)))
    deleted = q.delete(synchronize_session=False)
    db.commit()
    unread_count = db.query(Notification).filter(
        Notification.user_id == current.id, Notification.is_read == 0
    ).count()
    return ok({"deleted": deleted, "unread_count": unread_count})


# ============================================================
# B-4. 案例库 API
# ============================================================


def _get_attachments_from_report(db, report_id):
    if not report_id:
        return []
    atts = db.query(ReportAttachment).filter(
        ReportAttachment.report_id == report_id
    ).all()
    return [
        {
            "id": a.id,
            "filename": a.filename,
            "file_size": a.file_size,
            "mime_type": a.mime_type,
            "download_url": f"/api/reports/{report_id}/attachments/{a.id}",
            "uploaded_at_ts": _ts(a.uploaded_at),
        }
        for a in atts
    ]

@app.get("/api/cases", response_model=ApiResp[PageResp[CaseInfo]])
def list_cases(
    page: int = 1, size: int = 20, keyword: Optional[str] = None,
    tag: Optional[str] = None, level: Optional[str] = None,
    source: str = "all",   # all / official / employee / mine
    current: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    q = db.query(Case)
    if tag:
        q = q.filter(Case.tag == tag)
    if level:
        q = q.filter(Case.level == level)
    if source == "employee":
        q = q.filter(Case.submitter_role == "worker")
    elif source == "official":
        q = q.filter(Case.submitter_id.is_(None))
    elif source == "mine" and current:
        from sqlalchemy import or_ as _or2
        q = q.filter(_or2(
            Case.submitter_id == current.id,
            Case.contributor_name == current.fullname,
        ))
    if keyword:
        kw = f"%{keyword.strip()}%"
        from sqlalchemy import or_
        q = q.filter(or_(
            Case.title.ilike(kw), Case.device.ilike(kw),
            Case.fault.ilike(kw), Case.solution.ilike(kw),
            Case.summary.ilike(kw),
        ))
    total = q.count()
    rows = q.order_by(Case.created_at.desc()) \
        .offset((page - 1) * size).limit(size).all()
    items = [_to_case_info(c) for c in rows]
    return ok(page_wrap(page, size, total, items))


@app.get("/api/cases/tags", response_model=ApiResp)
def case_tags(current: Optional[User] = Depends(get_current_user_optional),
              db: Session = Depends(get_db)):
    rows = db.query(Case.tag).distinct().all()
    tags = [r[0] for r in rows if r[0]]
    return ok({"tags": tags})


@app.get("/api/cases/{case_id}", response_model=ApiResp[CaseInfo])
def get_case(case_id: int, current: Optional[User] = Depends(get_current_user_optional),
             db: Session = Depends(get_db)):
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c:
        return fail("案例不存在", 404)
    return ok(_to_case_info(c))


@app.get("/api/cases/{case_id}/attachments", response_model=ApiResp)
def get_case_attachments(
    case_id: int,
    current: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    c = db.query(Case).filter(Case.id == case_id).first()
    if not c:
        return fail("案例不存在", 404)
    attachments = _get_attachments_from_report(db, c.source_report_id)
    return ok({"items": attachments, "total": len(attachments)})



# ============================================================
# B-5. 作业指导 API
# ============================================================

@app.get("/api/guides", response_model=ApiResp[PageResp[GuideInfo]])
def list_guides(
    page: int = 1, size: int = 20, keyword: Optional[str] = None,
    device_type: Optional[str] = None,
    maintenance_level: Optional[str] = None,
    source: str = "all",
    current: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    q = db.query(Guide)
    if device_type:
        q = q.filter(Guide.device_type == device_type)
    if maintenance_level:
        q = q.filter(Guide.maintenance_level == maintenance_level)
    if source == "employee":
        from sqlalchemy import or_ as _or
        q = q.filter(_or(Guide.source_report_id.isnot(None), Guide.contributor_name.isnot(None)))
    elif source == "official":
        q = q.filter(Guide.source_report_id.is_(None), Guide.contributor_name.is_(None))
    if keyword:
        kw = f"%{keyword.strip()}%"
        from sqlalchemy import or_
        q = q.filter(or_(
            Guide.title.ilike(kw), Guide.device_type.ilike(kw),
            Guide.tag.ilike(kw), Guide.risk_note.ilike(kw),
        ))
    total = q.count()
    rows = q.order_by(Guide.created_at.desc()) \
        .offset((page - 1) * size).limit(size).all()
    items = [_to_guide_info(g) for g in rows]
    return ok(page_wrap(page, size, total, items))


@app.get("/api/guides/types", response_model=ApiResp)
def guide_types(current: Optional[User] = Depends(get_current_user_optional),
                db: Session = Depends(get_db)):
    rows = db.query(Guide.device_type).distinct().all()
    types = [r[0] for r in rows if r[0]]
    return ok({"types": types})


@app.get("/api/guides/{guide_id}", response_model=ApiResp[GuideInfo])
def get_guide(guide_id: int, current: Optional[User] = Depends(get_current_user_optional),
              db: Session = Depends(get_db)):
    g = db.query(Guide).filter(Guide.id == guide_id).first()
    if not g:
        return fail("作业指导不存在", 404)
    return ok(_to_guide_info(g))


@app.get("/api/guides/{guide_id}/attachments", response_model=ApiResp)
def get_guide_attachments(
    guide_id: int,
    current: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    g = db.query(Guide).filter(Guide.id == guide_id).first()
    if not g:
        return fail("作业指导不存在", 404)
    attachments = _get_attachments_from_report(db, g.source_report_id)
    return ok({"items": attachments, "total": len(attachments)})


@app.get("/api/guides/recommend", response_model=ApiResp)
def recommend_guides(
    device_type: str, level: Optional[str] = None,
    current: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    results = []
    if level:
        exact = db.query(Guide).filter(
            Guide.device_type == device_type,
            Guide.maintenance_level == level
        ).order_by(Guide.difficulty.asc().nullslast()).limit(5).all()
        results.extend(_to_guide_info(g) for g in exact)
        fallback = db.query(Guide).filter(
            Guide.device_type == device_type,
            Guide.maintenance_level.isnot(level)
        ).order_by(Guide.difficulty.asc().nullslast()).limit(5 - len(results)).all()
        results.extend(_to_guide_info(g) for g in fallback)
    else:
        all_type = db.query(Guide).filter(
            Guide.device_type == device_type
        ).order_by(Guide.difficulty.asc().nullslast()).limit(5).all()
        results.extend(_to_guide_info(g) for g in all_type)
    if len(results) < 3:
        generic = db.query(Guide).filter(
            Guide.device_type != device_type
        ).order_by(Guide.difficulty.asc().nullslast()).limit(3 - len(results)).all()
        results.extend(_to_guide_info(g) for g in generic)
    return ok({"recommended": results})


def _to_exec_info(e: GuideExecution, db: Session) -> GuideExecutionInfo:
    checklist_status = {}
    if e.checklist_status_json:
        try:
            checklist_status = json.loads(e.checklist_status_json)
        except Exception:
            pass
    steps_status = {}
    if e.steps_status_json:
        try:
            steps_status = json.loads(e.steps_status_json)
        except Exception:
            pass
    user_name = None
    guide_title = None
    u = db.query(User).filter(User.id == e.user_id).first()
    if u:
        user_name = u.fullname
    g = db.query(Guide).filter(Guide.id == e.guide_id).first()
    if g:
        guide_title = g.title
    return GuideExecutionInfo(
        id=e.id, ticket_id=e.ticket_id, guide_id=e.guide_id, user_id=e.user_id,
        user_name=user_name, guide_title=guide_title, status=e.status,
        checklist_status=checklist_status, steps_status=steps_status,
        started_at_ts=_ts(e.started_at),
        completed_at_ts=_ts(e.completed_at) if e.completed_at else None,
        review_remark=e.review_remark,
    )


@app.post("/api/guide-executions", response_model=ApiResp[GuideExecutionInfo])
def create_execution(
    req: GuideExecutionCreate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    guide = db.query(Guide).filter(Guide.id == req.guide_id).first()
    if not guide:
        return fail("作业指导不存在", 404)
    if req.ticket_id:
        ticket = db.query(Ticket).filter(Ticket.id == req.ticket_id).first()
        if not ticket:
            return fail("工单不存在", 404)
    existing_q = db.query(GuideExecution).filter(
        GuideExecution.guide_id == req.guide_id,
        GuideExecution.user_id == current.id,
        GuideExecution.status == EXEC_STATUS_IN_PROGRESS
    )
    if req.ticket_id:
        existing_q = existing_q.filter(GuideExecution.ticket_id == req.ticket_id)
    else:
        existing_q = existing_q.filter(GuideExecution.ticket_id.is_(None))
    existing = existing_q.first()
    if existing:
        return ok(_to_exec_info(existing, db))
    exe = GuideExecution(
        ticket_id=req.ticket_id,
        guide_id=req.guide_id,
        user_id=current.id,
        status=EXEC_STATUS_IN_PROGRESS,
    )
    db.add(exe)
    db.commit()
    db.refresh(exe)
    return ok(_to_exec_info(exe, db))


@app.put("/api/guide-executions/{exec_id}", response_model=ApiResp[GuideExecutionInfo])
def update_execution(
    exec_id: int, req: GuideExecutionUpdate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exe = db.query(GuideExecution).filter(GuideExecution.id == exec_id).first()
    if not exe:
        return fail("执行记录不存在", 404)
    if req.checklist_status_json is not None:
        exe.checklist_status_json = req.checklist_status_json
    if req.steps_status_json is not None:
        exe.steps_status_json = req.steps_status_json
    if req.status is not None:
        exe.status = req.status
        if req.status == EXEC_STATUS_COMPLETED:
            exe.completed_at = _utcnow()
    if req.review_remark is not None:
        exe.review_remark = req.review_remark
    if not exe.completed_at and exe.status == EXEC_STATUS_COMPLETED:
        exe.completed_at = _utcnow()
    db.commit()
    db.refresh(exe)
    return ok(_to_exec_info(exe, db))


@app.get("/api/guide-executions", response_model=ApiResp[list[GuideExecutionInfo]])
def list_executions(
    ticket_id: Optional[int] = None,
    user_id: Optional[int] = None,
    current: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    q = db.query(GuideExecution)
    if ticket_id:
        q = q.filter(GuideExecution.ticket_id == ticket_id)
    if user_id:
        q = q.filter(GuideExecution.user_id == user_id)
    rows = q.order_by(GuideExecution.started_at.desc()).all()
    items = [_to_exec_info(e, db) for e in rows]
    return ok(items)


# ============================================================
# B-6. 用户管理 API（仅管理员）
# ============================================================

@app.get("/api/users", response_model=ApiResp[PageResp[UserFullInfo]])
def list_users(
    page: int = 1, size: int = 50, keyword: Optional[str] = None,
    role: Optional[str] = None,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(current)
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    if keyword:
        kw = f"%{keyword.strip()}%"
        from sqlalchemy import or_
        q = q.filter(or_(
            User.username.ilike(kw), User.fullname.ilike(kw),
        ))
    total = q.count()
    rows = q.order_by(User.created_at.asc()) \
        .offset((page - 1) * size).limit(size).all()
    items = [_to_user_full(u, db) for u in rows]
    return ok(page_wrap(page, size, total, items))


@app.get("/api/users/options", response_model=ApiResp)
def user_options(
    role: Optional[str] = None,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(User).filter(~User.username.ilike("deleted_%"))
    if role == "worker":
        q = q.filter(User.role == ROLE_WORKER)
    elif role == "admin":
        from sqlalchemy import or_ as _or2
        q = q.filter(_or2(User.role == ROLE_MANAGER, User.role == ROLE_SYSADMIN))
    rows = q.order_by(User.fullname.asc()).all()
    options = [{"id": u.id, "username": u.username, "fullname": u.fullname,
                "role": u.role, "role_label": role_label_of(u.role)}
               for u in rows]
    return ok({"options": options})


@app.post("/api/user/password", response_model=ApiResp)
def change_my_password(
    form: UserPwdChange,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not form.old_password:
        return fail("请输入旧密码", 400)
    from .auth import verify_password
    if not verify_password(form.old_password, current.password_hash or ""):
        return fail("旧密码不正确", 401)
    current.password_hash = hash_password(form.new_password)
    db.add(current)
    db.commit()
    return ok(None, "密码修改成功，下次登录请使用新密码")


@app.get("/api/users/{user_id}", response_model=ApiResp[UserFullInfo])
def get_user(user_id: int, current: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    require_admin(current)
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        return fail("用户不存在", 404)
    return ok(_to_user_full(u, db))


@app.post("/api/users", response_model=ApiResp[UserFullInfo])
def create_user(form: UserCreate, current: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    require_admin(current)
    if db.query(User).filter(User.username == form.username.strip()).first():
        return fail("用户名已存在", 400)
    if form.role not in (ROLE_SYSADMIN, ROLE_MANAGER, ROLE_WORKER):
        return fail(f"角色必须是 {ROLE_SYSADMIN}/{ROLE_MANAGER}/{ROLE_WORKER} 之一", 400)
    u = User(
        username=form.username.strip(),
        password_hash=hash_password(form.password),
        fullname=form.fullname.strip(),
        role=form.role,
        avatar_preset=form.avatar_preset,
        created_at=_utcnow(),
    )
    db.add(u); db.commit(); db.refresh(u)
    return ok(_to_user_full(u, db), "用户创建成功")


@app.put("/api/users/{user_id}", response_model=ApiResp[UserFullInfo])
def update_user(user_id: int, form: UserUpdate,
                current: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    require_admin(current)
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        return fail("用户不存在", 404)
    if form.fullname is not None:
        u.fullname = form.fullname.strip()
    if form.role is not None:
        if form.role not in (ROLE_SYSADMIN, ROLE_MANAGER, ROLE_WORKER):
            return fail("角色不合法", 400)
        u.role = form.role
    if form.avatar_preset is not None:
        u.avatar_preset = form.avatar_preset
    # profile 扩展字段（admin 也能改）
    if form.emp_no is not None:
        u.emp_no = form.emp_no.strip() or None
    if form.dept is not None:
        u.dept = form.dept.strip() or None
    if form.position is not None:
        u.position = form.position.strip() or None
    if form.join_date is not None:
        u.join_date = form.join_date or None
    if form.mobile is not None:
        u.mobile = form.mobile.strip() or None
    if form.email is not None:
        u.email = form.email.strip().lower() or None
    if form.tel is not None:
        u.tel = form.tel.strip() or None
    if form.office is not None:
        u.office = form.office.strip() or None
    db.commit(); db.refresh(u)
    return ok(_to_user_full(u, db), "用户信息已更新")


@app.post("/api/users/{user_id}/reset_password", response_model=ApiResp)
def reset_user_password(user_id: int,
                        form: Optional[UserPwdChange] = None,
                        current: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    require_admin(current)
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        return fail("用户不存在", 404)
    new_pwd = (form.new_password if (form and form.new_password is not None) else None) or "123456"
    new_pwd = str(new_pwd).strip() or "123456"
    u.password_hash = hash_password(new_pwd)
    db.commit()
    return ok({"default_password": "123456"},
              f"密码重置成功（默认：123456）")


@app.delete("/api/users/{user_id}", response_model=ApiResp)
def delete_user(user_id: int, current: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    require_admin(current)
    if user_id == current.id:
        return fail("不能删除当前登录用户", 400)
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        return fail("用户不存在", 404)
    # 不要真删（工单/报告可能关联），把用户名改成 deleted_xxx，密码随机
    u.username = f"deleted_{u.id}_{u.username}"
    u.fullname = f"[已删除] {u.fullname}"
    u.password_hash = hash_password("__no_login__" + str(int(time.time())))
    db.commit()
    return ok(None, "用户已禁用（关联工单/报告保留）")


# ============================================================
# ============ ============ 阶段 B API 结束 ============ ============
# ============================================================


# ============================================================
# 前端 dist 托管（存在时；否则 FastAPI 只当 API 服务器）
# ============================================================
def _find_frontend_dist():
    backend_dir = Path(__file__).resolve().parent.parent  # backend/
    candidates = [
        backend_dir.parent / "frontend" / "dist",  # project/frontend/dist
        backend_dir / "frontend" / "dist",
        Path("frontend") / "dist",
        Path("..") / "frontend" / "dist",
    ]
    for c in candidates:
        if c.is_dir() and (c / "index.html").is_file():
            return str(c.resolve())
    return None


frontend_dist = _find_frontend_dist()
if frontend_dist:
    assets_dir = Path(frontend_dist) / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)),
                  name="frontend-assets")
    for static_name in ["favicon.svg", "icons.svg"]:
        fp = Path(frontend_dist) / static_name
        if fp.is_file():
            @app.get(f"/{static_name}", name=f"static-{static_name}")
            def _serve(fp=fp):
                return FileResponse(str(fp))
    _index_html = Path(frontend_dist) / "index.html"

    @app.get("/", response_class=HTMLResponse)
    def serve_index():
        return FileResponse(str(_index_html))

    @app.api_route("/{path_name:path}", methods=["GET"])
    async def spa_catch_all(request: Request, path_name: str):
        SPA_EXCLUDE_PREFIX = ["api", "health", "docs", "openapi.json",
                              "redoc", "assets", "favicon.svg", "icons.svg"]
        for p in SPA_EXCLUDE_PREFIX:
            if path_name.startswith(p):
                return JSONResponse(status_code=404,
                                    content={"detail": "Not Found", "path": path_name})
        return FileResponse(str(_index_html))
else:
    @app.get("/")
    def no_frontend_tip():
        return {
            "msg": "前端 dist 未找到，仅后端 API 可用（打开 /docs 看接口文档）",
            "tip": "在 frontend 目录执行 npm run build 生成 dist，或开发阶段用 npm run dev 单独跑前端，Vite 代理 /api 到 :8000",
            "api_docs": "/docs",
        }
