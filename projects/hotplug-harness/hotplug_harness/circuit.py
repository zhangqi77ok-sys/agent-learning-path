"""Circuit breaker: duplicate tool signatures open the circuit."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import PolicyDecision, RunState, ToolCall


@dataclass
class CircuitBreaker:
    """Sliding window: if the last N signatures are identical, trip open."""

    duplicate_signature_limit: int = 3

    def check(self, state: RunState, call: ToolCall) -> PolicyDecision:
        limit = self.duplicate_signature_limit
        recent = state.last_tool_signatures[-limit:]
        if len(recent) >= limit and all(s == call.signature for s in recent):
            return PolicyDecision(False, "duplicate_tool_signature_circuit")
        return PolicyDecision(True)

    def record(self, state: RunState, call: ToolCall) -> None:
        state.last_tool_signatures.append(call.signature)
