"""知识增强 Agent：混合检索 + 知识图谱 + 历史修正 + 相似案例匹配。
将检索过程包装为独立 Agent，使四 Agent 流水线（视觉→知识→推理→安全）完整可观测。"""

from __future__ import annotations

from .base_agent import BaseAgent
from ..retrieval_service import hybrid_search
from ..knowledge_graph import traverse_related, format_graph_context
from ...routers.rag import _load_recent_corrections


class RetrievalAgent(BaseAgent):
    name = "retrieval_agent"
    display_name = "知识增强Agent"
    icon = "📚"

    def _execute(
        self,
        query: str,
        fault_domain: str = "",
        top_k: int = 5,
        document_id: str | None = None,
        device_model: str | None = None,
    ) -> dict:
        # 1. 混合检索（BM25 + 向量 + RRF）
        search_result = hybrid_search(
            query,
            document_id=document_id,
            device_model=device_model,
            fault_domain=fault_domain,
            top_k=top_k,
        )
        evidence_items = search_result.get("items", [])
        diagnostics = search_result.get("diagnostics", {})

        # 2. 知识图谱增强
        graph_section = ""
        try:
            graph_results = traverse_related(
                query, tag=fault_domain or "all", max_depth=2, max_results=3
            )
            if graph_results:
                graph_section = format_graph_context(graph_results)
        except Exception:
            graph_section = ""

        # 3. 加载历史修正
        corrections = _load_recent_corrections(
            fault_domain=fault_domain or None, limit=5
        )

        # 4. 构建引用
        citations = []
        for idx, item in enumerate(evidence_items, start=1):
            page_label = (
                str(item["page_start"])
                if item["page_start"] == item["page_end"]
                else f"{item['page_start']}-{item['page_end']}"
            )
            citations.append({
                "id": f"S{idx}",
                "document_id": item["document_id"],
                "document_title": item["document_title"],
                "section_title": item["section_title"],
                "page_start": item["page_start"],
                "page_end": item["page_end"],
                "page_label": page_label,
                "excerpt": item["content"][:500],
                "file_url": f"/api/documents/{item['document_id']}/file#page={item['page_start']}",
                "retrieval_rank": item["rank"],
            })

        return {
            "pre_retrieved": search_result,
            "evidence_count": len(evidence_items),
            "citations": citations,
            "graph_used": bool(graph_section),
            "corrections_count": len(corrections),
            "retrieval_diagnostics": diagnostics,
        }

    def _format_summary(self, result: dict) -> str:
        parts = []
        ec = result.get("evidence_count", 0)
        if ec:
            parts.append(f"检索到 {ec} 条知识")
        if result.get("graph_used"):
            parts.append("图谱关联")
        cc = result.get("corrections_count", 0)
        if cc:
            parts.append(f"加载 {cc} 条历史修正")
        return "；".join(parts) if parts else "知识检索完成"
