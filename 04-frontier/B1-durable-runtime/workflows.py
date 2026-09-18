"""CreateTicketWorkflow — Durable orchestration. No business DB tx here."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities import CreateTicketInput, create_ticket_activity, record_outbox_dispatched


@dataclass
class StartTicket:
    tenant_id: str
    thread_id: str
    effect_key: str
    title: str
    amount: int
    snapshot_hash: str


@dataclass
class ApprovalSignal:
    approver: str
    approved: bool
    snapshot_hash: str


@workflow.defn
class CreateTicketWorkflow:
    def __init__(self) -> None:
        self._approval: ApprovalSignal | None = None
        self._ticket_ref: str | None = None
        self._status = "awaiting_approval"

    @workflow.signal
    def approval_granted(self, sig: ApprovalSignal) -> None:
        # Signal only records intent — MUST NOT call domain API here
        self._approval = sig

    @workflow.query
    def status(self) -> dict:
        return {
            "status": self._status,
            "ticket_ref": self._ticket_ref,
            "has_approval": self._approval is not None,
        }

    @workflow.run
    async def run(self, start: StartTicket) -> str:
        # Wait for HITL (Signal) — durable wait, survives worker crash
        await workflow.wait_condition(lambda: self._approval is not None)
        assert self._approval is not None

        if not self._approval.approved:
            self._status = "rejected"
            return "rejected"

        if self._approval.snapshot_hash != start.snapshot_hash:
            self._status = "snapshot_mismatch"
            raise RuntimeError("snapshot_mismatch")

        # Outbox-equivalent: Activity with idempotency key (tenant:thread:effect)
        idem = f"{start.tenant_id}:{start.thread_id}:{start.effect_key}"
        self._status = "dispatching_outbox"

        retry = RetryPolicy(
            initial_interval=timedelta(milliseconds=100),
            maximum_attempts=5,
        )
        ref = await workflow.execute_activity(
            create_ticket_activity,
            CreateTicketInput(idempotency_key=idem, title=start.title, amount=start.amount),
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=retry,
        )
        await workflow.execute_activity(
            record_outbox_dispatched,
            idem,
            start_to_close_timeout=timedelta(seconds=5),
        )
        self._ticket_ref = ref
        self._status = "done"
        return ref
