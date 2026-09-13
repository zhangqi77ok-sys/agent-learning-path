"""Chunk markdown KB and build a local lexical index (no remote embedding required)."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Chunk:
    chunk_id: str
    source: str
    text: str


_TOKEN = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Mix word tokens + CJK unigrams/bigrams for Chinese lexical recall."""
    toks: list[str] = []
    for t in _TOKEN.findall(text):
        t = t.lower()
        if any("\u4e00" <= ch <= "\u9fff" for ch in t):
            chars = list(t)
            toks.extend(chars)
            toks.extend(chars[i] + chars[i + 1] for i in range(len(chars) - 1))
        else:
            toks.append(t)
    return toks


def chunk_markdown(path: Path, *, max_chars: int = 180) -> list[Chunk]:
    raw = path.read_text(encoding="utf-8").strip()
    parts = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
    chunks: list[Chunk] = []
    n = 0
    for part in parts:
        buf = part
        while buf:
            piece = buf[:max_chars]
            buf = buf[max_chars:]
            n += 1
            chunks.append(Chunk(chunk_id=f"{path.stem}-{n}", source=path.name, text=piece))
    return chunks


class LexicalIndex:
    """TF-IDF cosine — stand-in until embedding API is available."""

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.docs = [tokenize(c.text) for c in chunks]
        df: dict[str, int] = {}
        for toks in self.docs:
            for t in set(toks):
                df[t] = df.get(t, 0) + 1
        self.n = len(self.docs) or 1
        self.idf = {t: math.log((1 + self.n) / (1 + c)) + 1.0 for t, c in df.items()}
        self.vecs = [self._tfidf(toks) for toks in self.docs]

    def _tfidf(self, toks: list[str]) -> dict[str, float]:
        tf: dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        denom = len(toks) or 1
        return {t: (tf[t] / denom) * self.idf.get(t, 0.0) for t in tf}

    @staticmethod
    def _cos(a: dict[str, float], b: dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        keys = set(a) | set(b)
        dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
        na = math.sqrt(sum(v * v for v in a.values())) or 1.0
        nb = math.sqrt(sum(v * v for v in b.values())) or 1.0
        return dot / (na * nb)

    def search(self, query: str, *, top_k: int = 3) -> list[tuple[Chunk, float]]:
        qv = self._tfidf(tokenize(query))
        scored = [(ch, self._cos(qv, self.vecs[i])) for i, ch in enumerate(self.chunks)]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


def load_kb(kb_dir: Path) -> LexicalIndex:
    chunks: list[Chunk] = []
    for path in sorted(kb_dir.glob("*.md")):
        chunks.extend(chunk_markdown(path))
    return LexicalIndex(chunks)
