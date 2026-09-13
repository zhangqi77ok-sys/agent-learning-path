"""Budget enforcement — owned by Harness, not the Model."""

from __future__ import annotations

import time
from dataclasses import dataclass

from .contracts import PolicyDecision, RunState


@dataclass
class Budget:
    max_steps: int = 8
    max_wall_ms: int = 30_000
    max_tool_calls: int = 16

    def check(self, state: RunState) -> PolicyDecision:
        if state.step >= self.max_steps:
            return PolicyDecision(False, "max_steps")
        if (time.time() * 1000 - state.started_ms) >= self.max_wall_ms:
            return PolicyDecision(False, "max_wall_ms")
        if state.tool_calls >= self.max_tool_calls:
            return PolicyDecision(False, "max_tool_calls")
        return PolicyDecision(True)
