from __future__ import annotations

from pathlib import Path

from hotplug_harness import Budget, Harness, ToolCall, load_default
from hotplug_harness.contracts import IsolationKeys, RunState

ROOT = Path(__file__).resolve().parent.parent


def test_allowlist_blocks_forbidden():
    reg = load_default(ROOT)
    model = reg.get_model("forbidden_tool")
    h = Harness(registry=reg, model=model, budget=Budget(), policy_names=("allowlist",))
    s = h.start_run(tenant_id="t", user_id="u", thread_id="th")
    h.run_until_done(s)
    assert s.status.value == "policy_blocked"
    assert "drop_db" in s.final


def test_allowlist_policy_direct():
    reg = load_default(ROOT)
    policy = reg.get_policy("allowlist")
    state = RunState(isolation=IsolationKeys("t", "u", "th", "r"))
    ok = policy.check(state, ToolCall("echo", {"message": "x"}))
    bad = policy.check(state, ToolCall("drop_db", {}))
    assert ok.allow
    assert not bad.allow
