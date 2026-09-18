"""Convert OTEL-like span dump → eval fixture with PII stripped."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

PHONE = re.compile(r"1\d{10}")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
IDCARD = re.compile(r"\b\d{17}[\dXx]\b")


def _redact(text: str) -> str:
    text = PHONE.sub("[PHONE]", text)
    text = EMAIL.sub("[EMAIL]", text)
    text = IDCARD.sub("[ID]", text)
    return text


def _hash_tenant(tenant_id: str) -> str:
    return "t_" + hashlib.sha256(tenant_id.encode()).hexdigest()[:8]


def trace_to_fixture(trace: dict[str, Any]) -> dict[str, Any]:
    """Build a replayable fixture; strip PII; require retrieve.filter when retrieve present."""
    spans = trace.get("spans", [])
    tools: list[str] = []
    retrieve_filter = None
    query = _redact(str(trace.get("query", "")))
    answer = _redact(str(trace.get("answer", "")))
    for s in spans:
        name = s.get("name", "")
        if name.startswith("tool."):
            tools.append(name.split(".", 1)[1])
        if name == "tool.retrieve":
            retrieve_filter = s.get("attributes", {}).get("filter")
    fixture = {
        "id": trace.get("trace_id", "unknown"),
        "query": query,
        "answer": answer,
        "tools": tools,
        "retrieve_filter": retrieve_filter,
        "tenant_hash": _hash_tenant(str(trace.get("tenant_id", ""))),
        "pii_stripped": True,
    }
    if "retrieve" in tools and not retrieve_filter:
        fixture["incomplete"] = "missing_retrieve_filter"
    return fixture


def dump_fixture(fixture: dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(fixture, f, ensure_ascii=False, indent=2)
