from __future__ import annotations

from pathlib import Path

from hotplug_harness import Budget, CircuitBreaker, Harness, load_default

ROOT = Path(__file__).resolve().parent.parent


def test_budget_max_steps():
    reg = load_default(ROOT)
    model = reg.get_model("unique_infinite")
    h = Harness(
        registry=reg,
        model=model,
        budget=Budget(max_steps=5, max_tool_calls=100),
        circuit=CircuitBreaker(3),
    )
    s = h.start_run(tenant_id="t", user_id="u", thread_id="th")
    h.run_until_done(s)
    assert s.status.value == "budget_exceeded"
    tool_events = [e for e in s.events if e.kind == "tool"]
    assert len(tool_events) <= 5
