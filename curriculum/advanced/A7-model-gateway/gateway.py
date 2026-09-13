"""Model gateway: route, budget, cache, fallback, circuit — decisions into Trace."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from budget import BudgetExhausted, BudgetLedger
from cache import TenantCache, cache_key
from circuit import CircuitBreaker
from models import FakeUpstream, ModelResponse, UpstreamError
from router import RouteKey, route


@dataclass
class TraceDecision:
    events: list[dict[str, Any]] = field(default_factory=list)

    def add(self, **kwargs: Any) -> None:
        self.events.append(kwargs)


class ModelGateway:
    def __init__(
        self,
        upstreams: dict[str, FakeUpstream],
        budgets: BudgetLedger,
        *,
        clock_ms: callable | None = None,
    ):
        self.upstreams = upstreams
        self.budgets = budgets
        self.cache = TenantCache()
        self.circuits = {name: CircuitBreaker() for name in upstreams}
        self._clock = clock_ms or (lambda: time.time() * 1000)
        self.expensive_calls_when_over_budget = 0  # SLO counter

    def complete(
        self,
        *,
        tenant_id: str,
        acl_version: str,
        task_class: str,
        sensitivity: str,
        prompt: str,
        allow_degrade: bool = True,
    ) -> tuple[ModelResponse, TraceDecision]:
        trace = TraceDecision()
        tb = self.budgets.get(tenant_id)
        left = tb.budget_left()
        rk = RouteKey(tenant_id, task_class, sensitivity, left)
        decision = route(rk)
        trace.add(event="route", **decision.__dict__, budget_left=left)

        # hard stop: no tokens left and degrade refused → explicit error
        if left <= 0 and not allow_degrade:
            trace.add(event="error", code="budget_exhausted")
            raise BudgetExhausted(tenant_id)

        # Never call premium when over budget
        candidates = [decision.primary, decision.fallback]
        if left <= 0:
            candidates = ["economy"]
            trace.add(event="force_economy", reason="budget_exhausted")

        ck = cache_key(
            tenant_id=tenant_id,
            acl_version=acl_version,
            task_class=task_class,
            prompt=prompt,
        )
        hit = self.cache.get(ck)
        if hit is not None:
            trace.add(event="cache_hit", key_prefix=ck[:8])
            return hit, trace

        start = self._clock()
        last_err: Exception | None = None
        for model_name in candidates:
            if model_name == "premium" and left <= 0:
                self.expensive_calls_when_over_budget += 1
                trace.add(event="blocked_premium_over_budget")
                continue
            cb = self.circuits[model_name]
            now = self._clock()
            if not cb.allow(now):
                trace.add(event="circuit_open", model=model_name)
                continue
            try:
                resp = self.upstreams[model_name].chat(prompt)
                # charge after success
                try:
                    tb.charge(resp.tokens)
                except BudgetExhausted:
                    # succeeded upstream but cannot charge — still record; do not retry premium
                    trace.add(event="charge_failed_budget")
                    if not allow_degrade:
                        raise
                cb.on_success()
                self.cache.put(ck, resp)
                elapsed = self._clock() - start
                trace.add(event="success", model=model_name, tokens=resp.tokens, elapsed_ms=elapsed)
                return resp, trace
            except UpstreamError as e:
                last_err = e
                cb.on_failure(self._clock())
                trace.add(event="upstream_error", model=model_name, code=e.code)
                if e.code not in ("429", "500", "502", "503"):
                    break
                continue

        elapsed = self._clock() - start
        trace.add(event="terminal_failure", elapsed_ms=elapsed)
        # SLO: reach clear terminal within 15s of 429 sequence
        raise UpstreamError("terminal", f"all_failed:{last_err}")
