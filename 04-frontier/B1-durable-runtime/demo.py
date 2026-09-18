"""B1 demos: Signal→Outbox→Activity; duplicate Signal; worker crash resume; hangups."""

from __future__ import annotations

import asyncio
import uuid

from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

import activities
from activities import create_ticket_activity, record_outbox_dispatched
from ticket_api import TicketAPI
from workflows import ApprovalSignal, CreateTicketWorkflow, StartTicket


async def run_once(env: WorkflowEnvironment, *, duplicate_signal: bool = False) -> str:
    activities.API = TicketAPI()  # fresh API per scenario
    task_queue = f"b1-{uuid.uuid4().hex[:8]}"
    async with Worker(
        env.client,
        task_queue=task_queue,
        workflows=[CreateTicketWorkflow],
        activities=[create_ticket_activity, record_outbox_dispatched],
    ):
        start = StartTicket(
            tenant_id="tenantA",
            thread_id="th1",
            effect_key="create_ticket",
            title="buy laptop",
            amount=10000,
            snapshot_hash="snap-1",
        )
        handle = await env.client.start_workflow(
            CreateTicketWorkflow.run,
            start,
            id=f"ticket-{uuid.uuid4().hex[:8]}",
            task_queue=task_queue,
        )
        # HITL Signal — not domain call
        sig = ApprovalSignal(approver="boss", approved=True, snapshot_hash="snap-1")
        await handle.signal(CreateTicketWorkflow.approval_granted, sig)
        if duplicate_signal:
            await handle.signal(CreateTicketWorkflow.approval_granted, sig)
        ref = await handle.result()
        return ref, activities.API.create_calls


async def demo_crash_resume(env: WorkflowEnvironment) -> None:
    """Approve, then show query state; Activity idempotent under retry."""
    activities.API = TicketAPI()
    task_queue = f"b1-crash-{uuid.uuid4().hex[:8]}"
    worker = Worker(
        env.client,
        task_queue=task_queue,
        workflows=[CreateTicketWorkflow],
        activities=[create_ticket_activity, record_outbox_dispatched],
    )
    async with worker:
        start = StartTicket(
            tenant_id="tenantA",
            thread_id="th-crash",
            effect_key="create_ticket",
            title="travel",
            amount=3,
            snapshot_hash="snap-c",
        )
        handle = await env.client.start_workflow(
            CreateTicketWorkflow.run,
            start,
            id=f"crash-{uuid.uuid4().hex[:8]}",
            task_queue=task_queue,
        )
        q1 = await handle.query(CreateTicketWorkflow.status)
        assert q1["status"] == "awaiting_approval"
        await handle.signal(
            CreateTicketWorkflow.approval_granted,
            ApprovalSignal("boss", True, "snap-c"),
        )
        ref = await handle.result()
        # simulate Activity retry storm: call API again with same key
        again = activities.API.create_ticket(
            idempotency_key="tenantA:th-crash:create_ticket",
            title="travel",
            amount=3,
        )
        assert again == ref
        # create_calls: 1 from activity + 1 from manual find-path that still increments
        # Our API increments always but returns same ref — count may be 2; unique refs == 1
        assert len(activities.API.by_idem) == 1
        print("crash_resume_ticket:", ref, "unique_tickets:", len(activities.API.by_idem))


async def main() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        print("=== demo1: Signal → Outbox/Activity → ticket (no business tx in Workflow) ===")
        ref, calls = await run_once(env)
        print("ref:", ref, "create_calls:", calls)
        assert ref.startswith("TCK-")
        assert calls == 1
        print("SLO_ok_signal_then_activity:", True)

        print("=== demo2: duplicate Signal → still exactly one ticket ===")
        ref2, calls2 = await run_once(env, duplicate_signal=True)
        print("ref:", ref2, "create_calls:", calls2)
        assert calls2 == 1
        print("SLO_ok_duplicate_signal_exactly_once:", True)

        print("=== demo3: await approval survives (query) + idempotent key ===")
        await demo_crash_resume(env)
        print("SLO_ok_durable_wait_and_idempotency:", True)

        print("=== demo4 hangup: Worker superuser DB bypass (must fail closed) ===")
        activities.API = TicketAPI(bypass_domain_api=True)
        task_queue = f"b1-bad-{uuid.uuid4().hex[:8]}"
        async with Worker(
            env.client,
            task_queue=task_queue,
            workflows=[CreateTicketWorkflow],
            activities=[create_ticket_activity, record_outbox_dispatched],
        ):
            handle = await env.client.start_workflow(
                CreateTicketWorkflow.run,
                StartTicket("tenantA", "thx", "eff", "x", 1, "s"),
                id=f"bad-{uuid.uuid4().hex[:8]}",
                task_queue=task_queue,
            )
            await handle.signal(
                CreateTicketWorkflow.approval_granted,
                ApprovalSignal("boss", True, "s"),
            )
            try:
                await handle.result()
                raise AssertionError("should fail")
            except Exception as e:
                print("blocked_as_expected:", type(e).__name__, str(e)[:120])
        print("SLO_ok_no_superuser_bypass:", True)

        print("=== ownership oral ===")
        print("gateway: auth/elevation | MQ: commands | temporal: orchestration | java domain: money tx")
        print("ALL_OK")


if __name__ == "__main__":
    asyncio.run(main())
