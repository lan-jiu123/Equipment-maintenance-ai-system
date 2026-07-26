"""
数据库引擎与会话管理
- SQLite：开启 WAL 模式 + 关闭单线程限制，比赛级并发不崩
- 换盘符/换系统不炸：路径由 config.database_url 动态计算（相对 backend/）
- ★ 方案 A（单库合并）：你业务表 + 队友 RAG 文档表全部存在同一个 SQLite 文件里
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings


# ====== 路径符号（队友 routers/services 强依赖，名字一字不能改）======
# 项目根目录（Equipment-maintenance-ai-system/ 级别）
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

# 数据目录：优先读环境变量 DATA_DIR，其次走 settings.data_dir_path（config.py 里定义）
if os.getenv("DATA_DIR"):
    DATA_DIR: Path = Path(os.getenv("DATA_DIR")).expanduser().resolve()
else:
    DATA_DIR = settings.data_dir_path

# ★ 核心：数据库路径 - 优先读环境变量 DATABASE_PATH，
#   否则解析 settings.database_url（sqlite:///C:/xxx/backend/equipai.db）的真实绝对路径
#   → 这样你 SQLAlchemy 的 engine 和队友原生 sqlite3 的 _connect() 连的是同一个文件！
if os.getenv("DATABASE_PATH"):
    DATABASE_PATH: Path = Path(os.getenv("DATABASE_PATH")).expanduser().resolve()
else:
    # 从 settings.database_url 里解析出真实文件绝对路径（去掉 sqlite:/// 前缀）
    _db_url: str = settings.database_url
    if _db_url.startswith("sqlite:///"):
        DATABASE_PATH = Path(_db_url[len("sqlite:///"):]).resolve()
    else:
        DATABASE_PATH = (settings.data_dir_path / "equipment_maintenance.db").resolve()

# 文档上传目录：优先读环境变量 DOCUMENT_UPLOAD_DIR，其次走 settings.upload_dir_path
if os.getenv("DOCUMENT_UPLOAD_DIR"):
    UPLOAD_DIR: Path = Path(os.getenv("DOCUMENT_UPLOAD_DIR")).expanduser().resolve()
else:
    UPLOAD_DIR = settings.upload_dir_path

# 启动时确保目录存在（避免首次运行文件写入报错）
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False, "timeout": 30},
    pool_pre_ping=True,
    future=True,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    """SQLite 连接即设置 WAL 模式 + 外键约束"""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.execute("PRAGMA busy_timeout=30000;")
    except Exception:
        pass
    finally:
        cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db():
    """FastAPI Depends 依赖：每次请求自动获取/关闭会话（你原有业务代码专用）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# 以下代码原样嫁接队友的原生 sqlite3 连接管理（RAG 文档表专用）
# 队友 routers/services 强依赖这 4 个函数，函数名/参数/返回值一字不能改
# ============================================================

def _connect() -> sqlite3.Connection:
    """队友原生 sqlite3 连接：连 DATABASE_PATH（默认和你 SQLAlchemy 同文件，方案 A）"""
    connection = sqlite3.connect(str(DATABASE_PATH), timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 30000")
    return connection


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """队友代码使用：with get_connection() as conn: conn.execute(...)"""
    connection = _connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_database() -> None:
    """队友 RAG 初始化：建 documents/document_pages/document_chunks/chunk_embeddings 4 张表 + 相关索引"""
    # 目录保障（再次 mkdir，兼容队友代码单独 import 场景）
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL UNIQUE,
                file_type TEXT NOT NULL DEFAULT 'pdf',
                mime_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL CHECK (size_bytes > 0),
                sha256 TEXT NOT NULL UNIQUE,
                page_count INTEGER,
                device_type TEXT,
                device_model TEXT,
                document_category TEXT,
                maintenance_level TEXT,
                status TEXT NOT NULL DEFAULT 'uploaded'
                    CHECK (status IN ('uploaded', 'parsing', 'indexing', 'ready', 'failed')),
                parse_error TEXT,
                uploaded_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_documents_status
                ON documents(status);
            CREATE INDEX IF NOT EXISTS idx_documents_device_model
                ON documents(device_model);
            CREATE INDEX IF NOT EXISTS idx_documents_created_at
                ON documents(created_at DESC);

            CREATE TABLE IF NOT EXISTS document_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                page_number INTEGER NOT NULL CHECK (page_number > 0),
                content TEXT NOT NULL,
                char_count INTEGER NOT NULL DEFAULT 0,
                is_toc INTEGER NOT NULL DEFAULT 0 CHECK (is_toc IN (0, 1)),
                created_at TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                UNIQUE (document_id, page_number)
            );

            CREATE INDEX IF NOT EXISTS idx_document_pages_document
                ON document_pages(document_id, page_number);

            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL CHECK (chunk_index >= 0),
                content TEXT NOT NULL,
                section_title TEXT,
                page_start INTEGER NOT NULL CHECK (page_start > 0),
                page_end INTEGER NOT NULL CHECK (page_end >= page_start),
                char_count INTEGER NOT NULL DEFAULT 0,
                device_type TEXT,
                device_model TEXT,
                component TEXT,
                safety_tags TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                UNIQUE (document_id, chunk_index)
            );

            CREATE INDEX IF NOT EXISTS idx_document_chunks_document
                ON document_chunks(document_id, chunk_index);
            CREATE INDEX IF NOT EXISTS idx_document_chunks_pages
                ON document_chunks(document_id, page_start, page_end);
            CREATE INDEX IF NOT EXISTS idx_document_chunks_section
                ON document_chunks(section_title);

            CREATE TABLE IF NOT EXISTS chunk_embeddings (
                chunk_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                embedding_model TEXT NOT NULL,
                dimension INTEGER NOT NULL CHECK (dimension > 0),
                vector BLOB NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (chunk_id, embedding_model),
                FOREIGN KEY (chunk_id) REFERENCES document_chunks(id) ON DELETE CASCADE,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_document
                ON chunk_embeddings(document_id, embedding_model);
            """
        )


def database_health() -> dict:
    """队友健康检查端点使用：返回 RAG 文档库连接状态+路径"""
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1").fetchone()
        return {"ok": True, "path": str(DATABASE_PATH)}
    except Exception as exc:
        return {"ok": False, "error": type(exc).__name__}
