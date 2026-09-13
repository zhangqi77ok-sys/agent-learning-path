#!/usr/bin/env python3
"""Hot-plug Harness demos — all scenarios must print ALL_OK at the end."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hotplug_harness import (  # noqa: E402
    Budget,
    CircuitBreaker,
    Harness,
    load_default,
    load_plugins,
)
from hotplug_harness.loader import discover_py_files  # noqa: E402


def _fresh_registry():
    """Reload plugins so stateful models start clean each scenario."""
    return load_default(ROOT)


def demo_a_happy_path() -> None:
    print("=== a) happy path with plugins ===")
    reg = _fresh_registry()
    model = reg.get_model("scripted_happy")
    assert model is not None, "scripted_happy model missing"
    h = Harness(
        registry=reg,
        model=model,
        budget=Budget(max_steps=8, max_wall_ms=30_000, max_tool_calls=16),
        circuit=CircuitBreaker(3),
        policy_names=("allowlist",),
    )
    s = h.start_run(tenant_id="t1", user_id="u1", thread_id="th-happy")
    h.run_until_done(s)
    print(
        s.status.value,
        "steps",
        s.step,
        "tools",
        s.tool_calls,
        "final",
        s.final,
        "run_id",
        s.run_id[:8],
    )
    assert s.status.value == "succeeded", s.status
    assert s.final == "done"
    assert s.tool_calls == 2
    assert s.tenant_id == "t1" and s.user_id == "u1" and s.thread_id == "th-happy"
    print("OK happy_path")


def demo_b_hotplug_tool() -> None:
    print("=== b) select/load tool from plugins dir (no core change) ===")
    tools_dir = ROOT / "plugins" / "tools"
    discovered = [p.stem for p in discover_py_files(tools_dir)]
    print("discovered_tool_files:", discovered)
    assert "echo" in discovered and "flaky" in discovered

    reg = _fresh_registry()
    print("registry.tools:", sorted(reg.tools))
    assert "echo" in reg.tools and "flaky" in reg.tools
    # Prove hot-plug: drop a *new* tool file into a temp dir and load — zero core edits
    with tempfile.TemporaryDirectory() as td:
        new_tool = Path(td) / "greet.py"
        new_tool.write_text(
            '''
from dataclasses import dataclass
from typing import Any

@dataclass
class GreetTool:
    name: str = "greet"
    def run(self, call: Any, state: Any) -> str:
        return f"hi:{call.args.get("who", "world")}"

def create_tool():
    return GreetTool()
''',
            encoding="utf-8",
        )
        reg2 = load_plugins(tools_dir=td)
        assert "greet" in reg2.tools
        result = reg2.tools["greet"].run(
            type("C", (), {"args": {"who": "maxzq"}, "signature": "greet"})(),
            None,
        )
        print("hotplugged_greet_result:", result)
        assert result == "hi:maxzq"
    print("OK hotplug_tool")


def demo_c_circuit_open() -> None:
    print("=== c) circuit_open on duplicate tool signature ===")
    reg = _fresh_registry()
    model = reg.get_model("infinite_same_tool")
    assert model is not None
    h = Harness(
        registry=reg,
        model=model,
        budget=Budget(max_steps=8, max_wall_ms=30_000, max_tool_calls=100),
        circuit=CircuitBreaker(duplicate_signature_limit=3),
    )
    s = h.start_run(tenant_id="t1", user_id="u1", thread_id="th-circuit")
    h.run_until_done(s)
    print(s.status.value, "steps", s.step, "tool_calls", s.tool_calls)
    assert s.status.value == "circuit_open", s.status
    assert s.step <= 8
    circuit_events = [e for e in s.events if e.kind == "circuit"]
    assert circuit_events, "expected circuit event"
    print("OK circuit_open")


def demo_d_budget_exceeded() -> None:
    print("=== d) budget_exceeded ===")
    reg = _fresh_registry()
    model = reg.get_model("unique_infinite")
    assert model is not None
    h = Harness(
        registry=reg,
        model=model,
        budget=Budget(max_steps=5, max_wall_ms=30_000, max_tool_calls=100),
        circuit=CircuitBreaker(3),
    )
    s = h.start_run(tenant_id="t1", user_id="u1", thread_id="th-budget")
    h.run_until_done(s)
    print(s.status.value, "steps", s.step)
    assert s.status.value == "budget_exceeded", s.status
    tool_events = [e for e in s.events if e.kind == "tool"]
    print("tool_spans", len(tool_events))
    assert len(tool_events) <= 5
    print("OK budget_exceeded")


def demo_e_forbidden_blocked() -> None:
    print("=== e) forbidden tool blocked by policy ===")
    reg = _fresh_registry()
    model = reg.get_model("forbidden_tool")
    assert model is not None
    h = Harness(
        registry=reg,
        model=model,
        budget=Budget(),
        circuit=CircuitBreaker(3),
        policy_names=("allowlist",),
    )
    s = h.start_run(tenant_id="t1", user_id="u1", thread_id="th-policy")
    h.run_until_done(s)
    print(s.status.value, s.final)
    assert s.status.value == "policy_blocked", s.status
    assert "tool_not_allowlisted:drop_db" in s.final
    print("OK policy_blocked")


def main() -> None:
    print("plugin roots:", ROOT / "plugins")
    reg = _fresh_registry()
    print("loaded:", reg.summary())

    demo_a_happy_path()
    demo_b_hotplug_tool()
    demo_c_circuit_open()
    demo_d_budget_exceeded()
    demo_e_forbidden_blocked()

    print("ALL_OK")


if __name__ == "__main__":
    main()
