"""Four isolation keys injected by Java gateway — never from model/state."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass


SECRET = b"capstone-demo-secret"


@dataclass(frozen=True)
class IsolationKeys:
    tenant_id: str
    user_id: str
    thread_id: str
    run_id: str


def issue_internal_token(
    *,
    tenant_id: str,
    user_id: str,
    roles: list[str],
    ttl_s: int = 300,
) -> str:
    payload = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "roles": roles,
        "aud": "python-agent",
        "exp": int(time.time()) + ttl_s,
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    sig = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def verify_internal_token(token: str) -> dict:
    try:
        body, sig = token.rsplit(".", 1)
    except ValueError as e:
        raise PermissionError("malformed_token") from e
    expect = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expect, sig):
        raise PermissionError("bad_signature")
    payload = json.loads(body)
    if payload.get("aud") != "python-agent":
        raise PermissionError("bad_aud")
    if int(payload.get("exp", 0)) < time.time():
        raise PermissionError("token_expired")
    return payload
