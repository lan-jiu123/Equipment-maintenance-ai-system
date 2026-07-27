"""基于检索证据生成带可验证引用的 RAG 回答。"""

from __future__ import annotations

import json
import re
from typing import Any

from .llm_service import get_llm_service
from .retrieval_service import hybrid_search


CITATION_RE = re.compile(r"\[S(\d+)\]")
JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)
MIN_LEXICAL_COVERAGE = 0.50


SYSTEM_PROMPT = """你是设备检修知识库助手。你只能依据用户消息中的【检索证据】回答。

严格规则：
1. 不得使用证据之外的型号、参数、步骤和结论。
2. 每个关键结论后必须标注证据编号，例如 [S1]。
3. 不得编造不存在的证据编号、文档、章节或页码。
4. 不同设备或型号的内容不得混用。
5. 证据不足时必须明确说明"现有知识库证据不足"。
6. 涉及拆装、旋转、高温或电气风险时给出安全提醒。
7. 返回严格 JSON，不要使用 Markdown 代码围栏。
8. 严格围绕指定的设备领域进行回答，不要涉及其他领域内容。
9. 如果检索证据中的某些术语与指定领域不一致，忽略这些术语，不要据此扩展回答。

JSON 格式：
{
  "summary": "简明结论，包含[Sx]引用",
  "possible_causes": ["原因及[Sx]引用"],
  "inspection_steps": ["步骤及[Sx]引用"],
  "safety_warnings": ["提醒及[Sx]引用"],
  "citation_ids": ["S1"]
}
"""


def _citation_from_result(item: dict, evidence_id: str) -> dict:
    page_label = (
        str(item["page_start"])
        if item["page_start"] == item["page_end"]
        else f"{item['page_start']}-{item['page_end']}"
    )
    return {
        "id": evidence_id,
        "document_id": item["document_id"],
        "document_title": item["document_title"],
        "section_title": item["section_title"],
        "page_start": item["page_start"],
        "page_end": item["page_end"],
        "page_label": page_label,
        "excerpt": item["content"][:500],
        "file_url": f"/api/documents/{item['document_id']}/file#page={item['page_start']}",
        "retrieval_rank": item["rank"],
    }


def _insufficient(
    search_result: dict,
    min_lexical_coverage: float = MIN_LEXICAL_COVERAGE,
    min_matched_terms: int = 0,
) -> tuple[bool, str | None]:
    if not search_result["items"]:
        return True, "知识库中没有可用的检修资料"
    diagnostics = search_result.get("diagnostics") or {}
    if diagnostics.get("missing_codes"):
        return True, "问题中的型号或故障码未在知识库证据中出现"
    if diagnostics.get("matched_term_count", 0) < min_matched_terms:
        return True, "检索证据命中的关键术语数量不足"
    if diagnostics.get("lexical_coverage", 0.0) < min_lexical_coverage:
        return True, "检索证据与问题的关键术语匹配度不足"
    return False, None


def _parse_model_json(raw: str) -> dict[str, Any] | None:
    match = JSON_BLOCK_RE.search(raw or "")
    if not match:
        return None
    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None


def _render_structured_answer(payload: dict[str, Any]) -> str:
    sections: list[str] = []
    summary = str(payload.get("summary") or "").strip()
    if summary:
        sections.append(f"【诊断结论】\n{summary}")
    for title, key in (
        ("可能原因", "possible_causes"),
        ("检查与处理步骤", "inspection_steps"),
        ("安全提醒", "safety_warnings"),
    ):
        values = payload.get(key) or []
        if isinstance(values, str):
            values = [values]
        cleaned = [str(value).strip() for value in values if str(value).strip()]
        if cleaned:
            sections.append(
                f"【{title}】\n" + "\n".join(
                    f"{index}. {value}" for index, value in enumerate(cleaned, start=1)
                )
            )
    return "\n\n".join(sections) or "现有知识库证据不足。"


