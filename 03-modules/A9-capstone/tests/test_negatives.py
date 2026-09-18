"""Capstone negative cases — one per segment."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

import pytest

from control_plane.agent import AgentControlPlane
from control_plane.eval_bridge import append_regression, trace_to_fixture
from control_plane.identity import IsolationKeys, issue_internal_token, verify_internal_token
from control_plane.store import Store


@pytest.fixture()
def cp(tmp_path: Path):
    return AgentControlPlane(Store(tmp_path / "t.db"))


def test_a_cross_tenant_checkpoint_zero(cp):
    tok = issue_internal_token(tenant_id="tenantA", user_id="u1", roles=["employee"])
    keys = cp.start_run(tok)
    assert cp.store.cross_tenant_checkpoint_rows("tenantB", keys.thread_id, keys.run_id) == 0


def test_a_forged_tenant_rejected():
    tok = issue_internal_token(tenant_id="tenantA", user_id="u1", roles=["employee"])
    body, sig = tok.rsplit(".", 1)
    forged = body.replace("tenantA", "tenantB") + "." + sig
    with pytest.raises(PermissionError):
        verify_internal_token(forged)


def test_b_duplicate_resume_exactly_one(cp):
    tok = issue_internal_token(tenant_id="tenantA", user_id="u1", roles=["employee"])
    keys = cp.start_run(tok)
    payload = {"x": 1}
    aid = cp.request_side_effect(keys, "eff1", payload, "boss")
    r1 = cp.resume_approved_effect(keys, aid, "eff1", payload, "boss")
    r2 = cp.resume_approved_effect(keys, aid, "eff1", payload, "boss")
    assert r1 == r2
    assert cp.tickets.create_calls == 1


def test_b_expired_approval_blocks(cp):
    tok = issue_internal_token(tenant_id="tenantA", user_id="u1", roles=["employee"])
    keys = cp.start_run(tok)
    payload = {"x": 1}
    aid = cp.request_side_effect(keys, "eff2", payload, "boss")
    cp.approvals.items[aid].expires_at = time.time() - 1
    with pytest.raises(PermissionError, match="approval_expired"):
        cp.resume_approved_effect(keys, aid, "eff2", payload, "boss")


def test_c_cross_tenant_rag(cp):
    tok_a = issue_internal_token(tenant_id="tenantA", user_id="u1", roles=["employee"])
    keys = cp.start_run(tok_a)
    out = cp.ask(tok_a, keys, "差旅")
    assert "tenantB" not in out["answer"]


def test_d_circuit_open(cp):
    h = cp.run_tool_loop("ping", {"a": 1})
    assert h.status == "circuit_open"


def test_d_forbidden_tool(cp):
    h = cp.run_tool_loop("export_all", {})
    assert h.status == "policy_blocked"


def test_e_incomplete_fixture_blocked(tmp_path: Path):
    fix = trace_to_fixture(
        {
            "trace_id": "t",
            "tenant_id": "tenantA",
            "query": "q",
            "spans": [{"name": "tool.retrieve", "attributes": {}}],
        }
    )
    with pytest.raises(PermissionError, match="incomplete"):
        append_regression(fix, tmp_path / "r.json")
