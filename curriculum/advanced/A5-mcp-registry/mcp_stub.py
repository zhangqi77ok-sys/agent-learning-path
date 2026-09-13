"""Minimal MCP-like tool advertisement (description+schema). Not a security boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class McpAdvertisement:
    name: str
    version: str
    description: str
    schema: dict[str, Any]


def advertise_write_note(version: str = "1.0.0") -> McpAdvertisement:
    return McpAdvertisement(
        name="write_note",
        version=version,
        description="Write a short note into the sandbox workspace.",
        schema={
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
            "additionalProperties": False,
        },
    )


def advertise_export_all(version: str = "1.0.0") -> McpAdvertisement:
    return McpAdvertisement(
        name="export_all",
        version=version,
        description="Export all tenant data.",  # high risk
        schema={"type": "object", "properties": {}, "additionalProperties": False},
    )
