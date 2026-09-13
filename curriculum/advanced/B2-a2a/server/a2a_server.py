"""Minimal A2A task server: identity + idempotency + deadline cancel."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from identity import verify


@dataclass
class Task:
    id: str
    tenant_id: str
    idempotency_key: str
    trace_id: str
    deadline_ms: int
    task_type: str
    payload: dict[str, Any]
    status: str = "pending"  # pending|running|done|cancelled
    result: Any = None
    side_effect_count: int = 0


@dataclass
class A2AServer:
    tasks: dict[str, Task] = field(default_factory=dict)
    by_idem: dict[str, str] = field(default_factory=dict)  # idem -> task_id

    def create_task(
        self,
        *,
        token: str | None,
        idempotency_key: str | None,
        trace_id: str | None,
        deadline_ms: int | None,
        task_type: str,
        payload: dict,
        now_ms: int | None = None,
    ) -> Task:
        now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
        if not token:
            raise PermissionError("missing_identity")
        if not idempotency_key:
            raise PermissionError("missing_idempotency_key")
        if deadline_ms is None:
            raise PermissionError("missing_deadline")
        claims = verify(token)
        tenant = claims["tenant_id"]
        if not idempotency_key.startswith(f"{tenant}:"):
            raise PermissionError("idempotency_tenant_mismatch")

        if idempotency_key in self.by_idem:
            return self.tasks[self.by_idem[idempotency_key]]

        tid = str(uuid.uuid4())[:8]
        task = Task(
            id=tid,
            tenant_id=tenant,
            idempotency_key=idempotency_key,
            trace_id=trace_id or "",
            deadline_ms=deadline_ms,
            task_type=task_type,
            payload=payload,
        )
        self.tasks[tid] = task
        self.by_idem[idempotency_key] = tid
        return task

    def run_task(self, task_id: str, *, now_ms: int | None = None) -> Task:
        now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
        task = self.tasks[task_id]
        if task.status == "cancelled":
            return task
        if task.status == "done":
            return task
        if now_ms > task.deadline_ms:
            task.status = "cancelled"
            return task
        task.status = "running"
        # side effect only if not past deadline
        task.side_effect_count += 1
        task.result = {"echo": task.payload, "tenant": task.tenant_id}
        task.status = "done"
        return task

    def cancel(self, task_id: str, *, token: str) -> Task:
        claims = verify(token)
        task = self.tasks[task_id]
        if claims["tenant_id"] != task.tenant_id:
            raise PermissionError("cross_tenant_cancel")
        if task.status not in ("done",):
            task.status = "cancelled"
        return task
