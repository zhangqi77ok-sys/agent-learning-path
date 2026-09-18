"""
Lesson 10 — RAG 工具化：KB_SEARCH 进入 Agent Loop

此前 RAG 是「脚本先检索再生成」。
本课改成真正的 Agent：
  模型自己决定何时调用 KB_SEARCH → 你执行检索 → role=tool 回灌 → 模型给最终答案

检索实现沿用 Lesson 07 的关键词方案（少依赖、本机一定能跑）。
你后续可把 retrieve() 换成 hybrid/embedding，而不改 Agent 循环。
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

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


def kb_search(query: str, top_k: int = 3) -> str:
    q = tokenize(query)
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
    hits = scored[:top_k]
    if not hits:
        return json.dumps({"query": query, "hits": [], "note": "无命中"}, ensure_ascii=False)
    payload = {
        "query": query,
        "hits": [
            {
                "rank": i,
                "score": round(score, 4),
                "source": ch.source,
                "chunk_id": ch.chunk_id,
                "text": ch.text,
            }
            for i, (score, ch) in enumerate(hits, 1)
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def finish(answer: str) -> str:
    return json.dumps({"ok": True, "answer": answer}, ensure_ascii=False)


TOOL_IMPL = {
    "KB_SEARCH": lambda a: kb_search(a["query"], int(a.get("top_k", 3))),
    "finish": lambda a: finish(a["answer"]),
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "KB_SEARCH",
            "description": "从公司知识库检索相关片段。回答制度/概念问题前应先检索。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索查询词"},
                    "top_k": {"type": "integer", "description": "返回条数，默认 3"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "提交最终中文答案。必须基于工具证据；没有证据就说不知道。",
            "parameters": {
                "type": "object",
                "properties": {"answer": {"type": "string"}},
                "required": ["answer"],
            },
        },
    },
]


def run_agent(user_text: str, max_steps: int = 6) -> dict:
    messages = [
        {
            "role": "system",
            "content": (
                "你是企业知识助手。"
                "涉及知识库内容时先调用 KB_SEARCH，再基于工具结果回答。"
                "最终必须调用 finish(answer=...)。"
                "没有证据时 answer 里明确说不知道，禁止编造。"
            ),
        },
        {"role": "user", "content": user_text},
    ]
    trace = []

    for step in range(1, max_steps + 1):
        t0 = time.time()
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        latency_ms = int((time.time() - t0) * 1000)
        msg = resp.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            final = msg.content or ""
            print(f"[step {step}] stop=no_tool_calls latency={latency_ms}ms")
            print("最终:", final)
            return {"stop_reason": "no_tool_calls", "final": final, "trace": trace}

        finished = None
        for call in msg.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            print(f"[step {step}] tool={name} args={args} llm_latency={latency_ms}ms")
            try:
                content = TOOL_IMPL[name](args)
            except Exception as e:
                content = json.dumps({"error": str(e)}, ensure_ascii=False)
            print(f"[step {step}] result={content[:240]}...")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": content})
            trace.append({"step": step, "tool": name, "args": args, "content": content})
            if name == "finish":
                finished = json.loads(content)

        if finished is not None:
            final = finished.get("answer", "")
            print(f"[step {step}] stop=finish_tool")
            print("最终:", final)
            return {"stop_reason": "finish_tool", "final": final, "trace": trace}

    return {"stop_reason": "max_steps", "final": "达到 max_steps", "trace": trace}


if __name__ == "__main__":
    print(f"loaded chunks: {len(CHUNKS)} from {KB_DIR}")
    for q in [
        "带薪年假有几天？怎么申请？",
        "Agent 和聊天机器人有什么区别？",
        "火星员工年假怎么休？",
    ]:
        print("\n" + "=" * 64)
        print("用户:", q)
        run_agent(q)
