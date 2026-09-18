"""Long-running run engine with durable checkpoint, effect ledger, outbox, lease."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Protocol

from store import Store


class ExternalClient(Protocol):
    def create_ticket(self, *, idempotency_key: str, effect_key: str) -> str:
        ...

    def find_by_idempotency_key(self, idempotency_key: str) -> str | None:
        ...


@dataclass
class MockTicketAPI:
    """Simulates an external API that dedupes by Idempotency-Key."""

    calls: list[str] = field(default_factory=list)
    by_key: dict[str, str] = field(default_factory=dict)
    # if True, succeed remotely but caller crashes before writing ref locally
    crash_before_local_ref: bool = False

    def create_ticket(self, *, idempotency_key: str, effect_key: str) -> str:
        self.calls.append(idempotency_key)
        if idempotency_key in self.by_key:
            return self.by_key[idempotency_key]  # idempotent replay
        ref = f"TICKET-{len(self.by_key)+1}"
        self.by_key[idempotency_key] = ref
        return ref

    def find_by_idempotency_key(self, idempotency_key: str) -> str | None:
        return self.by_key.get(idempotency_key)


@dataclass
class RunEngine:
    store: Store
    worker_id: str
    api: MockTicketAPI
    # fault: after remote success, crash before local external_ref is written
    crash_before_local_ref: bool = False
    # fault: after local unknown+ref, crash before succeeded checkpoint
    crash_after_local_ref: bool = False
    cancel_requested: bool = False

    def run_purchase_approval(
        self,
        *,
        tenant_id: str,
        thread_id: str,
        run_id: str | None = None,
    ) -> dict:
        run_id = run_id or str(uuid.uuid4())
        if not self.store.try_acquire_lease(run_id, self.worker_id):
            return {"status": "lease_denied", "run_id": run_id}

        try:
            existing = self.store.load_checkpoint(tenant_id, thread_id, run_id)
            step = int(existing["step"]) if existing else 0
            status = existing["status"] if existing else "running"
            if status in ("succeeded", "cancelled", "compensated"):
                return {"status": status, "run_id": run_id, "resumed": True, "api_calls": len(self.api.calls)}

            if self.cancel_requested:
                self.store.save_checkpoint(tenant_id, thread_id, run_id, step, "cancelled", "{}")
                return {"status": "cancelled", "run_id": run_id, "api_calls": len(self.api.calls)}

            effect_key = "create_ticket"
            # Stable idempotency key for this business intent (NOT a random uuid per attempt)
            idem_key = f"{tenant_id}:{thread_id}:{effect_key}"
            ledger_status = self.store.begin_effect(tenant_id, thread_id, effect_key)

            if ledger_status == "succeeded":
                step = max(step, 1)
            else:
                row = self.store.conn.execute(
                    "SELECT status, external_ref FROM effect_ledger WHERE tenant_id=? AND thread_id=? AND effect_key=?",
                    (tenant_id, thread_id, effect_key),
                ).fetchone()
                ref = row["external_ref"] if row else None
                st = row["status"] if row else "started"

                if st == "succeeded" and ref:
                    step = max(step, 1)
                elif ref:
                    # unknown/started with ref: reconcile only, never re-call blindly
                    self.store.complete_effect(tenant_id, thread_id, effect_key, ref, status="succeeded")
                    self.store.enqueue_outbox(tenant_id, thread_id, effect_key, json.dumps({"ref": ref}))
                    step = max(step, 1)
                else:
                    # started with NO ref: DO NOT bare-retry.
                    # 1) probe remote by idempotency key
                    # 2) if missing, call WITH the same Idempotency-Key
                    existing_ref = self.api.find_by_idempotency_key(idem_key)
                    if existing_ref:
                        ref = existing_ref
                    else:
                        ref = self.api.create_ticket(idempotency_key=idem_key, effect_key=effect_key)
                        if self.crash_before_local_ref:
                            # remote has ticket; local still started/no ref
                            raise RuntimeError("injected_crash_before_local_ref")

                    self.store.complete_effect(tenant_id, thread_id, effect_key, ref, status="unknown")
                    self.store.enqueue_outbox(tenant_id, thread_id, effect_key, json.dumps({"ref": ref}))
                    if self.crash_after_local_ref:
                        raise RuntimeError("injected_crash_after_local_ref")
                    self.store.complete_effect(tenant_id, thread_id, effect_key, ref, status="succeeded")
                    step = 1

            if self.cancel_requested:
                self.store.save_checkpoint(tenant_id, thread_id, run_id, step, "cancelled", "{}")
                return {"status": "cancelled", "run_id": run_id, "api_calls": len(self.api.calls)}

            self.store.save_checkpoint(
                tenant_id, thread_id, run_id, step, "succeeded", json.dumps({"ok": True})
            )
            dispatched = self.store.dispatch_outbox_once()
            return {
                "status": "succeeded",
                "run_id": run_id,
                "api_calls": len(self.api.calls),
                "unique_keys": len(self.api.by_key),
                "outbox_dispatched": len(dispatched),
            }
        finally:
            self.store.release_lease(run_id, self.worker_id)
