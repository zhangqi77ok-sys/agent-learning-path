"""A2 fault injection: crash after external, resume no double-write, lease contention, cancel."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from engine import RunEngine
from store import Store


def main() -> None:
    db = Path(tempfile.mkdtemp()) / "a2.sqlite"
    store = Store(db)
    tenant, thread = "t1", "th-purchase"

    print("=== demo1: O1 crash after external, resume without second call ===")
    calls = {"n": 0}

    def ext(_k: str) -> str:
        calls["n"] += 1
        return f"TICKET-{calls['n']}"

    eng = RunEngine(store, worker_id="w1", crash_after_external=True)
    run_id = "run-o1"
    try:
        eng.run_purchase_approval(tenant_id=tenant, thread_id=thread, run_id=run_id, external=ext)
    except RuntimeError as e:
        print("crashed:", e)
    print("external_calls_before_resume:", calls["n"])

    eng2 = RunEngine(store, worker_id="w1", crash_after_external=False)
    # reuse same external counter to prove we don't call again
    result = eng2.run_purchase_approval(tenant_id=tenant, thread_id=thread, run_id=run_id, external=ext)
    print(result)
    print("external_calls_total:", calls["n"], "SLO_ok_idempotent:", calls["n"] == 1)

    print("=== demo2: dual worker lease ===")
    store2 = Store(Path(tempfile.mkdtemp()) / "a2b.sqlite")
    a = RunEngine(store2, "worker-a")
    b = RunEngine(store2, "worker-b")
    # manually acquire by A
    assert store2.try_acquire_lease("run-lease", "worker-a", ttl_ms=10_000)
    denied = b.run_purchase_approval(tenant_id="t1", thread_id="th2", run_id="run-lease")
    print(denied)
    assert denied["status"] == "lease_denied"
    print("SLO_ok_lease:", True)

    print("=== demo3: cancel before finalize ===")
    store3 = Store(Path(tempfile.mkdtemp()) / "a2c.sqlite")
    eng3 = RunEngine(store3, "w3", cancel_requested=True)
    r3 = eng3.run_purchase_approval(tenant_id="t1", thread_id="th3", run_id="run-cancel")
    print(r3)
    assert r3["status"] == "cancelled"
    print("SLO_ok_cancel:", True)

    print("db_demo1:", db)


if __name__ == "__main__":
    main()
