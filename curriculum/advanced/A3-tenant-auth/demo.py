"""A3 fault injection: bypass gateway, tamper claim, cross-tenant ACL, expired approval."""

from __future__ import annotations

import time

from agent import AgentRuntime
from gateway import GATEWAY_SECRET, login
from tokens import issue_internal_token


def main() -> None:
    rt = AgentRuntime()

    print("=== demo1: cross-tenant retrieval ACL ===")
    tok_a = login("alice", "pw")
    tok_b = login("bob", "pw")
    hits_a = rt.ask(tok_a, "差旅")["hits"]
    hits_b = rt.ask(tok_b, "差旅")["hits"]
    print("A docs", [h["id"] for h in hits_a], "B docs", [h["id"] for h in hits_b])
    assert all(h["tenant_id"] == "tenantA" for h in hits_a)
    assert all(h["tenant_id"] == "tenantB" for h in hits_b)
    assert not any(h["id"].startswith("B") for h in hits_a)
    print("SLO_ok_no_cross_tenant:", True)

    print("=== demo2: role ACL — user cannot see approver-only doc ===")
    secret_hits = rt.ask(tok_a, "机密")["hits"]
    print("alice secret hits", [h["id"] for h in secret_hits])
    assert "A2" not in [h["id"] for h in secret_hits]
    tok_admin = login("adminA", "pw")
    admin_hits = rt.ask(tok_admin, "机密")["hits"]
    print("admin secret hits", [h["id"] for h in admin_hits])
    assert any(h["id"] == "A2" for h in admin_hits)

    print("=== demo3: bypass gateway (no token) ===")
    try:
        rt.ask(None, "差旅")  # type: ignore
        raise AssertionError("should fail")
    except PermissionError as e:
        print("blocked:", e)

    print("=== demo4: tamper tenant claim ===")
    # forge token with wrong signature / swapped tenant
    bad = issue_internal_token(
        secret="wrong-secret",
        tenant_id="tenantB",
        user_id="alice",
        roles=["user"],
        trace_id="x",
    )
    try:
        rt.ask(bad, "差旅")
        raise AssertionError("should fail")
    except ValueError as e:
        print("blocked:", e)

    print("=== demo5: high-risk export needs approval; expiry blocks side effect ===")
    pending = rt.export_all(tok_admin)
    print(pending)
    appr_id = pending["approval_id"]
    time.sleep(0.06)  # expire TTL=50ms
    try:
        rt.approvals.decide(appr_id, approver_id="adminA", approve=True)
        rt.export_all(tok_admin, approval_id=appr_id)
        raise AssertionError("should fail expired")
    except PermissionError as e:
        print("expired_blocked:", e)
    assert rt.side_effects == []
    print("SLO_ok_expired_no_side_effect:", True)

    print("=== demo6: approve in time then export ===")
    pending2 = rt.export_all(tok_admin)
    rt.approvals.items[pending2["approval_id"]].exp_ms = time.time() * 1000 + 10_000
    rt.approvals.decide(pending2["approval_id"], approver_id="adminA", approve=True)
    out = rt.export_all(tok_admin, approval_id=pending2["approval_id"])
    print(out, "effects", rt.side_effects)
    assert out["status"] == "exported"

    print("=== demo7: non-approver cannot export ===")
    try:
        rt.export_all(tok_a)
        raise AssertionError("should fail")
    except PermissionError as e:
        print("blocked:", e)

    print("ALL_OK")


if __name__ == "__main__":
    main()
