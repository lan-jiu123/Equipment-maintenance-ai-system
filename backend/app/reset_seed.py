"""
清库重植脚本 -- demo/测试用
用法：python -m backend.app.reset_seed
生产环境禁用：会清空全部表数据。
"""
from __future__ import annotations
from .database import SessionLocal
from sqlalchemy import text as sa_text


def reset_and_seed() -> None:
    db = SessionLocal()
    try:
        # 临时关 FK 约束，避免删除顺序问题
        db.execute(sa_text("PRAGMA foreign_keys=OFF"))
        for tbl in ("notifications", "knowledge_reports", "tickets", "reviews",
                    "cases", "guides", "devices", "users"):
            try:
                db.execute(sa_text(f"DELETE FROM {tbl}"))
            except Exception:
                pass
        db.execute(sa_text("PRAGMA foreign_keys=ON"))
        db.commit()
        print("[reset_seed] tables cleared")

        # 同步补列（使 SQLAlchemy 的 model 与实际表一致）
        from .main import _ensure_profile_columns
        from .database import engine
        _ensure_profile_columns(engine)

        from .seed import seed_if_empty
        seed_if_empty(db)
        print("seed 重植完成")
    finally:
        db.close()


if __name__ == "__main__":
    reset_and_seed()
