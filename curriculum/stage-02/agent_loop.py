"""Hand-written Agent Loop: tools + short-term memory + tool retry."""

from __future__ import annotations

import json
import time
from typing import Any

from openai import OpenAI

from client_config import load_config
from tools import DISPATCH, NON_RETRYABLE_PREFIXES, RETRYABLE, TOOL_SPECS, reset_flaky

SYSTEM = (
    "你是任务型助教。需要时间、算术或知识片段时必须调用工具。"
    "不要编造工具结果。用中文简短回答。"
)


def _run_tool(name: str, raw_args: str, *, max_retries: int = 3) -> str:
    try:
        args = json.loads(raw_args or "{}")
    except json.JSONDecodeError:
        return f"ERROR non_retryable: invalid JSON args: {raw_args!r}"

    fn = DISPATCH.get(name)
    if fn is None:
        return f"ERROR non_retryable: unknown tool {name}"

    attempt = 0
    while True:
        attempt += 1
        try:
            return fn(args)
        except Exception as e:
            msg = str(e)
            non_retry = any(msg.startswith(p) or p in msg for p in NON_RETRYABLE_PREFIXES)
            retryable = isinstance(e, RETRYABLE) and not non_retry
            if (not retryable) or attempt > max_retries:
                kind = "non_retryable" if not retryable else "exhausted"
                return f"ERROR {kind}: {name}: {msg}"
            sleep_s = min(2 ** (attempt - 1) * 0.2, 2.0)
            print(f"[retry] {name} attempt={attempt} sleep={sleep_s:.1f}s err={msg}")
            time.sleep(sleep_s)


def run_agent(user_text: str, *, max_steps: int = 8) -> str:
    cfg = load_config()
    client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_text},
    ]

    for step in range(1, max_steps + 1):
        print(f"[step {step}] calling model…")
        resp = client.chat.completions.create(
            model=cfg.model,
            messages=messages,
            tools=TOOL_SPECS,
            tool_choice="auto",
            temperature=0.2,
        )
        msg = resp.choices[0].message
        tool_calls = msg.tool_calls or []
        assistant_msg: dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
        if tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments or "{}",
                    },
                }
                for tc in tool_calls
            ]
        messages.append(assistant_msg)
        if not tool_calls:
            return msg.content or ""
        for tc in tool_calls:
            result = _run_tool(tc.function.name, tc.function.arguments or "{}")
            print(f"[tool] {tc.function.name} -> {result[:120]}")
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    return "ERROR: max_steps reached without final answer"


def main() -> None:
    reset_flaky(2)
    question = (
        "现在UTC几点？另外算一下 (12+8)*3。"
        "再用 flaky_kb 查一下 topic=agent 的说明，然后用三句话总结。"
    )
    t0 = time.perf_counter()
    answer = run_agent(question, max_steps=8)
    ms = (time.perf_counter() - t0) * 1000
    print("---")
    print(answer)
    print("---")
    print(f"latency_ms: {ms:.1f}")
    print("memory_scope: session (messages list in this run only)")


if __name__ == "__main__":
    main()
