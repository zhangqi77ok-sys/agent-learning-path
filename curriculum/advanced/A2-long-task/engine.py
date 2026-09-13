"""Long-running run engine with durable checkpoint, effect ledger, outbox, lease."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable

from store import Store


ExternalCall = Callable[[str], str]  # effect_key -> external_ref


@dataclass
class RunEngine:
    store: Store
    worker_id: str
    crash_after_external: bool = False  # fault injection O1
    cancel_requested: bool = False
    external_calls: list[str] = field(default_factory=list)

    def run_purchase_approval(
        self,
        *,
        tenant_id: str,
        thread_id: str,
        run_id: str | None = None,
        external: ExternalCall | None = None,
    ) -> dict:
        run_id = run_id or str(uuid.uuid4())
        if not self.store.try_acquire_lease(run_id, self.worker_id):
            return {"status": "lease_denied", "run_id": run_id}

        try:
            existing = self.store.load_checkpoint(tenant_id, thread_id, run_id)
            step = int(existing["step"]) if existing else 0
            status = existing["status"] if existing else "running"
            if status in ("succeeded", "cancelled", "compensated"):
                return {"status": status, "run_id": run_id, "resumed": True}

            if self.cancel_requested:
                self.store.save_checkpoint(tenant_id, thread_id, run_id, step, "cancelled", "{}")
                return {"status": "cancelled", "run_id": run_id}

            # Step 1: external side effect with ledger (create ticket)
            effect_key = "create_ticket"
            ledger_status = self.store.begin_effect(tenant_id, thread_id, effect_key)
            if ledger_status == "succeeded":
                # already done — skip external call (idempotent resume)
                step = max(step, 1)
            elif ledger_status in ("started", "unknown"):
                # may be first try or crash after external before complete
                if ledger_status == "started" and not self._has_external_ref(tenant_id, thread_id, effect_key):
                    # call external exactly once path via ledger gate
                    fn = external or (lambda k: f"TICKET-{k}-{int(time.time()*1000)%100000}")
                    self.external_calls.append(effect_key)
                    ref = fn(effect_key)
                    # mark unknown until checkpoint+ledger committed
                    self.store.complete_effect(tenant_id, thread_id, effect_key, ref, status="unknown")
                    self.store.enqueue_outbox(tenant_id, thread_id, effect_key, json.dumps({"ref": ref}))
                    if self.crash_after_external:
                        # simulate kill -9 before durable success checkpoint
                        raise RuntimeError("injected_crash_after_external")
                    self.store.complete_effect(tenant_id, thread_id, effect_key, ref, status="succeeded")
                    step = 1
                else:
                    # unknown with ref already — reconcile to succeeded without re-call
                    step = max(step, 1)
                    row = self.store.conn.execute(
                        "SELECT external_ref FROM effect_ledger WHERE tenant_id=? AND thread_id=? AND effect_key=?",
                        (tenant_id, thread_id, effect_key),
                    ).fetchone()
                    if row and row["external_ref"]:
                        self.store.complete_effect(tenant_id, thread_id, effect_key, row["external_ref"], status="succeeded")

            if self.cancel_requested:
                self.store.save_checkpoint(tenant_id, thread_id, run_id, step, "cancelled", "{}")
                return {"status": "cancelled", "run_id": run_id}

            # Step 2: finalize checkpoint
            self.store.save_checkpoint(
                tenant_id, thread_id, run_id, step, "succeeded", json.dumps({"ok": True})
            )
            dispatched = self.store.dispatch_outbox_once()
            return {
                "status": "succeeded",
                "run_id": run_id,
                "external_calls": list(self.external_calls),
                "outbox_dispatched": len(dispatched),
            }
        finally:
            self.store.release_lease(run_id, self.worker_id)

    def _has_external_ref(self, tenant_id: str, thread_id: str, effect_key: str) -> bool:
        row = self.store.conn.execute(
            "SELECT external_ref FROM effect_ledger WHERE tenant_id=? AND thread_id=? AND effect_key=?",
            (tenant_id, thread_id, effect_key),
        ).fetchone()
        return bool(row and row["external_ref"])
