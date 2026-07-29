"""Agent 调度器：编排多 Agent 协同诊断流程，收集执行轨迹。"""

from __future__ import annotations

import threading
from typing import Any

from .base_agent import AgentResult
from .vision_agent import VisionAgent
from .retrieval_agent import RetrievalAgent
from .reasoning_agent import ReasoningAgent
from .safety_agent import SafetyAgent

_LOCK = threading.Lock()
_INSTANCE: "AgentOrchestrator | None" = None


class AgentOrchestrator:
    """多 Agent 协同调度器。

    四 Agent 流水线：视觉诊断 → 知识增强 → 故障推理 → 安全审核。
    每个 Agent 的结果统一封装为 AgentResult，含执行时间与状态。
    """

    def __init__(self):
        self.agents = {
            "vision": VisionAgent(),
            "retrieval": RetrievalAgent(),
            "reasoning": ReasoningAgent(),
            "safety": SafetyAgent(),
        }

    def run(
        self,
        image_bytes: bytes,
        mime_type: str,
        user_note: str = "",
        filename: str = "",
        document_id: str | None = None,
        device_model: str | None = None,
        device_type: str | None = None,
        top_k: int = 5,
    ) -> dict:
        """执行四 Agent 诊断流水线，返回轨迹数组和诊断结果。"""
        trajectory: list[dict] = []

        # ========== Step 1: 视觉诊断 Agent ==========
        vision_res = self.agents["vision"].run(
            image_bytes, mime_type, user_note, filename,
        )
        trajectory.append(vision_res.to_dict())

        if vision_res.status == "failed":
            return self._build_response(
                trajectory=trajectory,
                error=f"视觉诊断失败：{vision_res.error}",
            )

        vision_data = vision_res.result or {}
        analysis = vision_data.get("analysis", {})
        query = vision_data.get("query", "")
        fault_domain = vision_data.get("fault_domain", "") or device_type or ""

        # ========== Step 2: 知识增强 Agent ==========
        retrieval_question = query or "识别图片中的设备部件并检索相关检修资料"
        retrieval_res = self.agents["retrieval"].run(
            query=retrieval_question,
            fault_domain=fault_domain,
            top_k=top_k,
            document_id=document_id,
            device_model=device_model,
        )
        trajectory.append(retrieval_res.to_dict())

        retrieval_data = retrieval_res.result or {}
        pre_retrieved = retrieval_data.get("pre_retrieved")

        # ========== Step 3: 故障推理 Agent ==========
        reasoning_res = self.agents["reasoning"].run(
            question=retrieval_question,
            fault_domain=fault_domain,
            top_k=top_k,
            document_id=document_id,
            device_model=device_model,
            pre_retrieved=pre_retrieved,
        )
        trajectory.append(reasoning_res.to_dict())

        reasoning_data = reasoning_res.result or {}
        diagnosis_answer = reasoning_data.get("answer", "")
        citations = reasoning_data.get("citations", [])
        retrieval_diagnostics = (
            reasoning_data.get("retrieval_diagnostics")
            or retrieval_data.get("retrieval_diagnostics")
        )

        # ========== Step 4: 安全审核 Agent ==========
        safety_res = self.agents["safety"].run(
            diagnosis_answer=diagnosis_answer,
            question=user_note or retrieval_question,
            fault_domain=fault_domain,
        )
        trajectory.append(safety_res.to_dict())

        return self._build_response(
            trajectory=trajectory,
            vision_analysis=analysis,
            vision_via=vision_data.get("vision_via", ""),
            query=query,
            fault_domain=fault_domain,
            diagnosis_answer=diagnosis_answer,
            citations=citations,
            retrieval_diagnostics=retrieval_diagnostics,
            graph_used=retrieval_data.get("graph_used", False),
            llm_via=reasoning_data.get("llm_via", ""),
            safety_result=safety_res.result,
        )

    # -------- 内部方法 --------

    def _build_response(
        self,
        trajectory: list[dict],
        error: str | None = None,
        vision_analysis: dict | None = None,
        vision_via: str = "",
        query: str = "",
        fault_domain: str = "",
        diagnosis_answer: str = "",
        citations: list | None = None,
        retrieval_diagnostics: dict | None = None,
        graph_used: bool = False,
        llm_via: str = "",
        safety_result: dict | None = None,
    ) -> dict:
        citations = citations or []
        safety_result = safety_result or {}

        if error:
            return {
                "error": error,
                "agents_trajectory": trajectory,
                "vision_analysis": vision_analysis or {},
                "diagnosis": {
                    "answerable": False,
                    "answer": f"诊断过程出错：{error}",
                    "citations": [],
                },
                "safety_review": {},
            }

        return {
            "agents_trajectory": trajectory,
            "vision_analysis": vision_analysis or {},
            "retrieval_query": query,
            "diagnosis": {
                "answerable": True,
                "answer": diagnosis_answer,
                "citations": citations,
                "retrieval": retrieval_diagnostics or {},
                "llm_via": llm_via,
                "fault_domain": fault_domain,
                "graph_used": graph_used,
            },
            "safety_review": {
                "passed": safety_result.get("passed", True),
                "risk_level": safety_result.get("risk_level", "低"),
                "warnings": safety_result.get("warnings", []),
                "suggestions": safety_result.get("suggestions", ""),
            },
        }


def get_orchestrator() -> AgentOrchestrator:
    global _INSTANCE
    if _INSTANCE is None:
        with _LOCK:
            if _INSTANCE is None:
                _INSTANCE = AgentOrchestrator()
    return _INSTANCE
