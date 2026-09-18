"""Simple circuit breaker per upstream."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    open_ms: int = 15_000
    failures: int = 0
    opened_at_ms: float | None = None

    def allow(self, now_ms: float) -> bool:
        if self.opened_at_ms is None:
            return True
        if now_ms - self.opened_at_ms >= self.open_ms:
            # half-open: allow one try
            return True
        return False

    def on_success(self) -> None:
        self.failures = 0
        self.opened_at_ms = None

    def on_failure(self, now_ms: float) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.opened_at_ms = now_ms
