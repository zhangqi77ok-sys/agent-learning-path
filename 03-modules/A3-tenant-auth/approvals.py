"""High-risk action approvals with identity + expiry + versioned snapshot."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field


@dataclass
class Approval:
    approval_id: str
    tenant_id: str
    user_id: str
    action: str
    snapshot_hash: str
    approver_id: str | None = None
    status: str = "pending"  # pending|approved|rejected|expired
    exp_ms: float = 0
    created_ms: float = field(default_factory=lambda: time.time() * 1000)


class ApprovalStore:
    def __init__(self):
        self.items: dict[str, Approval] = {}

    def request(self, *, tenant_id: str, user_id: str, action: str, snapshot_hash: str, ttl_ms: float = 60_000) -> Approval:
        a = Approval(
            approval_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            snapshot_hash=snapshot_hash,
            exp_ms=time.time() * 1000 + ttl_ms,
        )
        self.items[a.approval_id] = a
        return a

    def decide(self, approval_id: str, *, approver_id: str, approve: bool, now: float | None = None) -> Approval:
        now_ms = (time.time() if now is None else now) * 1000
        a = self.items[approval_id]
        if now_ms > a.exp_ms:
            a.status = "expired"
            return a
        a.approver_id = approver_id
        a.status = "approved" if approve else "rejected"
        return a

    def assert_executable(self, approval_id: str, *, snapshot_hash: str, now: float | None = None) -> Approval:
        now_ms = (time.time() if now is None else now) * 1000
        a = self.items[approval_id]
        if now_ms > a.exp_ms and a.status == "pending":
            a.status = "expired"
        if a.status != "approved":
            raise PermissionError(f"approval_not_executable:{a.status}")
        if a.snapshot_hash != snapshot_hash:
            raise PermissionError("snapshot_mismatch")
        return a
