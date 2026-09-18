"""Trace → PII-stripped fixture for regression."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

PHONE = re.compile(r"1\d{10}")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def strip_pii(text: str) -> str:
    return EMAIL.sub("[EMAIL]", PHONE.sub("[PHONE]", text))


def trace_to_fixture(trace: dict) -> dict:
    tools = [s["name"].split(".", 1)[1] for s in trace.get("spans", []) if s.get("name", "").startswith("tool.")]
    retrieve_filter = None
    for s in trace.get("spans", []):
        if s.get("name") == "tool.retrieve":
            retrieve_filter = s.get("attributes", {}).get("filter")
    fix = {
        "id": trace.get("trace_id"),
        "query": strip_pii(str(trace.get("query", ""))),
        "tools": tools,
        "retrieve_filter": retrieve_filter,
        "tenant_hash": "t_" + hashlib.sha256(str(trace.get("tenant_id", "")).encode()).hexdigest()[:8],
        "expect_no_tools": trace.get("expect_no_tools", []),
        "pii_stripped": True,
    }
    if "retrieve" in tools and not retrieve_filter:
        fix["incomplete"] = "missing_retrieve_filter"
    return fix


def append_regression(fixture: dict, path: Path) -> None:
    if fixture.get("incomplete"):
        raise PermissionError("incomplete_fixture_blocked")
    path.parent.mkdir(parents=True, exist_ok=True)
    cases = []
    if path.exists():
        cases = json.loads(path.read_text(encoding="utf-8"))
    cases.append(fixture)
    path.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
