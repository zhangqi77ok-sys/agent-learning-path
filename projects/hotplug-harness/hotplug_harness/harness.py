"""Hot-pluggable Agent Harness control plane.

Harness owns the loop. Model only proposes the next step.
Budget, allowlist policy, circuit breaker, cancel, and event log are enforced here.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Sequence

from .budget import Budget
from .circuit import CircuitBreaker
from .contracts import (
    IsolationKeys,
    ModelPlugin,
    PolicyPlugin,
    RunState,
    RunStatus,
    StepEvent,
    ToolCall,
)
from .registry import PluginRegistry


@dataclass
class Harness:
    registry: PluginRegistry
    model: ModelPlugin
    budget: Budget = field(default_factory=Budget)
    circuit: CircuitBreaker = field(default_factory=CircuitBreaker)
    policy_names: Sequence[str] = field(default_factory=lambda: ("allowlist",))

    def start_run(
        self,
        *,
        tenant_id: str,
        user_id: str,
        thread_id: str,
        run_id: str | None = None,
        user_message: str = "",
    ) -> RunState:
        keys = IsolationKeys(
            tenant_id=tenant_id,
            user_id=user_id,
            thread_id=thread_id,
            run_id=run_id or str(uuid.uuid4()),
        )
        return RunState(isolation=keys, user_message=user_message or "")

    def cancel(self, state: RunState) -> None:
        state.cancel_requested = True
        state.events.append(StepEvent(state.step, "cancel", {"cancel": True}))

    def _policies(self) -> list[PolicyPlugin]:
        out: list[PolicyPlugin] = []
        for name in self.policy_names:
            p = self.registry.get_policy(name)
            if p is not None:
                out.append(p)
        return out

    def step(self, state: RunState) -> RunState:
        if state.status != RunStatus.RUNNING:
            return state
        if state.cancel_requested:
            state.status = RunStatus.CANCELLED
            return state

        budget_ok = self.budget.check(state)
        if not budget_ok.allow:
            state.status = RunStatus.BUDGET_EXCEEDED
            state.events.append(StepEvent(state.step, "budget", {"reason": budget_ok.reason}))
            return state

        state.step += 1
        final, calls = self.model.propose(state)
        state.events.append(
            StepEvent(
                state.step,
                "model",
                {"model": self.model.name, "final": bool(final), "n_tools": len(calls)},
            )
        )

        if final and not calls:
            state.final = final
            state.status = RunStatus.SUCCEEDED
            return state

        for call in calls:
            for policy in self._policies():
                decision = policy.check(state, call)
                if not decision.allow:
                    state.events.append(
                        StepEvent(
                            state.step,
                            "policy",
                            {"reason": decision.reason, "tool": call.name, "policy": policy.name},
                        )
                    )
                    state.status = RunStatus.POLICY_BLOCKED
                    state.final = f"blocked:{decision.reason}"
                    return state

            circuit_ok = self.circuit.check(state, call)
            if not circuit_ok.allow:
                state.events.append(
                    StepEvent(
                        state.step,
                        "circuit",
                        {"reason": circuit_ok.reason, "tool": call.name},
                    )
                )
                state.status = RunStatus.CIRCUIT_OPEN
                return state

            budget_ok = self.budget.check(state)
            if not budget_ok.allow:
                state.status = RunStatus.BUDGET_EXCEEDED
                state.events.append(StepEvent(state.step, "budget", {"reason": budget_ok.reason}))
                return state

            tool = self.registry.get_tool(call.name)
            if tool is None:
                state.status = RunStatus.FAILED
                state.final = f"unknown_tool:{call.name}"
                state.events.append(
                    StepEvent(state.step, "policy", {"reason": state.final, "tool": call.name})
                )
                return state

            result = tool.run(call, state)
            state.tool_calls += 1
            self.circuit.record(state, call)
            state.last_tool_results.append(result)
            state.events.append(
                StepEvent(state.step, "tool", {"name": call.name, "result": result[:120]})
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
        return [
            {
                "run_id": state.run_id,
                "tenant_id": state.tenant_id,
                "user_id": state.user_id,
                "thread_id": state.thread_id,
                "step": e.step,
                "kind": e.kind,
                "detail": e.detail,
                "ts_ms": e.ts_ms,
            }
            for e in state.events
        ]
