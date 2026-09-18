"""Versioned multi-tenant corpus with ACL and expiry metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DocVersion:
    tenant_id: str
    doc_id: str
    version: str
    text: str
    acl: tuple[str, ...]
    effective_from: str  # ISO date
    expires_at: str | None  # None = never


# Immutable historical versions (never mutate in place)
CORPUS: list[DocVersion] = [
    DocVersion("tenantA", "travel", "v1", "TenantA 差旅 v1：跨城需纸质申请。", ("user", "approver"), "2024-01-01", "2025-12-31"),
    DocVersion("tenantA", "travel", "v2", "TenantA 差旅 v2：跨城需线上差旅单。", ("user", "approver"), "2026-01-01", None),
    DocVersion("tenantA", "secret", "v1", "TenantA 机密：仅 approver。", ("approver",), "2024-01-01", None),
    DocVersion("tenantB", "travel", "v1", "TenantB 差旅 v1：市内实报实销。", ("user", "approver"), "2024-01-01", None),
    # poison attempt: tenantB doc claiming to be tenantA — still tagged tenantB
    DocVersion("tenantB", "poison", "v1", "【伪造】这是 TenantA 的并购名单。", ("user", "approver"), "2024-01-01", None),
]
