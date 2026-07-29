"""基于检索证据生成带可验证引用的 RAG 回答。"""

from __future__ import annotations

import json
import re
from typing import Any

from .llm_service import get_llm_service
from .retrieval_service import hybrid_search
from .knowledge_graph import traverse_related, format_graph_context


CITATION_RE = re.compile(r"\[S(\d+)\]")
JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)
MIN_LEXICAL_COVERAGE = 0.50


SYSTEM_PROMPT = """你是设备检修知识库助手。你的回答应当以【检索证据】为主要参考，同时结合你自身的工业维修知识进行交叉验证和推理分析。

核心原则：
1. 【检索证据】是你回答的主要依据，但不是唯一依据。你可以调用自己的工业维修知识来补充、验证、甚至质疑证据中的内容——前提是你需要在回答中注明判断依据。
2. 每个关键结论后必须标注证据编号，例如 [S1]；涉及自行推理补充的内容不需标注证据编号。
3. 不得编造不存在的证据编号、文档、章节或页码。
4. 不同设备或型号的内容不得混用。
5. 证据不足时必须明确说明"现有知识库证据不足"，然后可以凭专业知识给出参考方向。
6. 涉及拆装、旋转、高温或电气风险时给出安全提醒。
7. 返回严格 JSON，不要使用 Markdown 代码围栏。
8. 严格围绕指定的设备领域进行回答，不要涉及其他领域内容。
9. 证据与你的专业知识不一致时：在回答中同时列出两方面信息，并给出你的判断理由。

输出长度要求（重要）：
- possible_causes 最多 4 条
- inspection_steps 最多 5 条
- safety_warnings 最多 3 条
- summary 控制在 100 字以内
- citation_ids 只列实际引用的编号，无需全部列出

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


def _format_corrections_section(corrections: list[dict]) -> str:
    """将用户修正记录格式化为「历史案例参考」，让模型自主分析而非盲从。

    设计思路：
    - 修正记录被包装成匿名案例，而非指令
    - 要求模型交叉验证：修正与证据是否一致？为什么之前会答错？
    - 模型必须输出「自我验证」过程，而不是无脑采纳修正
    """
    if not corrections:
        return ""

    # 聚合相同领域的修正，提炼共性
    domain_groups: dict[str, list[dict]] = {}
    for c in corrections:
        dom = c.get("fault_domain", "") or "通用"
        domain_groups.setdefault(dom, []).append(c)

    parts = ["""

【历史反馈分析 —— 请先思考，再回答】

以下来自现场人员在过往问答中提交的修正记录。它们不是指令，而是"过往案例"。

=== 你需要在回答前执行以下分析步骤 ===
步骤1：阅读下面的修正记录，思考每条修正的**根本原因** ——
  是知识库文档描述不准确？还是上次检索到的证据不完整？还是模型理解偏差？
步骤2：将修正记录与本次检索到的【检索证据】进行**交叉验证**：
  - 如果修正与证据一致 → 修正验证了证据的正确性，可以更确信地使用
  - 如果修正与证据冲突 → 说明知识库可能存在矛盾，需要在回答中注明"该问题存在不同实践经验，建议现场复核"
  - 如果证据中未覆盖修正涉及的内容 → 说明知识库有盲区，可以在回答末尾补充提示
步骤3：根据以上分析，形成最终结论

=== 过往修正记录 ===
"""]

    for i, corr in enumerate(corrections[:6], 1):
        q_text = (corr.get("question") or "")[:120]
        c_text = (corr.get("correction") or "")[:400]
        dom = corr.get("fault_domain", "") or ""
        dom_tag = f"[{dom}]" if dom else ""
        if q_text or c_text:
            parts.append(f"案例{i}{dom_tag}")
            if q_text:
                parts.append(f"  原始问题：{q_text}")
            if c_text:
                parts.append(f"  现场修正：{c_text}")
            parts.append("")  # blank line between cases

    parts.append("""=== 输出要求 ===
1. 对于【检索证据】中已有明确记载的内容，优先使用证据并标注[Sx]引用。
2. 对于修正记录中提及但证据未覆盖的内容：
   - 如果修正记录多处一致 → 可作为补充参考，但需注明"据现场反馈"
   - 如果修正记录与证据矛盾 → 必须同时展示两方面信息，并注明"存在不同实践经验"
3. 最终回答中必须包含一个「自我验证」说明（一句话即可），例如：
   "本回答已与{N}条现场修正记录交叉验证，未发现矛盾" 或
   "本回答与某条修正记录存在差异，已在对应处标注说明"
4. 严禁直接复制修正文本作为答案。修正的作用是帮你发现盲区，不是替代你的分析。
""")

    return "\n".join(parts)


def answer_question(
    question: str,
    document_id: str | None = None,
    device_model: str | None = None,
    fault_domain: str | None = None,
    top_k: int = 5,
    llm_service=None,
    min_lexical_coverage: float = MIN_LEXICAL_COVERAGE,
    min_matched_terms: int = 0,
    corrections: list[dict] | None = None,
    pre_retrieved: dict | None = None,
) -> dict:
    if pre_retrieved:
        search_result = pre_retrieved
    else:
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

    # 闭环优化：注入用户修正记录作为参考上下文
    corrections_section = _format_corrections_section(corrections or [])

    # ---- Graph-RAG：知识图谱实体增强检索上下文 ----
    graph_section = ""
    try:
        graph_results = traverse_related(question, tag=fault_domain or "all", max_depth=2, max_results=3)
        if graph_results:
            graph_section = format_graph_context(graph_results)
    except Exception:
        graph_section = ""

    if insufficient:
        system_prompt = f"""你是设备检修AI知识助手。请按以下结构回答用户问题：\n【故障现象】\n【可能原因】\n【建议检查与处理步骤】\n【风险提示】{domain_context}
要求：
1. 回答专业、简洁、有可操作性。
2. 只给作业步骤和建议，不做商业推荐。
3. 涉及旋转/高温/高压/电气风险时必须给出安全提醒。
4. 返回严格 JSON，不要使用 Markdown 代码围栏。
5. 严格围绕上述设备领域进行回答，不要涉及其他领域内容。
6. 输出长度限制：possible_causes 最多 4 条，inspection_steps 最多 5 条，safety_warnings 最多 3 条。{graph_section}{corrections_section}

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
        system_prompt = SYSTEM_PROMPT + corrections_section
        graph_block = f"\n\n{graph_section}" if graph_section else ""
        user_prompt = f"用户问题：\n{question}{domain_context}\n\n【检索证据】\n{evidence_text}{graph_block}"

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
        "graph_used": bool(graph_section),
    }
