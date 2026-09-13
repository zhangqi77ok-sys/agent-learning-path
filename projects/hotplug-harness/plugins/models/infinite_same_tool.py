"""Always proposes the same tool+args — trips circuit breaker."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _tool_call(name: str, args: dict):
    from hotplug_harness.contracts import ToolCall

    return ToolCall(name, args)


@dataclass
class InfiniteSameToolModel:
    name: str = "infinite_same_tool"
    tool_name: str = "echo"
    args: dict = field(default_factory=lambda: {"message": "loop"})

    def propose(self, state: Any):
        return None, [_tool_call(self.tool_name, dict(self.args))]


def create_model():
    return InfiniteSameToolModel()


PLUGIN = InfiniteSameToolModel()
