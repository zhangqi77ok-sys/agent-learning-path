"""Per-tenant daily/monthly token budgets."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TenantBudget:
    tenant_id: str
    daily_limit: int
    monthly_limit: int
    daily_used: int = 0
    monthly_used: int = 0

    def remaining_daily(self) -> int:
        return max(0, self.daily_limit - self.daily_used)

    def remaining_monthly(self) -> int:
        return max(0, self.monthly_limit - self.monthly_used)

    def budget_left(self) -> int:
        return min(self.remaining_daily(), self.remaining_monthly())

    def charge(self, tokens: int) -> None:
        if tokens > self.budget_left():
            raise BudgetExhausted(self.tenant_id)
        self.daily_used += tokens
        self.monthly_used += tokens


class BudgetExhausted(Exception):
    def __init__(self, tenant_id: str):
        super().__init__(f"budget_exhausted:{tenant_id}")
        self.tenant_id = tenant_id


@dataclass
class BudgetLedger:
    tenants: dict[str, TenantBudget] = field(default_factory=dict)

    def get(self, tenant_id: str) -> TenantBudget:
        if tenant_id not in self.tenants:
            raise KeyError(tenant_id)
        return self.tenants[tenant_id]
