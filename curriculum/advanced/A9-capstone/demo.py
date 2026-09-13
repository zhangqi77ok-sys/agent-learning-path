"""A9 Capstone five-segment demo + negatives."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

from control_plane.agent import AgentControlPlane
from control_plane.eval_bridge import append_regression, trace_to_fixture
from control_plane.harness import Harness
from control_plane.identity import issue_internal_token
from control_plane.store import Store


def main() -> None:
    db = Path(tempfile.mkdtemp()) / "cap.db"
    store = Store(db)
    cp = AgentControlPlane(store)

    token_a = issue_internal_token(tenant_id="tenantA", user_id="u1", roles=["employee"])
    token_b = issue_internal_token(tenant_id="tenantB", user_id="u2", roles=["employee"])
    token_admin = issue_internal_token(tenant_id="tenantA", user_id="admin1", roles=["admin", "employee"])

    print("=== (a) isolation keys + cross-tenant checkpoint = 0 ===")
    keys_a = cp.start_run(token_a)
    print("keys:", keys_a)
    row = store.read_checkpoint(keys_a.tenant_id, keys_a.thread_id, keys_a.run_id)
    assert row is not None
    assert row["tenant_id"] == keys_a.tenant_id
    assert row["user_id"] == keys_a.user_id
    assert row["thread_id"] == keys_a.thread_id
    assert row["run_id"] == keys_a.run_id
    cross = store.cross_tenant_checkpoint_rows("tenantB", keys_a.thread_id, keys_a.run_id)
    print("cross_tenant_rows:", cross)
    assert cross == 0
    print("SLO_ok_isolation:", True)

    print("=== (b) idempotent approved side effect + outbox ===")
    payload = {"title": "buy laptop", "amount": 10000}
    aid = cp.request_side_effect(keys_a, "create_ticket", payload, approver="boss")
    ref1 = cp.resume_approved_effect(keys_a, aid, "create_ticket", payload, "boss")
    # duplicate resume / redispatch
    ref2 = cp.resume_approved_effect(keys_a, aid, "create_ticket", payload, "boss")
    store.enqueue_outbox(keys_a.tenant_id, keys_a.thread_id, "create_ticket", payload)
    from control_plane.effects import dispatch_outbox

    dispatch_outbox(store, cp.tickets)
    print("refs:", ref1, ref2, "create_calls:", cp.tickets.create_calls)
    assert ref1 == ref2
    assert cp.tickets.create_calls == 1
    print("SLO_ok_exactly_once_side_effect:", True)

    print("=== (c) retrieval ACL ===")
    out_a = cp.ask(token_a, keys_a, "差旅")
    keys_b = cp.start_run(token_b)
    out_b = cp.ask(token_b, keys_b, "差旅")
    print("A hits:", out_a["hits"], "answer:", out_a["answer"])
    print("B hits:", out_b["hits"], "answer:", out_b["answer"])
    assert out_a["hits"] >= 1 and "tenantA" in out_a["answer"]
    assert out_b["hits"] >= 1 and "tenantB" in out_b["answer"]
    # employee cannot see admin-only
    out_secret = cp.ask(token_a, keys_a, "薪资")
    assert "机密" not in (out_secret["answer"] or "")
    out_admin = cp.ask(token_admin, cp.start_run(token_admin), "薪资")
    assert "机密" in out_admin["answer"]
    print("SLO_ok_rag_acl:", True)

    print("=== (d) loop budget + circuit ===")
    h = cp.run_tool_loop("search", {"q": "x"})
    print("status:", h.status, "events:", h.events)
    assert h.status == "circuit_open"
    assert any(e["event"] == "circuit_open" for e in h.events)
    h2 = Harness(max_steps=3, max_tool_calls=10)
    # varying args won't trip signature circuit quickly — force budget
    for i in range(5):
        if not h2.allow_tool("search", {"q": str(i)}):
            break
        h2.tick()
    print("budget status:", h2.status)
    assert h2.status in ("budget_exhausted", "circuit_open")
    # forbidden
    h3 = cp.run_tool_loop("export_all", {})
    assert h3.status == "policy_blocked"
    print("SLO_ok_circuit_and_forbidden:", True)

    print("=== (e) Trace → Bad Case → Eval replay ===")
    # craft a bad trace: dangerous tool attempted
    bad = {
        "trace_id": "tr_bad1",
        "tenant_id": "tenantA",
        "query": "导出数据联系 13900001111 发 boss@x.com",
        "spans": [
            {"name": "tool.retrieve", "attributes": {"filter": {"tenant_id": "tenantA"}}},
            {"name": "tool.export_all", "attributes": {}},
        ],
        "expect_no_tools": ["export_all"],
    }
    fix = trace_to_fixture(bad)
    print("fixture:", fix)
    assert "[PHONE]" in fix["query"] and "[EMAIL]" in fix["query"]
    reg = Path(tempfile.mkdtemp()) / "regression.json"
    append_regression(fix, reg)
    # CI must run: simulate gate
    cases = __import__("json").loads(reg.read_text())
    assert any("export_all" in c.get("expect_no_tools", []) or "export_all" in c.get("tools", []) for c in cases)
    # incomplete blocked
    bad2 = {
        "trace_id": "tr_bad2",
        "tenant_id": "tenantA",
        "query": "差旅",
        "spans": [{"name": "tool.retrieve", "attributes": {}}],
    }
    fix2 = trace_to_fixture(bad2)
    try:
        append_regression(fix2, reg)
        raise AssertionError("should block incomplete")
    except PermissionError as e:
        print("blocked incomplete:", e)
    print("SLO_ok_trace_to_eval:", True)

    print("=== P95 note ===")
    print("README declares: local/relay P95 target <8s for read-only Q&A; this demo is in-process mocks.")
    print("ALL_OK")


if __name__ == "__main__":
    main()
