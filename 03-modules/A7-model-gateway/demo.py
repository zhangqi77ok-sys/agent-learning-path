"""A7 fault injection: 429 sequence, cross-tenant cache, budget vs premium."""

from __future__ import annotations

from budget import BudgetLedger, TenantBudget, BudgetExhausted
from gateway import ModelGateway
from models import FakeUpstream, UpstreamError


def main() -> None:
    premium = FakeUpstream("premium", cost_per_1k=10.0)
    economy = FakeUpstream("economy", cost_per_1k=1.0)
    safe = FakeUpstream("safe-small", cost_per_1k=0.5)
    budgets = BudgetLedger(
        tenants={
            "tenantA": TenantBudget("tenantA", daily_limit=5000, monthly_limit=20000),
            "tenantB": TenantBudget("tenantB", daily_limit=5000, monthly_limit=20000),
            "tenantPoor": TenantBudget("tenantPoor", daily_limit=100, monthly_limit=100, daily_used=100, monthly_used=100),
        }
    )
    # controllable clock for circuit / SLO
    clock = {"t": 0.0}

    def now():
        return clock["t"]

    gw = ModelGateway(
        {"premium": premium, "economy": economy, "safe-small": safe},
        budgets,
        clock_ms=now,
    )

    print("=== demo1: happy route premium ===")
    resp, tr = gw.complete(
        tenant_id="tenantA",
        acl_version="acl-1",
        task_class="chat",
        sensitivity="low",
        prompt="hello policy",
    )
    print(resp.model, resp.tokens, [e["event"] for e in tr.events])
    assert resp.model == "premium"

    print("=== demo2: 429 on premium → fallback economy, terminal <15s ===")
    premium.fail_with = ["429", "429"]
    clock["t"] = 0.0
    # after failures circuit may open; economy should succeed
    resp2, tr2 = gw.complete(
        tenant_id="tenantA",
        acl_version="acl-1",
        task_class="chat",
        sensitivity="low",
        prompt="need fallback path unique",
    )
    clock["t"] = 10_000  # within 15s
    elapsed = [e for e in tr2.events if e["event"] == "success"][0]["elapsed_ms"]
    print("model:", resp2.model, "events:", tr2.events, "elapsed_ms:", elapsed)
    assert resp2.model == "economy"
    assert elapsed <= 15_000
    print("SLO_ok_429_terminal_lt_15s:", True)

    print("=== demo3: cross-tenant same query must NOT share cache ===")
    # seed tenantA cache
    gw.complete(
        tenant_id="tenantA",
        acl_version="acl-1",
        task_class="chat",
        sensitivity="low",
        prompt="same-query-secret",
    )
    # tenantB same prompt — must miss cache (different tenant in key)
    before_b = economy.calls + premium.calls + safe.calls
    resp_b, tr_b = gw.complete(
        tenant_id="tenantB",
        acl_version="acl-1",
        task_class="chat",
        sensitivity="low",
        prompt="same-query-secret",
    )
    assert not any(e["event"] == "cache_hit" for e in tr_b.events)
    # same tenant + same acl hits
    resp_a2, tr_a2 = gw.complete(
        tenant_id="tenantA",
        acl_version="acl-1",
        task_class="chat",
        sensitivity="low",
        prompt="same-query-secret",
    )
    assert any(e["event"] == "cache_hit" for e in tr_a2.events)
    # acl version bump → miss
    resp_a3, tr_a3 = gw.complete(
        tenant_id="tenantA",
        acl_version="acl-2",
        task_class="chat",
        sensitivity="low",
        prompt="same-query-secret",
    )
    assert not any(e["event"] == "cache_hit" for e in tr_a3.events)
    print("SLO_ok_cross_tenant_cache_0:", True)

    print("=== demo4: budget exhausted — no premium call ===")
    premium_calls_before = premium.calls
    try:
        gw.complete(
            tenant_id="tenantPoor",
            acl_version="acl-1",
            task_class="codegen",
            sensitivity="low",
            prompt="write expensive code",
            allow_degrade=False,
        )
        raise AssertionError("should fail")
    except BudgetExhausted as e:
        print("blocked:", e)
    assert premium.calls == premium_calls_before
    assert gw.expensive_calls_when_over_budget == 0
    # with degrade: economy only
    economy_before = economy.calls
    # give tenantPoor a tiny top-up so economy can charge, still force economy path
    budgets.tenants["tenantPoor"].daily_used = 90
    budgets.tenants["tenantPoor"].monthly_used = 90
    budgets.tenants["tenantPoor"].daily_limit = 100
    resp_d, tr_d = gw.complete(
        tenant_id="tenantPoor",
        acl_version="acl-1",
        task_class="codegen",
        sensitivity="low",
        prompt="cheap path only",
        allow_degrade=True,
    )
    print("degraded model:", resp_d.model, tr_d.events)
    assert resp_d.model == "economy"
    assert premium.calls == premium_calls_before
    print("SLO_ok_over_budget_premium_0:", True)

    print("=== demo5: high sensitivity → safe-small ===")
    resp_s, tr_s = gw.complete(
        tenant_id="tenantA",
        acl_version="acl-1",
        task_class="chat",
        sensitivity="high",
        prompt="payroll query",
    )
    print(resp_s.model, [e for e in tr_s.events if e["event"] == "route"])
    assert resp_s.model == "safe-small"

    print("ALL_OK")


if __name__ == "__main__":
    main()
