"""A2 fault injection including O1 started-without-ref (no bare retry)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from engine import MockTicketAPI, RunEngine
from store import Store


def main() -> None:
    print("=== demo1a: crash BEFORE local ref (started, no ref) then resume ===")
    db = Path(tempfile.mkdtemp()) / "a2a.sqlite"
    store = Store(db)
    api = MockTicketAPI()
    tenant, thread, run_id = "t1", "th-purchase", "run-o1a"

    eng = RunEngine(store, "w1", api, crash_before_local_ref=True)
    try:
        eng.run_purchase_approval(tenant_id=tenant, thread_id=thread, run_id=run_id)
    except RuntimeError as e:
        print("crashed:", e)
    print("api_calls_after_crash:", len(api.calls), "remote_tickets:", len(api.by_key))
    assert len(api.by_key) == 1

    eng2 = RunEngine(store, "w1", api, crash_before_local_ref=False)
    r = eng2.run_purchase_approval(tenant_id=tenant, thread_id=thread, run_id=run_id)
    print(r)
    # May call create_ticket again WITH same idempotency key, but remote returns same ticket.
    # Unique tickets must stay 1; probe+idempotent call must not create a second business effect.
    print(
        "unique_tickets:",
        len(api.by_key),
        "api_http_calls:",
        len(api.calls),
        "SLO_ok_no_double_effect:",
        len(api.by_key) == 1,
    )
    assert len(api.by_key) == 1
    assert r["status"] == "succeeded"

    print("=== demo1b: crash AFTER local unknown+ref then resume ===")
    db2 = Path(tempfile.mkdtemp()) / "a2b.sqlite"
    store2 = Store(db2)
    api2 = MockTicketAPI()
    eng3 = RunEngine(store2, "w1", api2, crash_after_local_ref=True)
    try:
        eng3.run_purchase_approval(tenant_id="t1", thread_id="th-b", run_id="run-o1b")
    except RuntimeError as e:
        print("crashed:", e)
    eng4 = RunEngine(store2, "w1", api2)
    r2 = eng4.run_purchase_approval(tenant_id="t1", thread_id="th-b", run_id="run-o1b")
    print(r2, "unique:", len(api2.by_key), "calls:", len(api2.calls))
    assert len(api2.by_key) == 1 and len(api2.calls) == 1

    print("=== demo2: dual worker lease ===")
    store3 = Store(Path(tempfile.mkdtemp()) / "a2c.sqlite")
    assert store3.try_acquire_lease("run-lease", "worker-a", ttl_ms=10_000)
    denied = RunEngine(store3, "worker-b", MockTicketAPI()).run_purchase_approval(
        tenant_id="t1", thread_id="th2", run_id="run-lease"
    )
    print(denied)
    assert denied["status"] == "lease_denied"

    print("=== demo3: cancel ===")
    store4 = Store(Path(tempfile.mkdtemp()) / "a2d.sqlite")
    r3 = RunEngine(store4, "w3", MockTicketAPI(), cancel_requested=True).run_purchase_approval(
        tenant_id="t1", thread_id="th3", run_id="run-cancel"
    )
    print(r3)
    assert r3["status"] == "cancelled"
    print("ALL_OK")


if __name__ == "__main__":
    main()
