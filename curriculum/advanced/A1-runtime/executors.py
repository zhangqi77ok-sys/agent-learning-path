"""Pluggable executors for A1 Harness demos (no LLM required for fault injection)."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness import RunState, ToolCall


@dataclass
class InfiniteToolExecutor:
    """Always proposes the same tool — should trip circuit / budget."""

    tool_name: str = "noop"
    args: dict = field(default_factory=dict)

    def propose(self, state: RunState):
        return None, [ToolCall(self.tool_name, dict(self.args))]


@dataclass
class FiniteTaskExecutor:
    """Calls tools N times then finishes."""

    remaining: int = 2
    tool_name: str = "noop"

    def propose(self, state: RunState):
        if self.remaining <= 0:
            return "done", []
        self.remaining -= 1
        return None, [ToolCall(self.tool_name, {"i": self.remaining})]


@dataclass
class ForbiddenToolExecutor:
    def propose(self, state: RunState):
        return None, [ToolCall("drop_db", {"all": True})]
