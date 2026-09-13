"""Approved side effects via outbox + idempotent external mock."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from control_plane.store import Store


@dataclass
class MockTicketAPI:
    by_idem: dict[str, str] = field(default_factory=dict)
    create_calls: int = 0

    def find(self, idem: str) -> str | None:
        return self.by_idem.get(idem)

    def create(self, idem: str, payload: dict) -> str:
        self.create_calls += 1
        if idem in self.by_idem:
            return self.by_idem[idem]
        ref = f"TCK-{len(self.by_idem)+1}"
        self.by_idem[idem] = ref
        return ref


@dataclass
class Approval:
    approval_id: str
    tenant_id: str
    approver: str
    snapshot_hash: str
    expires_at: float
    decided: bool = False
    approved: bool = False


class ApprovalStore:
    def __init__(self) -> None:
        self.items: dict[str, Approval] = {}

    def request(self, a: Approval) -> None:
        self.items[a.approval_id] = a

    def decide(self, approval_id: str, approver: str, approved: bool, now: float | None = None) -> None:
        now = now if now is not None else time.time()
        a = self.items[approval_id]
        if now > a.expires_at:
            raise PermissionError("approval_expired")
        if a.approver != approver:
            raise PermissionError("wrong_approver")
        a.decided = True
        a.approved = approved

    def assert_executable(self, approval_id: str, snapshot_hash: str, now: float | None = None) -> None:
        now = now if now is not None else time.time()
        a = self.items[approval_id]
        if now > a.expires_at:
            raise PermissionError("approval_expired")
        if not a.decided or not a.approved:
            raise PermissionError("not_approved")
        if a.snapshot_hash != snapshot_hash:
            raise PermissionError("snapshot_mismatch")


def dispatch_outbox(store: Store, api: MockTicketAPI) -> int:
    """Deliver pending outbox idempotently. Returns external creates attempted after find."""
    n = 0
    for row in store.pending_outbox():
        idem = f"{row['tenant_id']}:{row['thread_id']}:{row['effect_key']}"
        existing = api.find(idem)
        if existing:
            store.complete_effect(idem, existing)
            store.mark_outbox(row["id"], "done")
            continue
        ref = api.create(idem, {})
        store.complete_effect(idem, ref)
        store.mark_outbox(row["id"], "done")
        n += 1
    return n
