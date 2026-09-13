"""Response cache: key MUST include tenant_id + acl_version."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


def cache_key(*, tenant_id: str, acl_version: str, task_class: str, prompt: str) -> str:
    raw = f"{tenant_id}|{acl_version}|{task_class}|{prompt}"
    return hashlib.sha256(raw.encode()).hexdigest()


@dataclass
class TenantCache:
    store: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str) -> Any | None:
        return self.store.get(key)

    def put(self, key: str, value: Any) -> None:
        self.store[key] = value
