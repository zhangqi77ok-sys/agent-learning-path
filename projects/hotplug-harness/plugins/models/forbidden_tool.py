"""Proposes a tool not on the allowlist — policy should block."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _tool_call(name: str, args: dict):
    from hotplug_harness.contracts import ToolCall

    return ToolCall(name, args)


@dataclass
class ForbiddenToolModel:
    name: str = "forbidden_tool"

    def propose(self, state: Any):
        return None, [_tool_call("drop_db", {"all": True})]


def create_model():
    return ForbiddenToolModel()


PLUGIN = ForbiddenToolModel()
