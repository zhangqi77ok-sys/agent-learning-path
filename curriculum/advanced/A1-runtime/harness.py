"""Minimal Agent Harness control plane: Loop + Policy + Budget + Circuit + Replay."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Protocol


class RunStatus(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    CANCELLED = "cancelled"
    CIRCUIT_OPEN = "circuit_open"
    BUDGET_EXCEEDED = "budget_exceeded"
    FAILED = "failed"


@dataclass
class Budget:
    max_steps: int = 8
    max_wall_ms: int = 30_000
    max_tool_calls: int = 16


@dataclass
class PolicyDecision:
    allow: bool
    reason: str = ""


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any]
    signature: str = ""

    def __post_init__(self) -> None:
        if not self.signature:
            self.signature = f"{self.name}:{sorted(self.args.items())}"


@dataclass
class StepEvent:
    step: int
    kind: str  # model | tool | policy | circuit | budget
    detail: dict[str, Any] = field(default_factory=dict)
    ts_ms: float = field(default_factory=lambda: time.time() * 1000)


@dataclass
class RunState:
    run_id: str
    tenant_id: str
    user_id: str
    thread_id: str
    status: RunStatus = RunStatus.RUNNING
    step: int = 0
    tool_calls: int = 0
    started_ms: float = field(default_factory=lambda: time.time() * 1000)
    events: list[StepEvent] = field(default_factory=list)
    last_tool_signatures: list[str] = field(default_factory=list)
    cancel_requested: bool = False
    final: str = ""


class Executor(Protocol):
    def propose(self, state: RunState) -> tuple[str | None, list[ToolCall]]:
        """Return (final_text or None, tool_calls)."""


ToolHandler = Callable[[ToolCall], str]


@dataclass
class Harness:
    budget: Budget
    tools: dict[str, ToolHandler]
    executor: Executor
    allowlist: set[str] | None = None
    duplicate_signature_limit: int = 3

    def start_run(
        self,
        *,
        tenant_id: str,
        user_id: str,
        thread_id: str,
        run_id: str | None = None,
    ) -> RunState:
        return RunState(
            run_id=run_id or str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            thread_id=thread_id,
        )

    def cancel(self, state: RunState) -> None:
        state.cancel_requested = True
        state.events.append(StepEvent(state.step, "policy", {"cancel": True}))

    def _policy_tool(self, state: RunState, call: ToolCall) -> PolicyDecision:
        if self.allowlist is not None and call.name not in self.allowlist:
            return PolicyDecision(False, f"tool_not_allowlisted:{call.name}")
        # duplicate signature detection (loop smell)
        recent = state.last_tool_signatures[-(self.duplicate_signature_limit) :]
        if len(recent) >= self.duplicate_signature_limit and all(
            s == call.signature for s in recent
        ):
            return PolicyDecision(False, "duplicate_tool_signature_circuit")
        return PolicyDecision(True)

    def _budget_ok(self, state: RunState) -> PolicyDecision:
        if state.step >= self.budget.max_steps:
            return PolicyDecision(False, "max_steps")
        if (time.time() * 1000 - state.started_ms) >= self.budget.max_wall_ms:
            return PolicyDecision(False, "max_wall_ms")
        if state.tool_calls >= self.budget.max_tool_calls:
            return PolicyDecision(False, "max_tool_calls")
        return PolicyDecision(True)

    def step(self, state: RunState) -> RunState:
        if state.status != RunStatus.RUNNING:
            return state
        if state.cancel_requested:
            state.status = RunStatus.CANCELLED
            return state

        budget = self._budget_ok(state)
        if not budget.allow:
            state.status = RunStatus.BUDGET_EXCEEDED
            state.events.append(StepEvent(state.step, "budget", {"reason": budget.reason}))
            return state

        state.step += 1
        final, calls = self.executor.propose(state)
        state.events.append(
            StepEvent(
                state.step,
                "model",
                {"final": bool(final), "n_tools": len(calls)},
            )
        )

        if final and not calls:
            state.final = final
            state.status = RunStatus.SUCCEEDED
            return state

        for call in calls:
            decision = self._policy_tool(state, call)
            if not decision.allow:
                state.events.append(
                    StepEvent(state.step, "circuit" if "circuit" in decision.reason else "policy", {"reason": decision.reason, "tool": call.name})
                )
                if "circuit" in decision.reason:
                    state.status = RunStatus.CIRCUIT_OPEN
                else:
                    state.status = RunStatus.FAILED
                    state.final = f"blocked:{decision.reason}"
                return state

            # budget check before each tool
            budget = self._budget_ok(state)
            if not budget.allow:
                state.status = RunStatus.BUDGET_EXCEEDED
                state.events.append(StepEvent(state.step, "budget", {"reason": budget.reason}))
                return state

            handler = self.tools.get(call.name)
            if handler is None:
                state.status = RunStatus.FAILED
                state.final = f"unknown_tool:{call.name}"
                return state

            result = handler(call)
            state.tool_calls += 1
            state.last_tool_signatures.append(call.signature)
            state.events.append(
                StepEvent(state.step, "tool", {"name": call.name, "result": result[:80]})
            )

        return state

    def run_until_done(self, state: RunState, *, max_outer: int | None = None) -> RunState:
        outer = max_outer or (self.budget.max_steps + 2)
        for _ in range(outer):
            if state.status != RunStatus.RUNNING:
                break
            self.step(state)
        if state.status == RunStatus.RUNNING:
            state.status = RunStatus.BUDGET_EXCEEDED
            state.events.append(StepEvent(state.step, "budget", {"reason": "outer_guard"}))
        return state

    def replay(self, state: RunState) -> list[dict[str, Any]]:
        """Return a deterministic event log for Trace→Eval later."""
        return [
            {
                "run_id": state.run_id,
                "tenant_id": state.tenant_id,
                "step": e.step,
                "kind": e.kind,
                "detail": e.detail,
                "ts_ms": e.ts_ms,
            }
            for e in state.events
        ]
