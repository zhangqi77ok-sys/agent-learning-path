"""Retrieve with ACL before scoring."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Doc:
    tenant_id: str
    doc_id: str
    text: str
    acl_roles: set[str]


CORPUS = [
    Doc("tenantA", "a1", "tenantA 差旅：高铁二等座可报。", {"employee", "admin"}),
    Doc("tenantB", "b1", "tenantB 差旅：仅经济舱。", {"employee", "admin"}),
    Doc("tenantA", "a2", "tenantA 薪资带宽机密。", {"admin"}),
]


def _score(query: str, text: str) -> int:
    score = 0
    for i in range(len(query)):
        for n in (2, 1):
            gram = query[i : i + n]
            if len(gram) == n and gram in text:
                score += n
    return score


def retrieve(*, tenant_id: str, roles: set[str], query: str) -> list[Doc]:
    # ACL BEFORE scoring
    allowed = [d for d in CORPUS if d.tenant_id == tenant_id and (roles & d.acl_roles)]
    ranked = sorted(allowed, key=lambda d: _score(query, d.text), reverse=True)
    hits = [d for d in ranked if _score(query, d.text) > 0]
    return hits
