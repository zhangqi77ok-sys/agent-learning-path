"""
Lesson 07 — 最小 RAG（无向量库版）

教学重点：
1) 文档切分
2) 用简单关键词重叠做检索（先建立心智，不引入重依赖）
3) 把 TopK 片段塞进 messages，要求模型基于证据回答并引用

后续课再升级：Embedding + 向量库 + 混合检索 + Rerank。
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

api_key = os.environ.get("AGENTROUTER_API_KEY")
base_url = os.environ.get("AGENTROUTER_BASE_URL", "https://agentrouter.org/v1")
model = os.environ.get("AGENTROUTER_MODEL", "deepseek-v4-flash")
if not api_key:
    raise SystemExit("缺少环境变量 AGENTROUTER_API_KEY")

client = OpenAI(api_key=api_key, base_url=base_url)
KB_DIR = Path(__file__).resolve().parent / "kb"


@dataclass
class Chunk:
    source: str
    text: str
    chunk_id: str


def tokenize(text: str) -> set[str]:
    # 中英粗糙分词：够用做教学检索
    parts = re.findall(r"[\u4e00-\u9fff]{1,}|[a-zA-Z0-9_]+", text.lower())
    return set(parts)


def load_chunks(kb_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(kb_dir.glob("*.md")):
        raw = path.read_text(encoding="utf-8").strip()
        # 按空行切段；太短的并到下一段
        parts = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
        buf = ""
        idx = 0
        for part in parts:
            if len(buf) + len(part) < 80:
                buf = (buf + "\n\n" + part).strip()
                continue
            if buf:
                chunks.append(Chunk(source=path.name, text=buf, chunk_id=f"{path.stem}-{idx}"))
                idx += 1
            buf = part
        if buf:
            chunks.append(Chunk(source=path.name, text=buf, chunk_id=f"{path.stem}-{idx}"))
    return chunks


def retrieve(query: str, chunks: list[Chunk], top_k: int = 3) -> list[tuple[Chunk, float]]:
    q = tokenize(query)
    scored: list[tuple[Chunk, float]] = []
    for ch in chunks:
        t = tokenize(ch.text)
        if not q or not t:
            continue
        overlap = len(q & t)
        score = overlap / (len(q) ** 0.5)
        if score > 0:
            scored.append((ch, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def answer(query: str, hits: list[tuple[Chunk, float]]) -> str:
    evidence = []
    for i, (ch, score) in enumerate(hits, 1):
        evidence.append(
            f"[{i}] source={ch.source} id={ch.chunk_id} score={score:.2f}\n{ch.text}"
        )
    context = "\n\n".join(evidence) if evidence else "(无检索结果)"

    messages = [
        {
            "role": "system",
            "content": (
                "你是企业知识助手。只能依据给定证据回答；"
                "证据不足就明确说不知道。"
                "回答末尾列出引用编号，如 [1][2]。"
            ),
        },
        {
            "role": "user",
            "content": f"问题：{query}\n\n证据：\n{context}",
        },
    ]
    resp = client.chat.completions.create(model=model, messages=messages, temperature=0.1)
    return resp.choices[0].message.content or ""


def main() -> None:
    chunks = load_chunks(KB_DIR)
    print(f"已加载 {len(chunks)} 个 chunk，来自 {KB_DIR}")

    demos = [
        "带薪年假有几天？怎么申请？",
        "RAG 的典型链路是什么？",
        "Agent 和普通聊天机器人有什么区别？",
        "火星上的年假政策是什么？",  # 应回答不知道
    ]

    for q in demos:
        print("\n" + "=" * 60)
        print("问题:", q)
        hits = retrieve(q, chunks, top_k=3)
        print("检索:")
        for ch, score in hits:
            print(f"  - {ch.chunk_id} ({ch.source}) score={score:.2f}")
        print("回答:")
        print(answer(q, hits))


if __name__ == "__main__":
    main()
