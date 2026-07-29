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
from ..services.agents import get_orchestrator
from ..services.llm_service import LLMConfigError, LLMQuotaError, LLMServiceError


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
    """三阶段检索。

    Stage 1 — 宽召回：关键词 + fault_domain 模糊匹配，不提前过滤
    Stage 2 — Rerank：加权综合评分
      - 关键词匹配度 40%
      - 设备类别匹配 25%（tag/device_type == fault_domain）
      - 部件匹配 20%（组件关键词命中）
      - 故障领域匹配 15%
    Stage 3 — 阈值输出：>=75% 高度匹配 / 50-75% 相关参考 / <50% 不显示
    """
    if not keywords:
        return []
    terms = [kw for kw in keywords if len(kw) >= 2]
    if fault_domain and fault_domain not in terms:
        terms.append(fault_domain)
    if not terms:
        return []

    from sqlalchemy import or_

    # ===== Stage 1: 宽召回 =====
    # 案例库 — 不按领域过滤，全量关键词模糊匹配
    case_conds = []
    for kw in terms:
        kw_filter = f"%{kw}%"
        case_conds.append(Case.title.ilike(kw_filter))
        case_conds.append(Case.fault.ilike(kw_filter))
        case_conds.append(Case.solution.ilike(kw_filter))
        case_conds.append(Case.cause.ilike(kw_filter))
    similar_cases = (
        db.query(Case)
        .filter(or_(*case_conds))
        .order_by(Case.created_at.desc())
        .limit(top_k * 3)  # 宽召回用更大的候选集
        .all()
    )

    # 作业指导库
    guide_terms = terms + ["检修", "维修", "保养"]
    guide_conds = []
    for kw in guide_terms:
        kw_filter = f"%{kw}%"
        guide_conds.append(Guide.title.ilike(kw_filter))
        guide_conds.append(Guide.scope.ilike(kw_filter))
    similar_guides = (
        db.query(Guide)
        .filter(or_(*guide_conds))
        .order_by(Guide.difficulty.asc().nullslast())
        .limit(top_k * 3)
        .all()
    )

    # ===== Stage 2: Rerank 加权评分 =====
    # 部件关键词列表
    COMPONENT_TERMS = {
        "轴承", "齿轮", "密封", "阀", "轴", "联轴器", "皮带", "链条",
        "传感器", "连接器", "端子", "线缆", "电机", "泵", "缸", "活塞",
        "管路", "过滤器", "散热器", "风扇", "开关", "继电器", "接触器",
    }

    def _rerank(
        text_fields: list[str],
        tag: str,
        item_fault_domain: str | None,
    ) -> float:
        """综合评分：keyword 40% + domain 25% + component 20% + fault 15%"""
        combined = " ".join(str(f) for f in text_fields if f).lower()

        # 关键词匹配度 (40%)
        kw_matched = sum(1 for t in terms if t.lower() in combined)
        kw_score = kw_matched / len(terms) if terms else 0

        # 设备类别匹配 (25%)
        domain_score = 1.0 if (fault_domain and tag and tag == fault_domain) else 0.0

        # 部件匹配 (20%) — 部件关键词在文本中出现比例
        comp_hits = sum(1 for ct in COMPONENT_TERMS if ct.lower() in combined)
        comp_score = min(1.0, comp_hits / 3)  # 出现3个部件词即满分

        # 故障领域匹配 (15%) — fault_domain 关键词出现
        fault_score = 1.0 if (fault_domain and fault_domain.lower() in combined) else 0.0

        return kw_score * 0.40 + domain_score * 0.25 + comp_score * 0.20 + fault_score * 0.15

    def _calc_relevance(text_fields: list[str], search_terms: list[str]) -> float:
        if not search_terms:
            return 0.0
        combined = " ".join(str(f) for f in text_fields if f).lower()
        matched = sum(1 for t in search_terms if t.lower() in combined)
        return matched / len(search_terms)

    results: list[dict] = []

    for c in similar_cases:
        text_fields = [c.title, c.fault, c.solution, c.cause, c.tag]
        score = _rerank(text_fields, c.tag or "", c.tag)
        relevance = _calc_relevance(text_fields, terms)
        results.append({
            "type": "case",
            "id": c.id,
            "title": c.title,
            "device": c.device,
            "fault": c.fault,
            "cause": c.cause,
            "solution": c.solution,
            "tag": c.tag,
            "relevance_score": round(score, 2),
            "keyword_match": round(relevance, 2),
        })

    for g in similar_guides:
        text_fields = [g.title, g.scope or "", g.device_type or ""]
        score = _rerank(text_fields, g.device_type or "", g.device_type)
        relevance = _calc_relevance(text_fields, guide_terms)
        results.append({
            "type": "guide",
            "id": g.id,
            "title": g.title,
            "device_type": g.device_type,
            "scope": g.scope,
            "difficulty": g.difficulty,
            "risk_note": g.risk_note,
            "relevance_score": round(score, 2),
            "keyword_match": round(relevance, 2),
        })

    # ===== Stage 3: 阈值输出 =====
    # 去重
    seen_titles: set[str] = set()
    deduped: list[dict] = []
    for r in results:
        t = str(r.get("title", ""))
        if t and t not in seen_titles:
            seen_titles.add(t)
            deduped.append(r)

    # 低于 50% 不展示
    deduped = [r for r in deduped if r.get("relevance_score", 0) >= 0.50]

    # 按评分降序
    deduped.sort(key=lambda r: r.get("relevance_score", 0), reverse=True)

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
        # ---- 多 Agent 协同诊断 ----
        orchestrator = get_orchestrator()
        agent_result = orchestrator.run(
            image_bytes=content,
            mime_type=mime_type,
            user_note=note,
            filename=file.filename or '',
            document_id=document_id,
            device_model=device_model,
            device_type=device_type,
            top_k=top_k,
        )

        vision_analysis = agent_result.get('vision_analysis', {})
        diagnosis = agent_result.get('diagnosis', {})
        query = agent_result.get('retrieval_query', '')
        fault_domain = vision_analysis.get('fault_domain', '') or device_type or ''

        # ---- 跨模态匹配：基于视觉关键词搜索相似案例 ----
        search_keywords = vision_analysis.get('search_keywords', [])
        suspected_faults = vision_analysis.get('suspected_faults', [])
        all_keywords = list(set(search_keywords + suspected_faults))
        similar_items = _find_similar_cases(all_keywords, fault_domain, db, top_k=4)

        # ---- 构建跨模态匹配提示 ----
        cross_modal_hints = []
        if similar_items:
            case_count = sum(1 for i in similar_items if i['type'] == 'case')
            guide_count = sum(1 for i in similar_items if i['type'] == 'guide')
            high_count = sum(1 for i in similar_items if i.get('relevance_score', 0) >= 0.75)
            mid_count = sum(1 for i in similar_items if 0.50 <= i.get('relevance_score', 0) < 0.75)
            hint_parts = []
            if case_count:
                hint_parts.append(f'{case_count} 条相似案例')
            if guide_count:
                hint_parts.append(f'{guide_count} 条作业指导')
            if high_count:
                hint_parts.append(f'{high_count} 条高度匹配')
            if mid_count and not high_count:
                hint_parts.append(f'{mid_count} 条相关参考')
            if hint_parts:
                cross_modal_hints.append(f'跨模态匹配到：{"、".join(hint_parts)}')
        else:
            cross_modal_hints.append('跨模态暂未命中高度匹配的案例或指导')

        return {
            'filename': file.filename,
            'vision_analysis': vision_analysis,
            'retrieval_query': query,
            'diagnosis': diagnosis,
            'similar_items': similar_items,
            'cross_modal_hints': cross_modal_hints,
            'agents_trajectory': agent_result.get('agents_trajectory', []),
            'safety_review': agent_result.get('safety_review', {}),
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
