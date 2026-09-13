"""Docs with tenant metadata; ACL applied BEFORE retrieval (never only in Prompt)."""

from __future__ import annotations

DOCS = [
    {"id": "A1", "tenant_id": "tenantA", "text": "TenantA 差旅：跨城需提前申请差旅单。", "acl": ["user", "approver"]},
    {"id": "A2", "tenant_id": "tenantA", "text": "TenantA 机密：并购短名单仅 approver 可见。", "acl": ["approver"]},
    {"id": "B1", "tenant_id": "tenantB", "text": "TenantB 差旅：市内实报实销。", "acl": ["user", "approver"]},
]


def retrieve(query: str, *, tenant_id: str, roles: list[str]) -> list[dict]:
    # server-side filter first
    hits = []
    for d in DOCS:
        if d["tenant_id"] != tenant_id:
            continue
        if not set(roles) & set(d["acl"]):
            continue
        if any(tok in d["text"] for tok in query.replace("？", "").split()) or "差旅" in query or "机密" in query:
            hits.append(d)
        elif query.strip():
            # keyword soft match: include if role-visible and tenant matches for demo queries
            if "差旅" in d["text"] and "差旅" in query:
                hits.append(d)
            if "机密" in d["text"] and "机密" in query:
                hits.append(d)
    # fallback: all visible docs for tenant if explicit empty — still ACL'd
    if not hits and query == "*":
        hits = [d for d in DOCS if d["tenant_id"] == tenant_id and set(roles) & set(d["acl"])]
    return hits
