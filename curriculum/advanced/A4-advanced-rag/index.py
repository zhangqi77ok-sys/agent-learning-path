"""Hybrid lexical index with tenant ACL before scoring; blue-green alias switch."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from corpus import CORPUS, DocVersion

_TOKEN = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    toks: list[str] = []
    for t in _TOKEN.findall(text.lower()):
        if any("\u4e00" <= ch <= "\u9fff" for ch in t):
            chars = list(t)
            toks.extend(chars)
            toks.extend(a + b for a, b in zip(chars, chars[1:]))
        else:
            toks.append(t)
    return toks


@dataclass
class Hit:
    doc: DocVersion
    score: float


class Index:
    def __init__(self, docs: list[DocVersion], *, name: str):
        self.name = name
        self.docs = list(docs)
        self._tfidf = self._build(self.docs)

    def _build(self, docs: list[DocVersion]):
        tokenized = [tokenize(d.text) for d in docs]
        df: dict[str, int] = {}
        for toks in tokenized:
            for t in set(toks):
                df[t] = df.get(t, 0) + 1
        n = len(docs) or 1
        idf = {t: math.log((1 + n) / (1 + c)) + 1.0 for t, c in df.items()}
        vecs = []
        for toks in tokenized:
            tf: dict[str, int] = {}
            for t in toks:
                tf[t] = tf.get(t, 0) + 1
            denom = len(toks) or 1
            vecs.append({t: (tf[t] / denom) * idf.get(t, 0.0) for t in tf})
        return tokenized, idf, vecs

    @staticmethod
    def _cos(a: dict[str, float], b: dict[str, float]) -> float:
        if not a or not b:
            return 0.0
        keys = set(a) | set(b)
        dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
        na = math.sqrt(sum(v * v for v in a.values())) or 1.0
        nb = math.sqrt(sum(v * v for v in b.values())) or 1.0
        return dot / (na * nb)

    def search(
        self,
        query: str,
        *,
        tenant_id: str,
        roles: list[str],
        as_of: str,
        top_k: int = 3,
        min_score: float = 0.02,
    ) -> list[Hit]:
        # ACL + tenant + version window BEFORE scoring
        visible = [
            d
            for d in self.docs
            if d.tenant_id == tenant_id
            and set(roles) & set(d.acl)
            and d.effective_from <= as_of
            and (d.expires_at is None or d.expires_at >= as_of)
        ]
        # keep latest version per doc_id within window
        latest: dict[str, DocVersion] = {}
        for d in sorted(visible, key=lambda x: x.version):
            latest[d.doc_id] = d
        candidates = list(latest.values())

        qv_toks = tokenize(query)
        # keyword channel
        kw_scores = []
        for d in candidates:
            toks = set(tokenize(d.text))
            overlap = len(set(qv_toks) & toks)
            kw_scores.append(overlap / max(1, len(set(qv_toks))))

        # tfidf channel on filtered subset
        _, idf, _ = self._tfidf
        q_tf: dict[str, int] = {}
        for t in qv_toks:
            q_tf[t] = q_tf.get(t, 0) + 1
        qv = {t: (q_tf[t] / max(1, len(qv_toks))) * idf.get(t, 0.0) for t in q_tf}

        hits: list[Hit] = []
        for i, d in enumerate(candidates):
            dv_toks = tokenize(d.text)
            tf: dict[str, int] = {}
            for t in dv_toks:
                tf[t] = tf.get(t, 0) + 1
            dv = {t: (tf[t] / max(1, len(dv_toks))) * idf.get(t, 0.0) for t in tf}
            dense = self._cos(qv, dv)
            hybrid = 0.5 * dense + 0.5 * kw_scores[i]
            if hybrid >= min_score:
                hits.append(Hit(d, hybrid))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]


class AliasRouter:
    """Blue-green: tasks pin kb_version alias at start; switch is atomic."""

    def __init__(self):
        self.aliases: dict[str, Index] = {}
        self.live = "blue"

    def register(self, alias: str, index: Index) -> None:
        self.aliases[alias] = index

    def get_live(self) -> Index:
        return self.aliases[self.live]

    def atomic_switch(self, to_alias: str) -> None:
        if to_alias not in self.aliases:
            raise KeyError(to_alias)
        self.live = to_alias
