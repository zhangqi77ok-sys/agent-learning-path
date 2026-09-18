"""Queue workers: claim with lease, respect tenant pool, handle gateway faults."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable

from pools import PoolManager
from queue import JobQueue


@dataclass
class LatencyRecorder:
    by_tenant: dict[str, list[float]] = field(default_factory=dict)

    def add(self, tenant_id: str, ms: float) -> None:
        self.by_tenant.setdefault(tenant_id, []).append(ms)

    def p95(self, tenant_id: str) -> float:
        xs = sorted(self.by_tenant.get(tenant_id, []))
        if not xs:
            return 0.0
        idx = min(len(xs) - 1, int(round(0.95 * (len(xs) - 1))))
        return xs[idx]


class ModelGatewayStub:
    def __init__(self) -> None:
        self.all_503 = False

    def call(self, payload: dict) -> str:
        if self.all_503:
            raise RuntimeError("gateway_503")
        # simulate work
        time.sleep(payload.get("sleep_s", 0.01))
        return f"ok:{payload.get('q', '')}"


@dataclass
class Worker:
    worker_id: str
    queue: JobQueue
    pools: PoolManager
    gateway: ModelGatewayStub
    latencies: LatencyRecorder
    stop: threading.Event = field(default_factory=threading.Event)
    processed: int = 0

    def run_once(self) -> bool:
        job = self.queue.claim(self.worker_id)
        if not job:
            return False
        pool = self.pools.pool_for(job.tenant_id)
        if not pool.try_acquire():
            # backpressure: release lease without completing → retry later
            with self.queue.lock:
                job.lease_owner = None
                job.lease_until = None
            return True
        t0 = time.time()
        try:
            result = self.gateway.call(job.payload)
            self.queue.complete(job.id, self.worker_id, result)
            self.processed += 1
            self.latencies.add(job.tenant_id, (time.time() - t0) * 1000)
        except Exception as e:  # noqa: BLE001
            self.queue.fail(job.id, self.worker_id, str(e))
            self.latencies.add(job.tenant_id, (time.time() - t0) * 1000)
        finally:
            pool.release()
        return True

    def loop(self, idle_sleep: float = 0.005) -> None:
        while not self.stop.is_set():
            if not self.run_once():
                time.sleep(idle_sleep)
