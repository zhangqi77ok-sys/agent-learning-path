"""
Lesson 08 — Embedding 向量检索 RAG

对比 Lesson 07 的关键词重叠检索：
- 同一套 KB / chunk
- 同一套回答 Prompt
- 检索改为：Embedding + 余弦相似度

依赖：openai（OpenAI 兼容 embeddings 接口）
环境变量：
  AGENTROUTER_API_KEY
  AGENTROUTER_BASE_URL=https://agentrouter.org/v1
  AGENTROUTER_MODEL=deepseek-v4-flash          # 聊天模型
  AGENTROUTER_EMBED_MODEL=text-embedding-3-small  # 可按网关实际模型名改
"""

from __future__ import annotations

import math
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

api_key = os.environ.get("AGENTROUTER_API_KEY")
base_url = os.environ.get("AGENTROUTER_BASE_URL", "https://agentrouter.org/v1")
chat_model = os.environ.get("AGENTROUTER_MODEL", "deepseek-v4-flash")
embed_model = os.environ.get("AGENTROUTER_EMBED_MODEL", "text-embedding-3-small")

if not api_key:
    raise SystemExit("缺少环境变量 AGENTROUTER_API_KEY")

client = OpenAI(api_key=api_key, base_url=base_url)
KB_DIR = Path(__file__).resolve().parent.parent / "lesson07" / "kb"


@dataclass
class Chunk:
    source: str
    text: str
    chunk_id: str
    embedding: list[float] | None = None


def tokenize(text: str) -> set[str]:
    parts = re.findall(r"[\u4e00-\u9fff]{1,}|[a-zA-Z0-9_]+", text.lower())
    return set(parts)


def load_chunks(kb_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(kb_dir.glob("*.md")):
        raw = path.read_text(encoding="utf-8").strip()
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


def keyword_retrieve(query: str, chunks: list[Chunk], top_k: int = 3):
    q = tokenize(query)
    scored = []
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


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def embed_texts(texts: list[str]) -> list[list[float]]:
    # 兼容一次性多条；若网关不支持 batch，可改成循环单条
    resp = client.embeddings.create(model=embed_model, input=texts)
    # 按 index 排序，防止乱序
    data = sorted(resp.data, key=lambda d: d.index)
    return [d.embedding for d in data]


def ensure_chunk_embeddings(chunks: list[Chunk]) -> None:
    missing = [c for c in chunks if c.embedding is None]
    if not missing:
        return
    vectors = embed_texts([c.text for c in missing])
    for c, v in zip(missing, vectors):
        c.embedding = v


def vector_retrieve(query: str, chunks: list[Chunk], top_k: int = 3):
    ensure_chunk_embeddings(chunks)
    qv = embed_texts([query])[0]
    scored = [(ch, cosine(qv, ch.embedding or [])) for ch in chunks]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


def answer(query: str, hits) -> str:
    evidence = []
    for i, (ch, score) in enumerate(hits, 1):
        evidence.append(
            f"[{i}] source={ch.source} id={ch.chunk_id} score={score:.4f}\n{ch.text}"
        )
    context = "\n\n".join(evidence) if evidence else "(无检索结果)"
    messages = [
        {
            "role": "system",
            "content": (
                "你是企业知识助手。只能依据给定证据回答；"
                "证据不足就明确说不知道。回答末尾列出引用编号，如 [1][2]。"
            ),
        },
        {"role": "user", "content": f"问题：{query}\n\n证据：\n{context}"},
    ]
    resp = client.chat.completions.create(model=chat_model, messages=messages, temperature=0.1)
    return resp.choices[0].message.content or ""


def show_hits(title: str, hits) -> None:
    print(title)
    for ch, score in hits:
        print(f"  - {ch.chunk_id} ({ch.source}) score={score:.4f}")


def main() -> None:
    if not KB_DIR.exists():
        raise SystemExit(f"找不到知识库目录: {KB_DIR}")

    chunks = load_chunks(KB_DIR)
    print(f"KB={KB_DIR}")
    print(f"chunks={len(chunks)} chat_model={chat_model} embed_model={embed_model}")

    # 选一个「同义改写」问题，更容易看出向量检索优势
    demos = [
        "员工一年能休几天假？要怎么提申请？",  # 同义改写年假 FAQ
        "检索增强生成大概怎么走一遍流程？",  # 同义改写 RAG
        "火星上的年假政策是什么？",
    ]

    for q in demos:
        print("\n" + "=" * 64)
        print("问题:", q)
        try:
            kw = keyword_retrieve(q, chunks, top_k=3)
            show_hits("关键词检索:", kw)
        except Exception as e:
            print("关键词检索失败:", e)
            kw = []

        try:
            vec = vector_retrieve(q, chunks, top_k=3)
            show_hits("向量检索:", vec)
            print("向量检索回答:")
            print(answer(q, vec))
        except Exception as e:
            print("向量检索失败:", e)
            print(
                "提示：若报 model_not_found，请设置 AGENTROUTER_EMBED_MODEL 为网关支持的嵌入模型名。"
            )
            print("关键词检索回答（回退）:")
            print(answer(q, kw))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("运行失败:", e, file=sys.stderr)
        raise
