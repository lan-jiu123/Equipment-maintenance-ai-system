"""启动时将项目内置知识文档幂等导入 SQLite 并建立检索索引。"""

from __future__ import annotations

import hashlib
import logging
import mimetypes
import os
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader

from ..database import PROJECT_ROOT, UPLOAD_DIR, get_connection, init_database
from .document_parser import parse_document
from .retrieval_service import index_document


LOGGER = logging.getLogger(__name__)
SUPPORTED_SUFFIXES = {".pdf", ".md", ".markdown", ".txt"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _enabled() -> bool:
    return os.getenv("AUTO_IMPORT_KNOWLEDGE", "true").strip().lower() in {
        "1", "true", "yes", "on",
    }


def _knowledge_dir() -> Path:
    value = os.getenv("BUILTIN_KNOWLEDGE_DIR", "").strip()
    return Path(value).expanduser().resolve() if value else PROJECT_ROOT / "knowledge"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _page_count(path: Path) -> int:
    if path.suffix.lower() != ".pdf":
        return 1
    reader = PdfReader(str(path), strict=False)
    if reader.is_encrypted:
        raise ValueError("暂不支持加密 PDF")
    return len(reader.pages)


def _metadata(path: Path) -> dict[str, str]:
    name = path.stem
    if "轴承" in name:
        return {"device_type": "滚动轴承", "document_category": "故障案例"}
    return {"device_type": "", "document_category": "内置知识"}


def _existing_by_sha(sha256: str) -> sqlite3.Row | None:
    with get_connection() as connection:
        return connection.execute(
            "SELECT id, status, original_filename FROM documents WHERE sha256 = ?",
            (sha256,),
        ).fetchone()


def _create_document(source: Path, sha256: str) -> str:
    document_id = uuid.uuid4().hex
    suffix = source.suffix.lower()
    stored_filename = f"{document_id}{suffix}"
    destination = UPLOAD_DIR / stored_filename
    metadata = _metadata(source)
    mime_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
    now = _now_iso()
    shutil.copy2(source, destination)
    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    id, title, original_filename, stored_filename, file_type,
                    mime_type, size_bytes, sha256, page_count, device_type,
                    device_model, document_category, maintenance_level, status,
                    uploaded_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, NULL,
                          'uploaded', 'builtin-bootstrap', ?, ?)
                """,
                (
                    document_id, source.stem, source.name, stored_filename,
                    suffix.lstrip("."), mime_type, source.stat().st_size, sha256,
                    _page_count(source), metadata["device_type"] or None,
                    metadata["document_category"], now, now,
                ),
            )
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return document_id


def _prepare_document(document_id: str) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT stored_filename, status FROM documents WHERE id = ?",
            (document_id,),
        ).fetchone()
    if row is None:
        raise ValueError("文档记录不存在")
    if row["status"] == "ready":
        return {"document_id": document_id, "status": "skipped_ready"}
    path = UPLOAD_DIR / row["stored_filename"]
    if not path.is_file():
        raise FileNotFoundError(f"内置文档副本不存在：{path.name}")
    parse_document(document_id, path)
    result = index_document(document_id)
    return {"document_id": document_id, "status": result["status"]}


def bootstrap_builtin_knowledge() -> dict:
    """幂等导入 knowledge 目录；单个文件失败不会阻止 API 启动。"""
    summary = {"enabled": _enabled(), "directory": str(_knowledge_dir()),
               "imported": 0, "ready": 0, "skipped": 0, "failed": []}
    if not summary["enabled"]:
        return summary
    directory = _knowledge_dir()
    if not directory.is_dir():
        LOGGER.info("内置知识目录不存在，跳过自动导入：%s", directory)
        return summary

    init_database()
    files = sorted(
        path for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )
    for source in files:
        try:
            digest = _sha256(source)
            existing = _existing_by_sha(digest)
            if existing and existing["status"] == "ready":
                summary["skipped"] += 1
                continue
            if existing:
                document_id = existing["id"]
            else:
                try:
                    document_id = _create_document(source, digest)
                    summary["imported"] += 1
                except sqlite3.IntegrityError:
                    # 多 worker 同时启动时，由成功插入的一方负责后续处理。
                    existing = _existing_by_sha(digest)
                    if not existing:
                        raise
                    document_id = existing["id"]
            result = _prepare_document(document_id)
            if result["status"] == "ready":
                summary["ready"] += 1
            else:
                summary["skipped"] += 1
        except Exception as exc:
            LOGGER.exception("自动导入内置知识失败：%s", source.name)
            summary["failed"].append({"file": source.name, "error": str(exc)[:300]})
    LOGGER.info("内置知识自动导入完成：%s", summary)
    return summary
