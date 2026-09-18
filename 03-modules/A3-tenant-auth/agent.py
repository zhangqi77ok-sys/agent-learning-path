"""Agent runtime: trusts only gateway internal tokens; ACL before retrieve; audit."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field

from approvals import ApprovalStore
from gateway import GATEWAY_SECRET
from kb import retrieve
from tokens import verify_internal_token


@dataclass
class AuditLog:
    entries: list[dict] = field(default_factory=list)

    def write(self, **kwargs) -> None:
        self.entries.append({"ts_ms": time.time() * 1000, **kwargs})


class AgentRuntime:
    def __init__(self):
        self.approvals = ApprovalStore()
        self.audit = AuditLog()
        self.side_effects: list[str] = []

    def _auth(self, token: str | None, now: float | None = None) -> dict:
        if not token:
            raise PermissionError("missing_internal_token")
        return verify_internal_token(token, secret=GATEWAY_SECRET, now=now)

    def ask(self, token: str, query: str, now: float | None = None) -> dict:
        claims = self._auth(token, now=now)
        hits = retrieve(query, tenant_id=claims["tenant_id"], roles=list(claims["roles"]))
        self.audit.write(
            action="retrieve",
            tenant_id=claims["tenant_id"],
            user_id=claims["user_id"],
            trace_id=claims["trace_id"],
            doc_ids=[h["id"] for h in hits],
        )
        return {"tenant_id": claims["tenant_id"], "hits": hits}

    def export_all(self, token: str, *, approval_id: str | None = None, now: float | None = None) -> dict:
        """High-risk tool: requires approver role + valid approval."""
        claims = self._auth(token, now=now)
        if "approver" not in claims["roles"]:
            self.audit.write(action="export_denied_role", user_id=claims["user_id"], tenant_id=claims["tenant_id"])
            raise PermissionError("role_not_allowed")
        snap = hashlib.sha256(f"export:{claims['tenant_id']}".encode()).hexdigest()
        if not approval_id:
            a = self.approvals.request(
                tenant_id=claims["tenant_id"],
                user_id=claims["user_id"],
                action="export_all",
                snapshot_hash=snap,
                ttl_ms=50,  # short for demo expiry unless decided quickly
            )
            self.audit.write(action="approval_requested", approval_id=a.approval_id, user_id=claims["user_id"])
            return {"status": "pending_approval", "approval_id": a.approval_id, "snapshot_hash": snap}

        self.approvals.assert_executable(approval_id, snapshot_hash=snap, now=now)
        self.side_effects.append(f"export:{claims['tenant_id']}")
        self.audit.write(action="export_executed", approval_id=approval_id, user_id=claims["user_id"])
        return {"status": "exported", "tenant_id": claims["tenant_id"]}
