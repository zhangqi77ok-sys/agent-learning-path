"""Infinite tools with unique signatures each step — hits budget, not circuit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _tool_call(name: str, args: dict):
    from hotplug_harness.contracts import ToolCall

    return ToolCall(name, args)


@dataclass
class UniqueInfiniteModel:
    name: str = "unique_infinite"

    def propose(self, state: Any):
        return None, [_tool_call("echo", {"message": f"n-{state.step}"})]


def create_model():
    return UniqueInfiniteModel()


PLUGIN = UniqueInfiniteModel()
