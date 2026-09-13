"""
Lesson 14 — Trace + 黄金评测集（作品化闭环）

做三件事：
1) 跑一批固定问题（eval set）
2) 每次 run 写 trace JSON（可审计）
3) 用简单规则打分：是否拒答 / 是否命中关键词 / 是否引用

这不是学术 SOTA 评测，但是简历里能讲清的工程闭环。
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from openai import OpenAI

api_key = os.environ.get("AGENTROUTER_API_KEY")
base_url = os.environ.get("AGENTROUTER_BASE_URL", "https://agentrouter.org/v1")
model = os.environ.get("AGENTROUTER_MODEL", "deepseek-v4-flash")
if not api_key:
    raise SystemExit("缺少环境变量 AGENTROUTER_API_KEY")

client = OpenAI(api_key=api_key, base_url=base_url)
ROOT = Path(__file__).resolve().parent
KB_DIR = ROOT.parent / "lesson07" / "kb"
EVAL_PATH = ROOT / "eval_sets" / "golden.jsonl"
TRACE_DIR = ROOT / "traces"
TRACE_DIR.mkdir(exist_ok=True)


@dataclass
class Chunk:
    source: str
    text: str
    chunk_id: str


@dataclass
class Trace:
    run_id: str
    question: str
    spans: list[dict] = field(default_factory=list)
    t0: float = field(default_factory=time.time)

    def span(self, kind: str, **fields):
        item = {"kind": kind, "ts": time.time(), **fields}
        self.spans.append(item)
        print(f"[trace {self.run_id}] {kind} {fields}")
        return item

    def save(self, answer: str, scores: dict) -> Path:
        path = TRACE_DIR / f"{self.run_id}.json"
        payload = {
            "run_id": self.run_id,
            "question": self.question,
            "answer": answer,
            "scores": scores,
            "duration_ms": int((time.time() - self.t0) * 1000),
            "spans": self.spans,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[trace {self.run_id}] wrote {path}")
        return path


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[\u4e00-\u9fff]{1,}|[a-zA-Z0-9_]+", text.lower()))


def load_chunks() -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(KB_DIR.glob("*.md")):
        raw = path.read_text(encoding="utf-8").strip()
        parts = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
        buf, idx = "", 0
        for part in parts:
            if len(buf) + len(part) < 80:
                buf = (buf + "\n\n" + part).strip()
                continue
            if buf:
                chunks.append(Chunk(path.name, buf, f"{path.stem}-{idx}"))
                idx += 1
            buf = part
        if buf:
            chunks.append(Chunk(path.name, buf, f"{path.stem}-{idx}"))
    return chunks


CHUNKS = load_chunks()


def retrieve(query: str, top_k: int = 3):
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
    return scored[:top_k]


def generate(question: str, hits, tr: Trace) -> str:
    if not hits:
        evidence = "(无检索结果)"
    else:
        evidence = "\n\n".join(
            f"[{i}] {ch.chunk_id} ({ch.source}) score={score:.2f}\n{ch.text}"
            for i, (score, ch) in enumerate(hits, 1)
        )
    messages = [
        {
            "role": "system",
            "content": (
                "你是企业知识助手。只能依据证据回答；不足就明确说不知道。"
                "有证据时在末尾给出引用编号如 [1][2]。"
            ),
        },
        {"role": "user", "content": f"问题：{question}\n\n证据：\n{evidence}"},
    ]
    t0 = time.time()
    resp = client.chat.completions.create(model=model, messages=messages, temperature=0.1)
    latency = int((time.time() - t0) * 1000)
    answer = resp.choices[0].message.content or ""
    tr.span("llm", latency_ms=latency, messages_len=len(messages))
    return answer


def score_answer(case: dict, answer: str, hit_ids: list[str]) -> dict:
    """极简规则分：可解释，适合工程验收。"""
    ans = answer or ""
    expect_refuse = bool(case.get("expect_refuse"))
    must_include = case.get("must_include", [])
    refuse_hit = any(x in ans for x in ["不知道", "没有足够证据", "无法回答", "无足够"])

    if expect_refuse:
        ok = refuse_hit and not any(k in ans for k in ["10 天", "10天", "年假"])
        return {
            "pass": ok,
            "type": "refuse",
            "refuse_hit": refuse_hit,
            "detail": "应拒答且不编造年假政策",
        }

    missing = [k for k in must_include if k not in ans]
    has_cite = bool(re.search(r"\[\d+\]", ans))
    ok = (not missing) and has_cite and (not refuse_hit)
    return {
        "pass": ok,
        "type": "answer",
        "missing": missing,
        "has_cite": has_cite,
        "hit_ids": hit_ids,
        "detail": "应覆盖关键点并带引用",
    }


def run_case(case: dict) -> dict:
    q = case["question"]
    run_id = uuid.uuid4().hex[:8]
    tr = Trace(run_id=run_id, question=q)

    t0 = time.time()
    hits = retrieve(q, top_k=3)
    tr.span(
        "retrieve",
        latency_ms=int((time.time() - t0) * 1000),
        hit_ids=[c.chunk_id for _, c in hits],
    )

    answer = generate(q, hits, tr)
    scores = score_answer(case, answer, [c.chunk_id for _, c in hits])
    tr.span("eval", **scores)
    path = tr.save(answer, scores)
    return {
        "id": case.get("id"),
        "pass": scores["pass"],
        "scores": scores,
        "answer": answer,
        "trace": str(path),
    }


def main() -> None:
    cases = []
    for line in EVAL_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            cases.append(json.loads(line))

    print(f"eval cases={len(cases)} kb_chunks={len(CHUNKS)}")
    results = [run_case(c) for c in cases]
    passed = sum(1 for r in results if r["pass"])
    report = {
        "total": len(results),
        "passed": passed,
        "pass_rate": round(passed / max(len(results), 1), 4),
        "results": results,
    }
    out = ROOT / "eval_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n==== SUMMARY ====")
    print(json.dumps({"total": report["total"], "passed": passed, "pass_rate": report["pass_rate"]}, ensure_ascii=False))
    print(f"report => {out}")


if __name__ == "__main__":
    main()
