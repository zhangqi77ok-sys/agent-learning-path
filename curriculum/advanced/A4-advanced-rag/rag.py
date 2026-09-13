"""RAG API: tenant never accepted from client body — only from verified identity."""

from __future__ import annotations

from dataclasses import dataclass

from corpus import CORPUS
from index import AliasRouter, Index


@dataclass
class Identity:
    tenant_id: str
    roles: list[str]


@dataclass
class AnswerRecord:
    kb_alias: str
    doc_versions: list[str]
    text: str


class RagService:
    def __init__(self):
        # blue = full corpus; green = rebuild excluding expired-as-of-future demo
        self.router = AliasRouter()
        self.router.register("blue", Index(CORPUS, name="blue"))
        self.router.register("green", Index(CORPUS, name="green"))
        self.history: list[AnswerRecord] = []

    def search(self, identity: Identity, query: str, *, as_of: str, pin_alias: str | None = None):
        # CRITICAL: no client-provided tenant_id parameter
        idx = self.router.aliases[pin_alias] if pin_alias else self.router.get_live()
        return idx.search(query, tenant_id=identity.tenant_id, roles=identity.roles, as_of=as_of)

    def answer(self, identity: Identity, query: str, *, as_of: str, pin_alias: str | None = None) -> AnswerRecord:
        alias = pin_alias or self.router.live
        hits = self.search(identity, query, as_of=as_of, pin_alias=alias)
        if not hits:
            rec = AnswerRecord(alias, [], "依据不足，拒答。")
        else:
            cites = [f"{h.doc.doc_id}@{h.doc.version}" for h in hits]
            text = hits[0].doc.text + f" [{cites[0]}]"
            rec = AnswerRecord(alias, cites, text)
        self.history.append(rec)
        return rec
