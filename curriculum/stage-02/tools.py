"""Demo tools for stage-02 agent loop (incl. a flaky tool for retry drills)."""

from __future__ import annotations

import ast
import operator
from datetime import datetime, timezone
from typing import Any, Callable

_FLAKY_FAILS_LEFT = 2


def reset_flaky(fails: int = 2) -> None:
    global _FLAKY_FAILS_LEFT
    _FLAKY_FAILS_LEFT = fails


def tool_get_now(_: dict[str, Any] | None = None) -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    raise ValueError("only basic arithmetic is allowed")


def tool_calculator(args: dict[str, Any]) -> str:
    expr = str(args.get("expression", "")).strip()
    if not expr:
        raise ValueError("expression is required")
    tree = ast.parse(expr, mode="eval")
    return str(_eval_node(tree))


def tool_flaky_kb(args: dict[str, Any]) -> str:
    global _FLAKY_FAILS_LEFT
    topic = str(args.get("topic", "agent")).strip() or "agent"
    if _FLAKY_FAILS_LEFT > 0:
        _FLAKY_FAILS_LEFT -= 1
        raise TimeoutError(f"kb upstream timeout (remaining_fail_budget={_FLAKY_FAILS_LEFT})")
    return f"KB[{topic}]: Agent = LLM + tools + loop; production needs retries, auth, and eval."


TOOL_SPECS: list[dict[str, Any]] = [
    {"type": "function", "function": {"name": "get_now", "description": "Return current UTC time in ISO-8601.", "parameters": {"type": "object", "properties": {}, "additionalProperties": False}}},
    {"type": "function", "function": {"name": "calculator", "description": "Evaluate a basic arithmetic expression like (3+5)*2.", "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "flaky_kb", "description": "Lookup a short knowledge snippet; may transiently time out.", "parameters": {"type": "object", "properties": {"topic": {"type": "string"}}, "required": ["topic"], "additionalProperties": False}}},
]

DISPATCH: dict[str, Callable[[dict[str, Any]], str]] = {
    "get_now": tool_get_now,
    "calculator": tool_calculator,
    "flaky_kb": tool_flaky_kb,
}

RETRYABLE = (TimeoutError, ConnectionError)
NON_RETRYABLE_PREFIXES = ("only basic arithmetic", "expression is required", "unknown tool")
