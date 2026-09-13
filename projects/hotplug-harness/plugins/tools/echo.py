"""Echo tool plugin — drop-in under plugins/tools/."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EchoTool:
    name: str = "echo"

    def run(self, call: Any, state: Any) -> str:
        msg = call.args.get("message", "")
        return f"echo:{msg}"


def create_tool():
    return EchoTool()


PLUGIN = EchoTool()
