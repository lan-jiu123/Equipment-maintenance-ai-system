"""视觉诊断 Agent：调用 qwen-vl 分析设备图片，提取设备信息与故障线索。"""

from __future__ import annotations

from .base_agent import BaseAgent
from ..vision_service import analyze_image, build_retrieval_query


class VisionAgent(BaseAgent):
    name = "vision_agent"
    display_name = "视觉诊断Agent"
    icon = "👁️"

    def _execute(self, image_bytes: bytes, mime_type: str,
                 user_note: str = "", filename: str = "") -> dict:
        analysis, vision_via = analyze_image(image_bytes, mime_type,
                                             user_note, filename)
        query = build_retrieval_query(analysis, user_note)
        fault_domain = analysis.get("fault_domain", "") or ""
        return {
            "analysis": analysis,
            "query": query,
            "fault_domain": fault_domain,
            "vision_via": vision_via,
        }

    def _format_summary(self, result: dict) -> str:
        a = result.get("analysis", {})
        parts = []
        eq = a.get("equipment", "") or ""
        comp = a.get("component", "") or ""
        faults = a.get("suspected_faults", []) or []
        if eq:
            parts.append(f"识别设备：{eq}")
        if comp:
            parts.append(f"检测部件：{comp}")
        if faults:
            parts.append(f"疑似故障：{'、'.join(faults[:2])}")
        return "；".join(parts) if parts else "视觉分析完成"