def answer_question(
    question: str,
    document_id: str | None = None,
    device_model: str | None = None,
    fault_domain: str | None = None,
    top_k: int = 5,
    llm_service=None,
    min_lexical_coverage: float = MIN_LEXICAL_COVERAGE,
    min_matched_terms: int = 0,
) -> dict:
    search_result = hybrid_search(
        question,
        document_id=document_id,
        device_model=device_model,
        fault_domain=fault_domain,
        top_k=top_k,
    )
    insufficient, _ = _insufficient(
        search_result, min_lexical_coverage, min_matched_terms
    )

    evidence_items = search_result["items"]
    citations = [
        _citation_from_result(item, f"S{index}")
        for index, item in enumerate(evidence_items, start=1)
    ]
    evidence_text = "\n\n".join(
        f"[{citation['id']}] 文档：《{citation['document_title']}》；"
        f"章节：{citation['section_title'] or '未识别'}；PDF页码：{citation['page_label']}\n"
        f"{citation['excerpt']}"
        for citation in citations
    )

    domain_context = ""
    if fault_domain:
        domain_forbidden = {
            "电气": ["轴承", "齿轮", "润滑", "联轴器", "皮带", "链条", "减速机"],
            "机械": ["集成电路", "传感器", "PLC", "接触器", "继电器", "变压器"],
            "液压": ["轴承", "齿轮", "电机绕组", "电刷"],
            "仪表": ["轴承", "齿轮", "润滑", "联轴器"],
            "安全": ["轴承", "齿轮", "润滑"],
        }
        forbidden = domain_forbidden.get(fault_domain, [])
        domain_context = f"\n\n【设备领域】{fault_domain}类设备\n"
        if forbidden:
            domain_context += f"【禁止涉及】{'、'.join(forbidden)}等非{fault_domain}领域内容\n"
        domain_context += f"【回答要求】所有结论、原因和步骤必须围绕{fault_domain}领域的设备展开\n"

    if insufficient:
        system_prompt = f"""你是设备检修AI知识助手。请按以下结构回答用户问题：\n【故障现象】\n【可能原因】\n【建议检查与处理步骤】\n【风险提示】{domain_context}
要求：
1. 回答专业、简洁、有可操作性。
2. 只给作业步骤和建议，不做商业推荐。
3. 涉及旋转/高温/高压/电气风险时必须给出安全提醒。
4. 返回严格 JSON，不要使用 Markdown 代码围栏。
5. 严格围绕上述设备领域进行回答，不要涉及其他领域内容。

JSON 格式：
{{
  "summary": "简明结论",
  "possible_causes": ["原因1", "原因2"],
  "inspection_steps": ["步骤1", "步骤2"],
  "safety_warnings": ["提醒1"],
  "citation_ids": []
}}
"""
        user_prompt = f"用户问题：\n{question}"
        llm_via = "rag-knowledge-insufficient+llm-reference"
    else:
        system_prompt = SYSTEM_PROMPT
        user_prompt = f"用户问题：\n{question}{domain_context}\n\n【检索证据】\n{evidence_text}"

    service = llm_service or get_llm_service()
    raw_answer, llm_via_or_fallback = service.chat(system_prompt, user_prompt)
    if not insufficient:
        llm_via = llm_via_or_fallback
    payload = _parse_model_json(raw_answer)
    answer = _render_structured_answer(payload) if payload else raw_answer.strip()
    payload = _parse_model_json(raw_answer)
    answer = _render_structured_answer(payload) if payload else raw_answer.strip()

    valid_ids = {citation["id"] for citation in citations}
    referenced = {
        f"S{number}" for number in CITATION_RE.findall(answer) if f"S{number}" in valid_ids
    }
    if payload and isinstance(payload.get("citation_ids"), list):
        referenced.update(
            str(value) for value in payload["citation_ids"] if str(value) in valid_ids
        )
    selected = [citation for citation in citations if citation["id"] in referenced]
    if not insufficient and not selected:
        selected = citations[:1]
    for citation in selected:
        citation["used_in_answer"] = citation["id"] in referenced

    return {
        "answerable": True,
        "answer": answer,
        "citations": selected,
        "retrieval": search_result["diagnostics"],
        "llm_via": llm_via,
        "fault_domain": fault_domain or "",
    }
