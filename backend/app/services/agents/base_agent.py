"""Agent 基类与结果模型。"""

from __future__ import annotations

import time
from typing import Any


class AgentResult:
    """单个 Agent 的执行结果，包含轨迹信息供前端展示。"""

    def __init__(
        self,
        name: str,
        display_name: str,
        icon: str,
        status: str = "pending",
        summary: str = "",
        result: Any = None,
        error: str | None = None,
        duration_ms: int = 0,
    ):
        self.name = name              # 英文标识: vision / retrieval / reasoning / safety
        self.display_name = display_name  # 中文展示名: 视觉诊断Agent / 知识增强Agent / ...
        self.icon = icon              # 图标: 👁️ / 📚 / 🧠 / 🛡️
        self.status = status          # completed / failed
        self.summary = summary        # 一句话摘要
        self.result = result          # 结构化结果
        self.error = error
        self.duration_ms = duration_ms

    def to_dict(self) -> dict:
        """标准化轨迹格式，供前端统一展示。"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "icon": self.icon,
            "status": "success" if self.status == "completed" else "failed",
            "summary": self.summary,
            "duration": round(self.duration_ms / 1000, 2),
            "error": self.error,
        }


class BaseAgent:
    """所有 Agent 的基类。

    子类只需实现 _execute() 和 _format_summary()。
    run() 方法自动处理计时、异常捕获和结果封装。
    """

    name: str = ""
    display_name: str = ""
    icon: str = ""

    def run(self, *args, **kwargs) -> AgentResult:
        start = time.time()
        try:
            result = self._execute(*args, **kwargs)
            elapsed = int((time.time() - start) * 1000)
            return AgentResult(
                name=self.name,
                display_name=self.display_name,
                icon=self.icon,
                status="completed",
                summary=self._format_summary(result),
                result=result,
                duration_ms=elapsed,
            )
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            return AgentResult(
                name=self.name,
                display_name=self.display_name,
                icon=self.icon,
                status="failed",
                error=str(e),
                duration_ms=elapsed,
            )

    def _execute(self, *args, **kwargs) -> Any:
        raise NotImplementedError

    def _format_summary(self, result: Any) -> str:
        return ""
