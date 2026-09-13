"""Durable-ish in-memory queue with lease (stands in for Redis/PG SKIP LOCKED)."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Job:
    id: str
    tenant_id: str
    payload: dict[str, Any]
    enqueued_at: float
    lease_owner: str | None = None
    lease_until: float | None = None
    done: bool = False
    result: Any = None
    error: str | None = None


@dataclass
class JobQueue:
    """Single logical queue; lease prevents double-processing across workers."""

    lease_ms: float = 2000
    jobs: dict[str, Job] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)
    pg_paused: bool = False  # fault injection: SPOF PG down
    depth_samples: list[int] = field(default_factory=list)

    def enqueue(self, tenant_id: str, payload: dict[str, Any]) -> str:
        if self.pg_paused:
            raise RuntimeError("pg_unavailable")
        jid = str(uuid.uuid4())[:8]
        job = Job(id=jid, tenant_id=tenant_id, payload=payload, enqueued_at=time.time())
        with self.lock:
            self.jobs[jid] = job
            self.order.append(jid)
            self.depth_samples.append(self._pending_unlocked())
        return jid

    def _pending_unlocked(self) -> int:
        return sum(1 for j in self.jobs.values() if not j.done and j.lease_owner is None)

    def depth(self) -> int:
        with self.lock:
            return self._pending_unlocked()

    def claim(self, worker_id: str, now: float | None = None) -> Job | None:
        if self.pg_paused:
            return None
        now = now if now is not None else time.time()
        with self.lock:
            for jid in self.order:
                job = self.jobs[jid]
                if job.done:
                    continue
                if job.lease_owner and job.lease_until and job.lease_until > now:
                    continue
                # expired or free
                job.lease_owner = worker_id
                job.lease_until = now + self.lease_ms / 1000.0
                return job
        return None

    def complete(self, job_id: str, worker_id: str, result: Any) -> None:
        with self.lock:
            job = self.jobs[job_id]
            if job.lease_owner != worker_id:
                raise PermissionError("lease_stolen")
            job.done = True
            job.result = result
            job.lease_owner = None

    def fail(self, job_id: str, worker_id: str, error: str) -> None:
        with self.lock:
            job = self.jobs[job_id]
            if job.lease_owner != worker_id:
                raise PermissionError("lease_stolen")
            job.done = True
            job.error = error
            job.lease_owner = None
