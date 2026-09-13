from __future__ import annotations

from pathlib import Path

from hotplug_harness import Budget, CircuitBreaker, Harness, load_default

ROOT = Path(__file__).resolve().parent.parent


def test_circuit_opens_on_duplicate_signature():
    reg = load_default(ROOT)
    model = reg.get_model("infinite_same_tool")
    h = Harness(
        registry=reg,
        model=model,
        budget=Budget(max_steps=8, max_tool_calls=100),
        circuit=CircuitBreaker(duplicate_signature_limit=3),
    )
    s = h.start_run(tenant_id="t", user_id="u", thread_id="th")
    h.run_until_done(s)
    assert s.status.value == "circuit_open"
    assert any(e.kind == "circuit" for e in s.events)
