"""Single-machine shadow / canary percentage routing."""

from __future__ import annotations

import hashlib


def route(request_id: str, *, canary_percent: int) -> str:
    """Return 'canary' or 'stable'. Deterministic by request_id."""
    if canary_percent <= 0:
        return "stable"
    if canary_percent >= 100:
        return "canary"
    h = int(hashlib.sha256(request_id.encode()).hexdigest()[:8], 16) % 100
    return "canary" if h < canary_percent else "stable"


def shadow_compare(stable_out: dict, canary_out: dict) -> dict:
    """Offline shadow: never serve canary; log diffs."""
    return {
        "served": "stable",
        "diff_tools": sorted(set(stable_out.get("tools", [])) ^ set(canary_out.get("tools", []))),
        "same_refuse": stable_out.get("refused") == canary_out.get("refused"),
    }
