"""Agent tool gateway: resolve via Registry, execute in sandbox when needed."""

from __future__ import annotations

from typing import Any

from registry import Registry, ToolRecord, schema_fingerprint
from sandbox import Sandbox


class ToolGateway:
    def __init__(self, registry: Registry, sandbox: Sandbox):
        self.registry = registry
        self.sandbox = sandbox

    def call(
        self,
        *,
        name: str,
        pinned_version: str,
        tenant_id: str,
        args: dict[str, Any],
        presented_schema: dict[str, Any] | None = None,
        presented_description: str | None = None,
    ) -> str:
        rec = self.registry.resolve(
            name,
            pinned_version=pinned_version,
            tenant_id=tenant_id,
            presented_schema=presented_schema,
            presented_description=presented_description,
        )
        # basic arg check against required
        required = rec.schema.get("required", [])
        for k in required:
            if k not in args:
                raise ValueError(f"missing_arg:{k}")
        if rec.schema.get("additionalProperties") is False:
            allowed = set(rec.schema.get("properties", {}))
            extra = set(args) - allowed
            if extra:
                raise ValueError(f"extra_args:{sorted(extra)}")
        return rec.handler(args)
