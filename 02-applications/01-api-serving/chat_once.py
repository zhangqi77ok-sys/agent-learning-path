"""Minimal one-shot Chat Completions call with latency + token printout."""

from __future__ import annotations

import time

from openai import OpenAI

from client_config import load_config


def main() -> None:
    cfg = load_config()
    client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)

    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=cfg.model,
        messages=[
            {"role": "system", "content": "你是简洁的助教，用中文回答。"},
            {"role": "user", "content": "用一句话解释什么是 AI Agent。"},
        ],
        temperature=0.2,
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000

    print(resp.choices[0].message.content)
    print("---")
    print("base_url:", cfg.base_url)
    print("requested_model:", cfg.model)
    print("response_model:", resp.model)
    print(f"latency_ms: {elapsed_ms:.1f}")
    if resp.usage:
        print(
            "tokens:",
            f"prompt={resp.usage.prompt_tokens}",
            f"completion={resp.usage.completion_tokens}",
            f"total={resp.usage.total_tokens}",
        )


if __name__ == "__main__":
    main()
