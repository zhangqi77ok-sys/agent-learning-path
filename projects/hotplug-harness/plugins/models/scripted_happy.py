"""Scripted happy-path model: echo twice then finish. No API keys."""

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
        if self.remaining_echoes <= 0:
            return "done", []
        i = self.remaining_echoes
        self.remaining_echoes -= 1
        return None, [_tool_call("echo", {"message": f"hello-{i}"})]


def create_model():
    return ScriptedHappyModel()


PLUGIN = ScriptedHappyModel()
