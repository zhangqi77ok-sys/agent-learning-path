"""
Lesson 13 — MCP Server（知识库工具服务）

运行：
  pip install mcp
  python mcp_kb_server.py

这是一个 stdio MCP Server：对外暴露 kb_search 工具。
Agent / Cursor / 其他客户端都可以通过 MCP 协议发现并调用它。
"""

from __future__ import annotations

import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

KB_DIR = Path(__file__).resolve().parent.parent / "08-rag-keyword" / "kb"
mcp = FastMCP("14-mcp-kb")


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[\u4e00-\u9fff]{1,}|[a-zA-Z0-9_]+", text.lower()))


def _load_chunks():
    chunks = []
    for path in sorted(KB_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8").strip()
        parts = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
        buf, idx = "", 0
        for part in parts:
            if len(buf) + len(part) < 80:
                buf = (buf + "\n\n" + part).strip()
                continue
            if buf:
                chunks.append({"source": path.name, "chunk_id": f"{path.stem}-{idx}", "text": buf})
                idx += 1
            buf = part
        if buf:
            chunks.append({"source": path.name, "chunk_id": f"{path.stem}-{idx}", "text": buf})
    return chunks


CHUNKS = _load_chunks()


@mcp.tool()
def kb_search(query: str, top_k: int = 3) -> str:
    """从公司知识库检索相关片段，返回 JSON 字符串。"""
    import json

    q = _tokenize(query)
    scored = []
    for ch in CHUNKS:
        t = _tokenize(ch["text"])
        if not q or not t:
            continue
        overlap = len(q & t)
        score = overlap / (len(q) ** 0.5)
        if score > 0:
            scored.append((score, ch))
    scored.sort(key=lambda x: x[0], reverse=True)
    hits = [
        {
            "rank": i,
            "score": round(score, 4),
            "source": ch["source"],
            "chunk_id": ch["chunk_id"],
            "text": ch["text"],
        }
        for i, (score, ch) in enumerate(scored[:top_k], 1)
    ]
    return json.dumps({"query": query, "hits": hits}, ensure_ascii=False)


if __name__ == "__main__":
    # stdio transport：客户端拉起本进程并管道通信
    mcp.run()
