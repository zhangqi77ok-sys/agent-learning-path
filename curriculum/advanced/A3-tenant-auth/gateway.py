"""Spring-gateway stub: SSO login -> internal token. Identity elevation only happens here."""

from __future__ import annotations

import uuid

from tokens import issue_internal_token

GATEWAY_SECRET = "dev-gateway-hmac-not-for-prod"
USERS = {
    # username -> (password, tenant, roles)
    "alice": ("pw", "tenantA", ["user"]),
    "bob": ("pw", "tenantB", ["user"]),
    "adminA": ("pw", "tenantA", ["user", "approver"]),
}


def login(username: str, password: str) -> str:
    rec = USERS.get(username)
    if not rec or rec[0] != password:
        raise PermissionError("login_failed")
    _, tenant, roles = rec
    return issue_internal_token(
        secret=GATEWAY_SECRET,
        tenant_id=tenant,
        user_id=username,
        roles=roles,
        trace_id=str(uuid.uuid4()),
    )
