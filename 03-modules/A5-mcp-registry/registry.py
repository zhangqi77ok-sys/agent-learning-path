"""Tool Registry: pinned version + schema fingerprint + change review. MCP is discovery, not security."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable


def schema_fingerprint(schema: dict[str, Any]) -> str:
    blob = json.dumps(schema, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


@dataclass
class ToolRecord:
    name: str
    version: str
    schema: dict[str, Any]
    fingerprint: str
    risk: str  # low|high
    tenant_allowlist: set[str]
    reviewed: bool
    description: str
    handler: Callable[[dict[str, Any]], str]


@dataclass
class Registry:
    tools: dict[str, ToolRecord] = field(default_factory=dict)

    def register(self, rec: ToolRecord) -> None:
        if not rec.reviewed:
            raise PermissionError("unreviewed_tool")
        expected = schema_fingerprint(rec.schema)
        if rec.fingerprint != expected:
            raise PermissionError("fingerprint_mismatch_on_register")
        self.tools[f"{rec.name}@{rec.version}"] = rec

    def resolve(
        self,
        name: str,
        *,
        pinned_version: str,
        tenant_id: str,
        presented_schema: dict[str, Any] | None = None,
        presented_description: str | None = None,
    ) -> ToolRecord:
        key = f"{name}@{pinned_version}"
        if key not in self.tools:
            raise PermissionError("tool_version_not_pinned")
        rec = self.tools[key]
        if tenant_id not in rec.tenant_allowlist:
            raise PermissionError("tenant_not_allowlisted")
        if presented_schema is not None:
            fp = schema_fingerprint(presented_schema)
            if fp != rec.fingerprint:
                raise PermissionError("schema_fingerprint_mismatch")  # silent schema change
        if presented_description is not None and presented_description != rec.description:
            raise PermissionError("description_tamper")  # tool poisoning
        return rec
