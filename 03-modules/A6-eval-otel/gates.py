"""Hard gates > soft scores. Any hard failure blocks release."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from layers import LayerResult


@dataclass
class GateDecision:
    allow_release: bool
    reasons: list[str]
    soft_score: float


def decide(
    layers: list[LayerResult],
    *,
    holdout_score: float,
    baseline_holdout: float,
    max_drop_points: float = 2.0,
) -> GateDecision:
    reasons: list[str] = []
    for lr in layers:
        for h in lr.hard_failures:
            reasons.append(f"hard:{lr.layer}:{h}")
    drop = (baseline_holdout - holdout_score) * 100  # scores 0..1 → points
    if drop >= max_drop_points:
        reasons.append(f"hard:holdout_regression:drop_{drop:.1f}pt")
    soft = sum(lr.score for lr in layers) / max(len(layers), 1)
    return GateDecision(allow_release=not reasons, reasons=reasons, soft_score=soft)
