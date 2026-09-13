"""Allowlist policy plugin — only named tools may run."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AllowlistPolicy:
    name: str = "allowlist"
    allowed: set[str] = field(default_factory=lambda: {"echo", "flaky"})

    def check(self, state: Any, call: Any):
        from hotplug_harness.contracts import PolicyDecision

        if call.name not in self.allowed:
            return PolicyDecision(False, f"tool_not_allowlisted:{call.name}")
        return PolicyDecision(True)


def create_policy():
    return AllowlistPolicy()


PLUGIN = AllowlistPolicy()
