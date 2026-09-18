"""Tenant isolation pools + concurrency caps + backpressure."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field


@dataclass
class TenantPool:
    tenant_id: str
    max_inflight: int
    inflight: int = 0
    rejected: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)

    def try_acquire(self) -> bool:
        with self.lock:
            if self.inflight >= self.max_inflight:
                self.rejected += 1
                return False
            self.inflight += 1
            return True

    def release(self) -> None:
        with self.lock:
            self.inflight = max(0, self.inflight - 1)


@dataclass
class PoolManager:
    default_max: int = 2
    pools: dict[str, TenantPool] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def pool_for(self, tenant_id: str, max_inflight: int | None = None) -> TenantPool:
        with self.lock:
            if tenant_id not in self.pools:
                self.pools[tenant_id] = TenantPool(
                    tenant_id, max_inflight if max_inflight is not None else self.default_max
                )
            return self.pools[tenant_id]
