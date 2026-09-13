"""Mock domain API (stands in for Java 领域服务). Idempotent by key."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TicketAPI:
    """Simulates Java domain service: NOT called from Signal body directly."""

    by_idem: dict[str, str] = field(default_factory=dict)
    create_calls: int = 0
    # fault: if True, pretend Worker held superuser DB and wrote around API
    bypass_domain_api: bool = False
    illicit_db_writes: int = 0

    def create_ticket(self, *, idempotency_key: str, title: str, amount: int) -> str:
        if self.bypass_domain_api:
            self.illicit_db_writes += 1
            raise RuntimeError("hangup:worker_superuser_db_bypass")
        self.create_calls += 1
        if idempotency_key in self.by_idem:
            return self.by_idem[idempotency_key]
        ref = f"TCK-{len(self.by_idem) + 1}"
        self.by_idem[idempotency_key] = ref
        return ref
