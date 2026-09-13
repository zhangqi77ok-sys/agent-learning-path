"""Simulated agent runners for fault-injection demos."""

from __future__ import annotations


def good_runner(case: dict) -> dict:
    q = case["query"]
    if case.get("expect_refuse"):
        return {"refused": True, "answer_ok": True, "tools": [], "tokens": 200, "cited": False, "retrieve_filter": None}
    tools = ["retrieve"] if "差旅" in q or "报销" in q or "政策" in q else []
    return {
        "refused": False,
        "answer_ok": True,
        "tools": tools,
        "tokens": 500,
        "cited": bool(case.get("expect_cite")),
        "retrieve_filter": {"tenant_id": "from_token"} if "retrieve" in tools else None,
    }


def dangerous_tool_runner(case: dict) -> dict:
    """Fault: offline quality looks up, but export_all wrongly opens."""
    base = good_runner(case)
    base["tools"] = list(base["tools"]) + ["export_all"]
    base["answer_ok"] = True  # soft score up
    base["tokens"] = 600
    return base


def missing_filter_runner(case: dict) -> dict:
    base = good_runner(case)
    if "retrieve" in base["tools"]:
        base["retrieve_filter"] = None
    return base
