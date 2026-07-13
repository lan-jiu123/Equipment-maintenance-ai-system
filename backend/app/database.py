"""
数据库引擎与会话管理
- SQLite：开启 WAL 模式 + 关闭单线程限制，比赛级并发不崩
- 换盘符/换系统不炸：路径由 config.database_url 动态计算（相对 backend/）
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings


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
    """FastAPI Depends 依赖：每次请求自动获取/关闭会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
