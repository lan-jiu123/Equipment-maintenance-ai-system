"""故障图片上传、视觉识别与 RAG 联合诊断接口。
增强版：VLM 深度分析 + 相似历史案例匹配 + 跨模态关联推荐。"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Case, Guide
from ..services.llm_service import LLMConfigError, LLMQuotaError, LLMServiceError
from ..services.rag_service import answer_question
from ..services.vision_service import analyze_image, build_retrieval_query


router = APIRouter(prefix="/api/images", tags=["多模态图片诊断"])
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAGIC_BYTES = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/webp": (b"RIFF",),
}


def _validate_magic(content: bytes, mime_type: str) -> bool:
    if mime_type == "image/webp":
        return content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    return any(content.startswith(prefix) for prefix in MAGIC_BYTES[mime_type])


def _find_similar_cases(
    keywords: list[str],
    fault_domain: str,
    db,
    top_k: int = 4,
) -> list[dict]:
    """基于 VLM 提取的关键词和故障领域，匹配相似历史案例和作业指导。

    实现跨模态关联：VLM 视觉输出 → 文本语义检索 → 案例库匹配。
    """
    if not keywords:
        return []
    # 构造搜索关键词集
    terms = [kw for kw in keywords if len(kw) >= 2]
    if fault_domain and fault_domain not in terms:
        terms.append(fault_domain)

    results: list[dict] = []

    # 1. 搜索案例库
    if terms:
        from sqlalchemy import or_
        conds = []
        for kw in terms:
            kw_filter = f"%{kw}%"
            conds.append(Case.title.ilike(kw_filter))
            conds.append(Case.fault.ilike(kw_filter))
            conds.append(Case.solution.ilike(kw_filter))
            conds.append(Case.cause.ilike(kw_filter))
        similar_cases = (
            db.query(Case)
            .filter(or_(*conds))
            .order_by(Case.created_at.desc())
            .limit(top_k)
            .all()
        )
        for c in similar_cases:
            results.append({
                "type": "case",
                "id": c.id,
                "title": c.title,
                "device": c.device,
                "fault": c.fault,
                "cause": c.cause,
                "solution": c.solution,
                "tag": c.tag,
            })

    # 2. 搜索作业指导库
    guide_terms = terms + ["检修", "维修", "保养"]
    if fault_domain:
        from sqlalchemy import or_
        conds = [Guide.device_type == fault_domain]
        for kw in guide_terms:
            kw_filter = f"%{kw}%"
            conds.append(Guide.title.ilike(kw_filter))
            conds.append(Guide.scope.ilike(kw_filter))
        similar_guides = (
            db.query(Guide)
            .filter(or_(*conds))
            .order_by(Guide.difficulty.asc().nullslast())
            .limit(top_k)
            .all()
        )
        for g in similar_guides:
            results.append({
                "type": "guide",
                "id": g.id,
                "title": g.title,
                "device_type": g.device_type,
                "scope": g.scope,
                "difficulty": g.difficulty,
                "risk_note": g.risk_note,
            })

    # 去重 & 截断
    seen_titles: set[str] = set()
    deduped: list[dict] = []
    for r in results:
        t = str(r.get("title", ""))
        if t and t not in seen_titles:
            seen_titles.add(t)
            deduped.append(r)
    return deduped[:top_k * 2]


@router.post("/diagnose", response_model=None)
async def diagnose_image(
    file: UploadFile = File(...),
    note: str = Form(default="", max_length=500),
    document_id: str | None = Form(default=None),
    device_model: str | None = Form(default=None),
    device_type: str | None = Form(default=None),
    top_k: int = Form(default=5, ge=1, le=10),
    db: Session = Depends(get_db),
):
    mime_type = (file.content_type or "").lower()
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail="仅支持 JPG、PNG 或 WebP 图片")
    limit = int(settings.MAX_IMAGE_UPLOAD_MB or 10) * 1024 * 1024
    content = await file.read(limit + 1)
    await file.close()
    if not content:
        raise HTTPException(status_code=400, detail="上传图片为空")
    if len(content) > limit:
        raise HTTPException(status_code=413, detail=f"图片不能超过 {settings.MAX_IMAGE_UPLOAD_MB} MB")
    if not _validate_magic(content, mime_type):
        raise HTTPException(status_code=415, detail="文件内容与图片格式不符")

    try:
        analysis, vision_via = analyze_image(content, mime_type, note, filename=file.filename or "")
        query = build_retrieval_query(analysis, note)
        fault_domain = analysis.get("fault_domain", "") or device_type or ""

        # ---- VLM 深度诊断：RAG 检索知识库 ----
        rag = answer_question(
            question=query or "识别图片中的设备部件并检索相关检修资料",
            document_id=document_id,
            device_model=device_model,
            fault_domain=fault_domain,
            top_k=top_k,
            min_lexical_coverage=0.30,
            min_matched_terms=2,
        )

        # ---- 跨模态匹配：基于视觉关键词搜索相似案例 ----
        search_keywords = analysis.get("search_keywords", [])
        suspected_faults = analysis.get("suspected_faults", [])
        all_keywords = list(set(search_keywords + suspected_faults))
        similar_items = _find_similar_cases(all_keywords, fault_domain, db, top_k=4)

        # ---- 构建跨模态关联：如果找到了相似案例，总结关联性 ----
        cross_modal_hints = []
        if similar_items:
            case_count = sum(1 for i in similar_items if i["type"] == "case")
            guide_count = sum(1 for i in similar_items if i["type"] == "guide")
            cross_modal_hints.append(
                f"基于视觉特征跨模态匹配到 {case_count} 个相似历史案例、{guide_count} 个相关作业指导"
            )

        return {
            "filename": file.filename,
            "vision_analysis": analysis,
            "retrieval_query": query,
            "diagnosis": rag,
            "similar_items": similar_items,
            "cross_modal_hints": cross_modal_hints,
            "vision_via": vision_via,
        }
    except LLMQuotaError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc
    except LLMConfigError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LLMServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="图片诊断服务暂时不可用，请检查模型配置和网络") from exc
