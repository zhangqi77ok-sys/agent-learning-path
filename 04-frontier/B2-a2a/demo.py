"""B2 fault injection: missing identity/idem, duplicate idem, deadline cancel, cross-tenant."""

from __future__ import annotations

import time

from client.a2a_client import A2AClient
from identity import issue
from server.a2a_server import A2AServer


def main() -> None:
    srv = A2AServer()
    cli = A2AClient(srv)
    now = int(time.time() * 1000)
    tok_a = issue("tenantA", "u1", ["employee"])
    tok_b = issue("tenantB", "u2", ["employee"])

    print("=== demo1: happy path delegate ===")
    t1 = cli.delegate(
        token=tok_a,
        idempotency_key="tenantA:th1:eff1",
        trace_id="tr-1",
        deadline_ms=now + 60_000,
        task_type="summarize_policy",
        payload={"q": "差旅"},
        now_ms=now,
    )
    print(t1.status, t1.result, "side_effects:", t1.side_effect_count)
    assert t1.status == "done" and t1.side_effect_count == 1

    print("=== demo2: duplicate idempotency → same task, no double side effect ===")
    t2 = cli.delegate(
        token=tok_a,
        idempotency_key="tenantA:th1:eff1",
        trace_id="tr-1",
        deadline_ms=now + 60_000,
        task_type="summarize_policy",
        payload={"q": "差旅"},
        now_ms=now,
    )
    assert t2.id == t1.id
    assert t1.side_effect_count == 1
    print("same_id:", t2.id, "side_effects:", t1.side_effect_count)
    print("SLO_ok_idempotent_delegate:", True)

    print("=== demo3: missing identity / idem / deadline ===")
    for kwargs, err in [
        (dict(token=None, idempotency_key="tenantA:th:e", trace_id="t", deadline_ms=now + 1, task_type="x", payload={}, now_ms=now, auto_run=False), "missing_identity"),
        (dict(token=tok_a, idempotency_key=None, trace_id="t", deadline_ms=now + 1, task_type="x", payload={}, now_ms=now, auto_run=False), "missing_idempotency_key"),
        (dict(token=tok_a, idempotency_key="tenantA:th:e2", trace_id="t", deadline_ms=None, task_type="x", payload={}, now_ms=now, auto_run=False), "missing_deadline"),
    ]:
        try:
            cli.delegate(**kwargs)
            raise AssertionError("should fail")
        except PermissionError as e:
            print("blocked:", e)
            assert str(e) == err

    print("=== demo4: past deadline → cancelled, side_effect=0 ===")
    t3 = cli.delegate(
        token=tok_a,
        idempotency_key="tenantA:th1:late",
        trace_id="tr-late",
        deadline_ms=now - 1,
        task_type="summarize_policy",
        payload={"q": "x"},
        now_ms=now,
        auto_run=True,
    )
    print(t3.status, "side_effects:", t3.side_effect_count)
    assert t3.status == "cancelled" and t3.side_effect_count == 0
    print("SLO_ok_deadline_cancel:", True)

    print("=== demo5: explicit cancel before run ===")
    t4 = cli.delegate(
        token=tok_a,
        idempotency_key="tenantA:th1:cancel",
        trace_id="tr-c",
        deadline_ms=now + 60_000,
        task_type="summarize_policy",
        payload={"q": "x"},
        now_ms=now,
        auto_run=False,
    )
    srv.cancel(t4.id, token=tok_a)
    srv.run_task(t4.id, now_ms=now)
    assert t4.status == "cancelled" and t4.side_effect_count == 0
    print("SLO_ok_explicit_cancel:", True)

    print("=== demo6: cross-tenant cancel blocked ===")
    t5 = cli.delegate(
        token=tok_a,
        idempotency_key="tenantA:th1:x",
        trace_id="tr-x",
        deadline_ms=now + 60_000,
        task_type="summarize_policy",
        payload={},
        now_ms=now,
        auto_run=False,
    )
    try:
        srv.cancel(t5.id, token=tok_b)
        raise AssertionError("should fail")
    except PermissionError as e:
        print("blocked:", e)
        assert str(e) == "cross_tenant_cancel"

    print("=== demo7: idem key tenant mismatch ===")
    try:
        cli.delegate(
            token=tok_a,
            idempotency_key="tenantB:th:e",
            trace_id="t",
            deadline_ms=now + 1,
            task_type="x",
            payload={},
            now_ms=now,
            auto_run=False,
        )
        raise AssertionError("should fail")
    except PermissionError as e:
        print("blocked:", e)
        assert str(e) == "idempotency_tenant_mismatch"

    print("ALL_OK")


if __name__ == "__main__":
    main()
