"""A1 fault-injection demos: infinite tools, allowlist, budget."""

from __future__ import annotations

import time

from executors import FiniteTaskExecutor, ForbiddenToolExecutor, InfiniteToolExecutor
from harness import Budget, Harness, ToolCall


def noop_tool(call: ToolCall) -> str:
    time.sleep(0.01)
    return f"ok:{call.name}"


def main() -> None:
    tools = {"noop": noop_tool}

    print("=== demo1: happy path ===")
    h = Harness(Budget(max_steps=8, max_wall_ms=30000, max_tool_calls=16), tools, FiniteTaskExecutor(2), allowlist={"noop"})
    s = h.start_run(tenant_id="t1", user_id="u1", thread_id="th1")
    h.run_until_done(s)
    print(s.status.value, "steps", s.step, "tools", s.tool_calls, "final", s.final)

    print("=== demo2: infinite same tool -> circuit_open ===")
    h2 = Harness(
        Budget(max_steps=8, max_wall_ms=30000, max_tool_calls=100),
        tools,
        InfiniteToolExecutor("noop", {"x": 1}),
        allowlist={"noop"},
        duplicate_signature_limit=3,
    )
    s2 = h2.start_run(tenant_id="t1", user_id="u1", thread_id="th2")
    t0 = time.time()
    h2.run_until_done(s2)
    dt = (time.time() - t0) * 1000
    print(s2.status.value, "steps", s2.step, "wall_ms", round(dt, 1))
    assert s2.status.value == "circuit_open", s2.status
    assert s2.step <= 8
    print("SLO_ok_circuit:", True)

    print("=== demo3: forbidden tool blocked ===")
    h3 = Harness(Budget(), tools, ForbiddenToolExecutor(), allowlist={"noop"})
    s3 = h3.start_run(tenant_id="t1", user_id="u1", thread_id="th3")
    h3.run_until_done(s3)
    print(s3.status.value, s3.final)

    print("=== demo4: budget max_steps ===")
    # executor keeps going with unique signatures so circuit doesn't trip first
    class UniqueInfinite:
        def propose(self, state):
            return None, [ToolCall("noop", {"n": state.step})]

    h4 = Harness(Budget(max_steps=5, max_wall_ms=30000, max_tool_calls=100), tools, UniqueInfinite(), allowlist={"noop"})
    s4 = h4.start_run(tenant_id="t1", user_id="u1", thread_id="th4")
    h4.run_until_done(s4)
    print(s4.status.value, "steps", s4.step)
    assert s4.status.value == "budget_exceeded"
    # after budget, no further tool spans beyond budget
    tool_events = [e for e in s4.events if e.kind == "tool"]
    print("tool_spans", len(tool_events), "SLO_ok_budget:", len(tool_events) <= 5)

    print("=== replay sample ===")
    print(h2.replay(s2)[:3])


if __name__ == "__main__":
    main()
