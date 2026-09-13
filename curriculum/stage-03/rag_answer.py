"""Retrieve → generate with citations; degrade when evidence is weak."""

from __future__ import annotations

import time
from pathlib import Path

from openai import OpenAI

from chunk_index import load_kb
from client_config import load_config

ROOT = Path(__file__).resolve().parent
KB = ROOT / "kb"
MIN_SCORE = 0.02


def answer(question: str, *, top_k: int = 3) -> str:
    index = load_kb(KB)
    hits = index.search(question, top_k=top_k)
    strong = [(c, s) for c, s in hits if s >= MIN_SCORE]

    print("retrieval:")
    for c, s in hits:
        flag = "KEEP" if s >= MIN_SCORE else "DROP"
        print(f"  [{flag}] {c.chunk_id} score={s:.4f} source={c.source}")

    if not strong:
        return (
            "未找到足够依据，无法可靠回答。"
            "（降级：检索分数均低于阈值，拒绝编造。）"
        )

    context = "\n\n".join(
        f"[{c.chunk_id} | {c.source}] {c.text}" for c, _ in strong
    )
    cfg = load_config()
    client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
    prompt = (
        "只根据给定资料回答，并在句末用 [chunk_id] 标注引用。"
        "资料不足就说不知道，不要编造。\n\n"
        f"资料:\n{context}\n\n问题: {question}"
    )
    resp = client.chat.completions.create(
        model=cfg.model,
        messages=[
            {"role": "system", "content": "你是严谨的知识库助教。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )
    return resp.choices[0].message.content or ""


def main() -> None:
    questions = [
        "什么是 AI Agent？生产环境还要补什么？",
        "什么时候不该上 RAG？",
        "跨城差旅要先做什么？",
        "火星上有没有我们公司的年假政策？",
    ]
    t0 = time.perf_counter()
    for q in questions:
        print("\n===", q)
        print(answer(q))
    print(f"\nlatency_ms_total: {(time.perf_counter()-t0)*1000:.1f}")
    print("index: local TF-IDF (no remote embedding on this relay)")


if __name__ == "__main__":
    main()
