"""
Lesson 12 — 条件边 + Multi-Agent 入门

图：
  START → retrieve_agent → route
                              ├─(hits 足够)→ answer_agent → END
                              └─(hits 空)→ refuse → END

两个“Agent”：
- retrieve_agent：只负责检索（本课用关键词函数；也可换成只会检索的 LLM）
- answer_agent：只负责基于证据回答
仍共享一个 GraphState；这是最小可运行的多角色拆分。
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

from openai import OpenAI

api_key = os.environ.get("AGENTROUTER_API_KEY")
base_url = os.environ.get("AGENTROUTER_BASE_URL", "https://agentrouter.org/v1")
model = os.environ.get("AGENTROUTER_MODEL", "deepseek-v4-flash")
if not api_key:
    raise SystemExit("缺少环境变量 AGENTROUTER_API_KEY")

client = OpenAI(api_key=api_key, base_url=base_url)
KB_DIR = Path(__file__).resolve().parent.parent / "lesson07" / "kb"


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
    route: str = ""
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


def node_retrieve_agent(state: GraphState) -> GraphState:
    """检索员：只产出 hits，不写最终答案。"""
    state.trace.append("agent:retrieve")
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
    state.trace.append(f"hits={[h['chunk_id'] for h in state.hits]}")
    return state


def route_after_retrieve(state: GraphState) -> Literal["answer_agent", "refuse"]:
    """条件边：有证据去回答员，否则拒答。"""
    nxt = "answer_agent" if state.hits else "refuse"
    state.route = nxt
    state.trace.append(f"route→{nxt}")
    return nxt


def node_answer_agent(state: GraphState) -> GraphState:
    """回答员：只能基于 hits 说话。"""
    state.trace.append("agent:answer")
    evidence = "\n\n".join(
        f"[{h['rank']}] {h['chunk_id']} ({h['source']})\n{h['text']}" for h in state.hits
    )
    messages = [
        {
            "role": "system",
            "content": (
                "你是回答员 Agent。只能依据检索员提供的证据回答；"
                "禁止使用证据外知识。末尾给引用编号。"
            ),
        },
        {
            "role": "user",
            "content": f"用户问题：{state.question}\n\n检索员证据：\n{evidence}",
        },
    ]
    resp = client.chat.completions.create(model=model, messages=messages, temperature=0.1)
    state.answer = resp.choices[0].message.content or ""
    return state


def node_refuse(state: GraphState) -> GraphState:
    state.trace.append("node:refuse")
    state.answer = "知识库中没有足够证据，我不知道。请换个问法或补充文档。"
    return state


NodeFn = Callable[[GraphState], GraphState]


class StateGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, NodeFn] = {}
        self.fixed_edges: dict[str, str] = {}
        self.conditional: dict[str, Callable[[GraphState], str]] = {}
        self.entry: str | None = None

    def add_node(self, name: str, fn: NodeFn) -> None:
        self.nodes[name] = fn

    def set_entry(self, name: str) -> None:
        self.entry = name

    def add_edge(self, a: str, b: str) -> None:
        self.fixed_edges[a] = b

    def add_conditional_edge(self, a: str, router: Callable[[GraphState], str]) -> None:
        self.conditional[a] = router

    def run(self, state: GraphState, max_hops: int = 12) -> GraphState:
        cur = self.entry
        assert cur
        for _ in range(max_hops):
            if cur == "END":
                state.trace.append("END")
                return state
            print(f"→ {cur}")
            state = self.nodes[cur](state)
            if cur in self.conditional:
                cur = self.conditional[cur](state)
            else:
                cur = self.fixed_edges.get(cur, "END")
        state.trace.append("max_hops")
        return state


def build_graph() -> StateGraph:
    g = StateGraph()
    g.add_node("retrieve_agent", node_retrieve_agent)
    g.add_node("answer_agent", node_answer_agent)
    g.add_node("refuse", node_refuse)
    g.set_entry("retrieve_agent")
    g.add_conditional_edge("retrieve_agent", route_after_retrieve)
    g.add_edge("answer_agent", "END")
    g.add_edge("refuse", "END")
    return g


def main() -> None:
    print("graph: retrieve_agent → (hits? answer_agent : refuse) → END")
    g = build_graph()
    for q in ["带薪年假有几天？怎么申请？", "火星员工怎么报销？"]:
        print("\n" + "=" * 64)
        print("问题:", q)
        st = g.run(GraphState(question=q))
        print("route:", st.route)
        print("trace:", " | ".join(st.trace))
        print("回答:", st.answer)


if __name__ == "__main__":
    main()
