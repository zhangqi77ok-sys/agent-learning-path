"""Temporal Activities = side effects. Must be idempotent."""

from __future__ import annotations

from dataclasses import dataclass

from temporalio import activity

from ticket_api import TicketAPI

# process-local stand-in; in prod inject via activity context / client
API = TicketAPI()


@dataclass
class CreateTicketInput:
    idempotency_key: str
    title: str
    amount: int


@activity.defn
async def create_ticket_activity(inp: CreateTicketInput) -> str:
    # Activity may retry — API dedupes by idempotency_key
    return API.create_ticket(
        idempotency_key=inp.idempotency_key,
        title=inp.title,
        amount=inp.amount,
    )


@activity.defn
async def record_outbox_dispatched(idempotency_key: str) -> str:
    """Audit marker: Outbox entry marked dispatched (ledger side)."""
    return f"outbox_done:{idempotency_key}"
