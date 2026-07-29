"""安全审核 Agent：独立审查维修方案的安全性，确保包含必要的防护措施。
使用 qwen3.6-flash 轻量模型，不影响主链路并发。"""

from __future__ import annotations

import json
import re

from .base_agent import BaseAgent
from ..llm_service import get_llm_service

JSON_RE = re.compile(r"\{.*\}", re.DOTALL)

SAFETY_SYSTEM_PROMPT = """你是工业设备维修安全审核专家。
请逐一检查维修方案中的安全隐患，并给出审核结论。"""

# 专用安全审核模型：qwen3.6-flash 轻量高速，不影响主推理模型并发
SAFETY_MODEL = "qwen3.6-flash"


def _parse_json(text: str) -> dict | None:
    match = JSON_RE.search(text or "")
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


class SafetyAgent(BaseAgent):
    name = "safety_agent"
    display_name = "安全审核Agent"
    icon = "🛡️"

    def _execute(self, diagnosis_answer: str, question: str = "",
                 fault_domain: str = "") -> dict:
        user_prompt = f"""请审核以下设备维修方案是否存在安全隐患。

设备领域：{fault_domain or '未指定'}
用户问题：{question or '未提供'}

维修方案：
{diagnosis_answer or '无'}

请逐项检查：
1. 方案是否涉及高压电、高温、旋转机械、化学危险、密闭空间等风险
2. 方案中是否包含必要的安全防护措施（断电、挂牌、验电、泄压、通风等）
3. 操作步骤顺序是否安全（如先断电再拆解）
4. 是否存在可能危及人身安全或设备安全的遗漏

返回严格 JSON，不要使用 Markdown 代码围栏：
{{
  "passed": true,
  "risk_level": "低/中/高",
  "warnings": ["具体安全提醒1", "具体安全提醒2"],
  "suggestions": "如果未通过，给出修改建议；如通过则为空字符串"
}}"""

        service = get_llm_service()
        # 使用独立模型配置，不影响其他 Agent
        raw, llm_via = service.chat(SAFETY_SYSTEM_PROMPT, user_prompt, model=SAFETY_MODEL)

        parsed = _parse_json(raw)
        if parsed:
            return {
                "passed": bool(parsed.get("passed", True)),
                "risk_level": str(parsed.get("risk_level", "低")),
                "warnings": parsed.get("warnings", []),
                "suggestions": parsed.get("suggestions", "") or "",
                "llm_via": llm_via,
            }
        # 解析失败时默认通过
        return {
            "passed": True,
            "risk_level": "低",
            "warnings": [],
            "suggestions": "",
            "llm_via": llm_via,
        }

    def _format_summary(self, result: dict) -> str:
        risk = result.get("risk_level", "低")
        warnings = result.get("warnings", []) or []
        if warnings:
            return f"风险等级：{risk}，检测到 {len(warnings)} 项安全补充建议"
        return f"安全审核完成，风险等级：{risk}"
