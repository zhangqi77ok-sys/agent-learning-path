"""A2A client — never confuse with MCP tool call."""

from __future__ import annotations

from typing import Any

from server.a2a_server import A2AServer, Task


class A2AClient:
    """In-process client for demos; production would be HTTP."""

    def __init__(self, server: A2AServer):
        self.server = server

    def delegate(
        self,
        *,
        token: str,
        idempotency_key: str,
        trace_id: str,
        deadline_ms: int,
        task_type: str,
        payload: dict[str, Any],
        now_ms: int | None = None,
        auto_run: bool = True,
    ) -> Task:
        task = self.server.create_task(
            token=token,
            idempotency_key=idempotency_key,
            trace_id=trace_id,
            deadline_ms=deadline_ms,
            task_type=task_type,
            payload=payload,
            now_ms=now_ms,
        )
        if auto_run and task.status == "pending":
            self.server.run_task(task.id, now_ms=now_ms)
        return task
