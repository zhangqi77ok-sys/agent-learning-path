"""
Lesson 11 — 手写状态图 RAG（LangGraph 同款心智）

还不是 Multi-Agent：仍然可以是同一个模型。
关键变化是：流程从「隐式 while」变成「显式节点 + 边」。

图结构：

  START → retrieve → generate → END
              ↑          |
              └─(可选：证据不足再检索，本课先做线性版)

对应 LangGraph：
  StateGraph / Node / Edge / END
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from openai import OpenAI

api_key = os.environ.get("AGENTROUTER_API_KEY")
base_url = os.environ.get("AGENTROUTER_BASE_URL", "https://agentrouter.org/v1")
model = os.environ.get("AGENTROUTER_MODEL", "deepseek-v4-flash")
if not api_key:
    raise SystemExit("缺少环境变量 AGENTROUTER_API_KEY")

client = OpenAI(api_key=api_key, base_url=base_url)
KB_DIR = Path(__file__).resolve().parent.parent / "08-rag-keyword" / "kb"


@dataclass
class Chunk:
    source: str
    text: str
    chunk_id: str


@dataclass
class GraphState:
    question: str
    hits: list[dict[str, Any]] = field(default_factory=list)
    answer: str = ""
    trace: list[str] = field(default_factory=list)


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[\u4e00-\u9fff]{1,}|[a-zA-Z0-9_]+", text.lower()))


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


CHUNKS = load_chunks(KB_DIR)


# ---------- nodes ----------
def node_retrieve(state: GraphState) -> GraphState:
    state.trace.append("enter:retrieve")
    q = tokenize(state.question)
    scored = []
    for ch in CHUNKS:
        t = tokenize(ch.text)
        if not q or not t:
            continue
        overlap = len(q & t)
        score = overlap / (len(q) ** 0.5)
        if score > 0:
            scored.append((score, ch))
    scored.sort(key=lambda x: x[0], reverse=True)
    state.hits = [
        {
            "rank": i,
            "score": round(score, 4),
            "source": ch.source,
            "chunk_id": ch.chunk_id,
            "text": ch.text,
        }
        for i, (score, ch) in enumerate(scored[:3], 1)
    ]
    state.trace.append(f"retrieve_hits={ [h['chunk_id'] for h in state.hits] }")
    return state


def node_generate(state: GraphState) -> GraphState:
    state.trace.append("enter:generate")
    if not state.hits:
        evidence = "(无检索结果)"
    else:
        evidence = "\n\n".join(
            f"[{h['rank']}] {h['chunk_id']} ({h['source']})\n{h['text']}" for h in state.hits
        )
    messages = [
        {
            "role": "system",
            "content": (
                "你是企业知识助手。只能依据证据回答；不足就说不知道。"
                "末尾给出引用编号。"
            ),
        },
        {"role": "user", "content": f"问题：{state.question}\n\n证据：\n{evidence}"},
    ]
    resp = client.chat.completions.create(model=model, messages=messages, temperature=0.1)
    state.answer = resp.choices[0].message.content or ""
    state.trace.append("leave:generate")
    return state


# ---------- tiny graph runtime ----------
NodeFn = Callable[[GraphState], GraphState]


class StateGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, NodeFn] = {}
        self.edges: dict[str, str] = {}
        self.entry: str | None = None

    def add_node(self, name: str, fn: NodeFn) -> None:
        self.nodes[name] = fn

    def set_entry(self, name: str) -> None:
        self.entry = name

    def add_edge(self, a: str, b: str) -> None:
        self.edges[a] = b

    def run(self, state: GraphState, max_hops: int = 10) -> GraphState:
        if not self.entry:
            raise RuntimeError("entry not set")
        cur = self.entry
        for _ in range(max_hops):
            if cur == "END":
                state.trace.append("reach:END")
                return state
            if cur not in self.nodes:
                raise RuntimeError(f"unknown node: {cur}")
            print(f"→ node {cur}")
            state = self.nodes[cur](state)
            cur = self.edges.get(cur, "END")
        state.trace.append("max_hops")
        return state


def build_graph() -> StateGraph:
    g = StateGraph()
    g.add_node("retrieve", node_retrieve)
    g.add_node("generate", node_generate)
    g.set_entry("retrieve")
    g.add_edge("retrieve", "generate")
    g.add_edge("generate", "END")
    return g


def main() -> None:
    print(f"chunks={len(CHUNKS)}")
    print("graph: START → retrieve → generate → END")
    g = build_graph()
    for q in [
        "带薪年假有几天？怎么申请？",
        "火星员工怎么报销？",
    ]:
        print("\n" + "=" * 64)
        print("问题:", q)
        state = g.run(GraphState(question=q))
        print("trace:", " | ".join(state.trace))
        print("hits:", json.dumps([h["chunk_id"] for h in state.hits], ensure_ascii=False))
        print("回答:", state.answer)


if __name__ == "__main__":
    main()
