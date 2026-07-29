"""故障推理 Agent：综合检索证据与知识图谱，生成结构化维修方案。"""

from __future__ import annotations

from .base_agent import BaseAgent
from ..rag_service import answer_question


class ReasoningAgent(BaseAgent):
    name = "reasoning_agent"
    display_name = "故障推理Agent"
    icon = "🧠"

    def _execute(
        self,
        question: str,
        fault_domain: str = "",
        top_k: int = 5,
        document_id: str | None = None,
        device_model: str | None = None,
        pre_retrieved: dict | None = None,
    ) -> dict:
        rag = answer_question(
            question=question,
            document_id=document_id,
            device_model=device_model,
            fault_domain=fault_domain,
            top_k=top_k,
            min_lexical_coverage=0.30,
            min_matched_terms=2,
            pre_retrieved=pre_retrieved,
        )
        return {
            "answer": rag.get("answer", ""),
            "answerable": rag.get("answerable", True),
            "citations": rag.get("citations", []),
            "llm_via": rag.get("llm_via", ""),
            "retrieval_diagnostics": rag.get("retrieval", {}),
            "graph_used": rag.get("graph_used", False),
        }

    def _format_summary(self, result: dict) -> str:
        ans = result.get("answer", "") or ""
        citations = result.get("citations", []) or []
        # 取 answer 的前 50 字作为摘要
        plain = ans.replace("\n", " ").strip()
        summary = plain[:50] + ("…" if len(plain) > 50 else "") if plain else "已生成维修方案"
        cite_info = f"（引用 {len(citations)} 条证据）" if citations else ""
        return f"{summary}{cite_info}"
