"""Flaky / retryable tool — fails first N calls then succeeds."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FlakyTool:
    name: str = "flaky"
    fail_times: int = 2
    _attempts: dict[str, int] = field(default_factory=dict)

    def run(self, call: Any, state: Any) -> str:
        key = call.signature
        n = self._attempts.get(key, 0) + 1
        self._attempts[key] = n
        if n <= self.fail_times:
            return f"flaky:fail:{n}"
        return f"flaky:ok:{n}"


def create_tool():
    return FlakyTool()


PLUGIN = FlakyTool()
