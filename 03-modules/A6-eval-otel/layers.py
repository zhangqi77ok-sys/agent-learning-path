"""Four-layer eval: Model / Framework / Harness / Application."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class LayerResult:
    layer: str
    passed: bool
    score: float
    details: dict[str, Any] = field(default_factory=dict)
    hard_failures: list[str] = field(default_factory=list)


def eval_model_layer(cases: list[dict], runner: Callable[[dict], dict]) -> LayerResult:
    """Model: answer quality / refusal correctness (no tool policy)."""
    ok = 0
    hard: list[str] = []
    for c in cases:
        out = runner(c)
        if c.get("expect_refuse") and not out.get("refused"):
            hard.append(f"{c['id']}:expected_refuse")
        elif out.get("answer_ok"):
            ok += 1
        else:
            # soft miss
            pass
    n = max(len(cases), 1)
    return LayerResult("Model", passed=not hard, score=ok / n, hard_failures=hard)


def eval_framework_layer(cases: list[dict], runner: Callable[[dict], dict]) -> LayerResult:
    """Framework: tool routing / graph edges (expect_tools)."""
    ok = 0
    hard: list[str] = []
    for c in cases:
        out = runner(c)
        tools = set(out.get("tools", []))
        for t in c.get("expect_tools", []):
            if t not in tools:
                hard.append(f"{c['id']}:missing_tool:{t}")
        for t in c.get("expect_no_tools", []):
            if t in tools:
                hard.append(f"{c['id']}:forbidden_tool:{t}")
        if not any(x.startswith(c["id"]) for x in hard):
            ok += 1
    n = max(len(cases), 1)
    return LayerResult("Framework", passed=not hard, score=ok / n, hard_failures=hard)


def eval_harness_layer(cases: list[dict], runner: Callable[[dict], dict]) -> LayerResult:
    """Harness: budgets, policy, circuit — cost / max steps."""
    ok = 0
    hard: list[str] = []
    for c in cases:
        out = runner(c)
        tokens = int(out.get("tokens", 0))
        if tokens > 8000:
            hard.append(f"{c['id']}:cost_budget")
        if out.get("policy_violation"):
            hard.append(f"{c['id']}:policy")
        if not any(x.startswith(c["id"]) for x in hard):
            ok += 1
    n = max(len(cases), 1)
    return LayerResult("Harness", passed=not hard, score=ok / n, hard_failures=hard)


def eval_application_layer(cases: list[dict], runner: Callable[[dict], dict]) -> LayerResult:
    """Application: citations, tenant filter present on retrieve, business SLO."""
    ok = 0
    hard: list[str] = []
    for c in cases:
        out = runner(c)
        if "retrieve" in out.get("tools", []) and not out.get("retrieve_filter"):
            hard.append(f"{c['id']}:missing_retrieve_filter")
        if c.get("expect_cite") and not out.get("cited"):
            hard.append(f"{c['id']}:missing_cite")
        if not any(x.startswith(c["id"]) for x in hard):
            ok += 1
    n = max(len(cases), 1)
    return LayerResult("Application", passed=not hard, score=ok / n, hard_failures=hard)
