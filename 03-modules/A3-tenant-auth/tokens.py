"""Internal short-lived tokens issued by the gateway (Java stub semantics in Python)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def issue_internal_token(
    *,
    secret: str,
    tenant_id: str,
    user_id: str,
    roles: list[str],
    trace_id: str,
    aud: str = "agent-runtime",
    ttl_sec: int = 300,
    now: float | None = None,
) -> str:
    now = time.time() if now is None else now
    payload = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "roles": roles,
        "trace_id": trace_id,
        "aud": aud,
        "iat": int(now),
        "exp": int(now + ttl_sec),
    }
    body = _b64(json.dumps(payload, sort_keys=True).encode())
    sig = _b64(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def verify_internal_token(
    token: str,
    *,
    secret: str,
    expected_aud: str = "agent-runtime",
    now: float | None = None,
) -> dict[str, Any]:
    now = time.time() if now is None else now
    try:
        body, sig = token.split(".", 1)
    except ValueError as e:
        raise ValueError("malformed_token") from e
    expect = _b64(hmac.new(secret.encode(), body.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(expect, sig):
        raise ValueError("bad_signature")
    payload = json.loads(_unb64(body).decode())
    if payload.get("aud") != expected_aud:
        raise ValueError("bad_aud")
    if int(payload.get("exp", 0)) < int(now):
        raise ValueError("expired")
    for k in ("tenant_id", "user_id", "roles", "trace_id"):
        if k not in payload:
            raise ValueError("missing_claim")
    return payload
