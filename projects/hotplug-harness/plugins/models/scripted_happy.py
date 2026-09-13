"""Scripted happy-path model: echo then finish. No API keys.

CLI demo: echo twice then "done".
Chat Q&A: when state.user_message is set, echo the question once then
return a reply that includes the user's question.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _tool_call(name: str, args: dict):
    from hotplug_harness.contracts import ToolCall

    return ToolCall(name, args)


@dataclass
class ScriptedHappyModel:
    name: str = "scripted_happy"
    remaining_echoes: int = 2

    def propose(self, state: Any):
        msg = (getattr(state, "user_message", None) or "").strip()
        if msg:
            # Q&A mode: one echo tool call, then a reply that quotes the question.
            if not getattr(state, "last_tool_results", None):
                snippet = msg[:120]
                return None, [_tool_call("echo", {"message": snippet})]
            echoed = state.last_tool_results[-1]
            return (
                f"关于「{msg}」：我已通过 Harness 调用 echo 工具。"
                f"工具返回：{echoed}。"
                f"这是脚本模型的教学回复（无真实 LLM Key）。",
                [],
            )

        # Legacy CLI / demo path (no user_message).
        if self.remaining_echoes <= 0:
            return "done", []
        i = self.remaining_echoes
        self.remaining_echoes -= 1
        return None, [_tool_call("echo", {"message": f"hello-{i}"})]


def create_model():
    return ScriptedHappyModel()


PLUGIN = ScriptedHappyModel()
