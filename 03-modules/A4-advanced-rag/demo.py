"""A4 fault injection: cross-tenant, expired docs, version pin across alias switch."""

from __future__ import annotations

from rag import Identity, RagService


def main() -> None:
    svc = RagService()
    a = Identity("tenantA", ["user"])
    b = Identity("tenantB", ["user"])
    approver = Identity("tenantA", ["approver"])

    print("=== demo1: cross-tenant hit = 0 ===")
    hits_a = svc.search(a, "差旅", as_of="2026-06-01")
    hits_b = svc.search(b, "差旅", as_of="2026-06-01")
    print("A", [(h.doc.doc_id, h.doc.tenant_id, h.doc.version) for h in hits_a])
    print("B", [(h.doc.doc_id, h.doc.tenant_id, h.doc.version) for h in hits_b])
    assert all(h.doc.tenant_id == "tenantA" for h in hits_a)
    assert all(h.doc.tenant_id == "tenantB" for h in hits_b)
    poison = svc.search(a, "并购", as_of="2026-06-01")
    print("poison_hits_for_A", [(h.doc.doc_id, h.doc.tenant_id) for h in poison])
    assert all(h.doc.tenant_id == "tenantA" for h in poison)
    print("SLO_ok_cross_tenant:", True)

    print("=== demo2: expired doc recall = 0 at as_of ===")
    # as_of in 2025 should get v1; as_of 2026 should get v2 not expired v1
    h2025 = svc.search(a, "差旅", as_of="2025-06-01")
    h2026 = svc.search(a, "差旅", as_of="2026-06-01")
    print("2025", [(h.doc.version, h.doc.text[:20]) for h in h2025])
    print("2026", [(h.doc.version, h.doc.text[:20]) for h in h2026])
    assert h2025 and h2025[0].doc.version == "v1"
    assert h2026 and h2026[0].doc.version == "v2"
    # force window where nothing effective
    empty = svc.search(a, "差旅", as_of="2020-01-01")
    print("before_effective", empty)
    assert empty == []
    print("SLO_ok_expiry:", True)

    print("=== demo3: role ACL ===")
    assert not any(h.doc.doc_id == "secret" for h in svc.search(a, "机密", as_of="2026-06-01"))
    assert any(h.doc.doc_id == "secret" for h in svc.search(approver, "机密", as_of="2026-06-01"))

    print("=== demo4: pin kb alias across atomic switch (historical replay) ===")
    rec_old = svc.answer(a, "差旅", as_of="2026-06-01", pin_alias="blue")
    print("pinned", rec_old)
    # switch live alias (simulates rebuild)
    svc.router.atomic_switch("green")
    assert svc.router.live == "green"
    # old answer still bound to blue versions
    print("history_versions", rec_old.doc_versions, "alias", rec_old.kb_alias)
    assert rec_old.kb_alias == "blue"
    # replay with pin uses same alias
    rec_replay = svc.answer(a, "差旅", as_of="2026-06-01", pin_alias=rec_old.kb_alias)
    assert rec_replay.doc_versions == rec_old.doc_versions
    print("SLO_ok_version_pin:", True)

    print("=== demo5: weak retrieval reject ===")
    weak = svc.answer(a, "火星年假政策", as_of="2026-06-01")
    print(weak.text)
    assert "拒答" in weak.text or weak.doc_versions == []

    print("ALL_OK")


if __name__ == "__main__":
    main()
