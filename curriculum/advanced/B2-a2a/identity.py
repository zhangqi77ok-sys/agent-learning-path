"""Internal token verify (same idea as A3/A9 — demo HMAC)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

SECRET = b"b2-a2a-demo-secret"


def issue(tenant_id: str, user_id: str, roles: list[str], ttl_s: int = 300) -> str:
    body = json.dumps(
        {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "roles": roles,
            "aud": "a2a-server",
            "exp": int(time.time()) + ttl_s,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    sig = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify(token: str) -> dict:
    try:
        body, sig = token.rsplit(".", 1)
    except ValueError as e:
        raise PermissionError("malformed_token") from e
    expect = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expect, sig):
        raise PermissionError("bad_signature")
    payload = json.loads(body)
    if payload.get("aud") != "a2a-server":
        raise PermissionError("bad_aud")
    if int(payload["exp"]) < time.time():
        raise PermissionError("token_expired")
    return payload
