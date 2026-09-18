"""Minimal harness: budget + circuit on repeated tool signature."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Harness:
    max_steps: int = 8
    max_tool_calls: int = 6
    steps: int = 0
    tool_calls: int = 0
    recent_sigs: list[str] = field(default_factory=list)
    status: str = "running"
    events: list[dict[str, Any]] = field(default_factory=list)

    def allow_tool(self, name: str, args: dict) -> bool:
        if self.status != "running":
            return False
        if self.steps >= self.max_steps or self.tool_calls >= self.max_tool_calls:
            self.status = "budget_exhausted"
            self.events.append({"event": "budget_exhausted"})
            return False
        sig = f"{name}:{sorted(args.items())}"
        self.recent_sigs.append(sig)
        if len(self.recent_sigs) >= 3 and len(set(self.recent_sigs[-3:])) == 1:
            self.status = "circuit_open"
            self.events.append({"event": "circuit_open", "sig": sig})
            return False
        self.tool_calls += 1
        return True

    def tick(self) -> None:
        self.steps += 1
        if self.steps >= self.max_steps and self.status == "running":
            self.status = "budget_exhausted"
            self.events.append({"event": "budget_exhausted"})
