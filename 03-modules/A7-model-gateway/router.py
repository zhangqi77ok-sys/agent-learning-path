"""Route by (tenant, task_class, sensitivity, budget_left)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RouteKey:
    tenant: str
    task_class: str  # chat|rag|codegen
    sensitivity: str  # low|high
    budget_left: int


@dataclass
class RouteDecision:
    primary: str
    fallback: str
    reason: str


# pricing tiers: premium expensive, economy cheap
PREMIUM = "premium"
ECONOMY = "economy"
SAFE = "safe-small"  # for high sensitivity / low budget


def route(key: RouteKey) -> RouteDecision:
    if key.budget_left <= 0:
        return RouteDecision(primary=ECONOMY, fallback=ECONOMY, reason="budget_zero_force_economy")
    if key.sensitivity == "high":
        return RouteDecision(primary=SAFE, fallback=ECONOMY, reason="high_sensitivity")
    if key.task_class == "codegen" and key.budget_left > 2000:
        return RouteDecision(primary=PREMIUM, fallback=ECONOMY, reason="codegen_budget_ok")
    if key.budget_left < 500:
        return RouteDecision(primary=ECONOMY, fallback=ECONOMY, reason="low_budget")
    return RouteDecision(primary=PREMIUM, fallback=ECONOMY, reason="default")
