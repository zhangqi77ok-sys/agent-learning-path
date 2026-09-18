"""Capstone control plane: Java token → harness → RAG/tools/HITL → outbox → trace."""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from control_plane.effects import Approval, ApprovalStore, MockTicketAPI, dispatch_outbox
from control_plane.harness import Harness
from control_plane.identity import IsolationKeys, verify_internal_token
from control_plane.rag import retrieve
from control_plane.store import Store


FORBIDDEN = {"export_all"}


@dataclass
class AgentControlPlane:
    store: Store
    approvals: ApprovalStore = field(default_factory=ApprovalStore)
    tickets: MockTicketAPI = field(default_factory=MockTicketAPI)
    traces: list[dict] = field(default_factory=list)

    def start_run(self, token: str, thread_id: str | None = None) -> IsolationKeys:
        claims = verify_internal_token(token)
        keys = IsolationKeys(
            tenant_id=claims["tenant_id"],
            user_id=claims["user_id"],
            thread_id=thread_id or str(uuid.uuid4())[:8],
            run_id=str(uuid.uuid4())[:8],
        )
        self.store.save_checkpoint(keys, 0, {"status": "started", "roles": claims["roles"]})
        return keys

    def ask(self, token: str, keys: IsolationKeys, query: str) -> dict[str, Any]:
        claims = verify_internal_token(token)
        if claims["tenant_id"] != keys.tenant_id or claims["user_id"] != keys.user_id:
            raise PermissionError("key_mismatch")
        roles = set(claims["roles"])
        harness = Harness()
        spans: list[dict] = []
        # retrieve
        if not harness.allow_tool("retrieve", {"q": query}):
            return {"status": harness.status, "answer": None}
        filt = {"tenant_id": keys.tenant_id, "roles": sorted(roles)}
        hits = retrieve(tenant_id=keys.tenant_id, roles=roles, query=query)
        spans.append({"name": "tool.retrieve", "attributes": {"filter": filt, "hits": len(hits)}})
        harness.tick()
        answer = hits[0].text if hits else "无权限可见文档"
        cited = bool(hits)
        self.store.save_checkpoint(keys, harness.steps, {"query": query, "hits": len(hits)})
        trace = {
            "trace_id": f"tr_{keys.run_id}",
            "tenant_id": keys.tenant_id,
            "query": query,
            "spans": spans,
            "answer": answer,
        }
        self.traces.append(trace)
        return {"status": "ok", "answer": answer, "cited": cited, "hits": len(hits), "keys": keys, "trace": trace}

    def request_side_effect(self, keys: IsolationKeys, effect_key: str, payload: dict, approver: str) -> str:
        snap = hashlib.sha256(str(sorted(payload.items())).encode()).hexdigest()[:16]
        aid = str(uuid.uuid4())[:8]
        self.approvals.request(
            Approval(
                approval_id=aid,
                tenant_id=keys.tenant_id,
                approver=approver,
                snapshot_hash=snap,
                expires_at=time.time() + 3600,
            )
        )
        return aid

    def resume_approved_effect(
        self, keys: IsolationKeys, approval_id: str, effect_key: str, payload: dict, approver: str
    ) -> str:
        snap = hashlib.sha256(str(sorted(payload.items())).encode()).hexdigest()[:16]
        self.approvals.decide(approval_id, approver, True)
        self.approvals.assert_executable(approval_id, snap)
        idem = self.store.begin_effect(keys.tenant_id, keys.thread_id, effect_key)
        row = self.store.get_effect(idem)
        if row and row["status"] == "done" and row["external_ref"]:
            return row["external_ref"]
        self.store.enqueue_outbox(keys.tenant_id, keys.thread_id, effect_key, payload)
        dispatch_outbox(self.store, self.tickets)
        row2 = self.store.get_effect(idem)
        return row2["external_ref"]

    def run_tool_loop(self, tool_name: str, args: dict, harness: Harness | None = None) -> Harness:
        h = harness or Harness()
        while h.status == "running":
            if tool_name in FORBIDDEN:
                h.events.append({"event": "forbidden_blocked", "tool": tool_name})
                h.status = "policy_blocked"
                break
            if not h.allow_tool(tool_name, args):
                break
            h.tick()
        return h
