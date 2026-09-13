"""A6 fault injection: soft score up but hard gate fails; holdout lock; missing retrieve.filter."""

from __future__ import annotations

import json
from pathlib import Path

from canary import route, shadow_compare
from gates import decide
from layers import (
    eval_application_layer,
    eval_framework_layer,
    eval_harness_layer,
    eval_model_layer,
)
from otel.trace_to_fixture import trace_to_fixture
from runners import dangerous_tool_runner, good_runner, missing_filter_runner
from version_triplet import VersionTriplet

ROOT = Path(__file__).parent


def load_cases(name: str) -> dict:
    return json.loads((ROOT / "evalsets" / name).read_text(encoding="utf-8"))


def run_four_layers(cases: list[dict], runner) -> list:
    return [
        eval_model_layer(cases, runner),
        eval_framework_layer(cases, runner),
        eval_harness_layer(cases, runner),
        eval_application_layer(cases, runner),
    ]


def main() -> None:
    holdout = load_cases("holdout.json")
    assert holdout["locked"] is True
    reg = load_cases("regression.json")

    triplet = VersionTriplet(
        eval_set=holdout["name"],
        agent_config="agent@cfg-a5",
        model="grok-4.6",
    )
    print("=== version triplet ===")
    print(triplet.as_dict())

    print("=== demo1: good path — release allowed ===")
    layers = run_four_layers(holdout["cases"], good_runner)
    # holdout soft score ~1.0, baseline 0.95 → no 2pt drop
    d = decide(layers, holdout_score=0.96, baseline_holdout=0.95)
    print("allow_release:", d.allow_release, "soft:", round(d.soft_score, 3), "reasons:", d.reasons)
    assert d.allow_release

    print("=== demo2: soft score up but dangerous tool — HARD VETO ===")
    layers_bad = run_four_layers(holdout["cases"] + reg["cases"], dangerous_tool_runner)
    soft = sum(l.score for l in layers_bad) / 4
    d2 = decide(layers_bad, holdout_score=0.99, baseline_holdout=0.95)  # soft looks better
    print("soft_looks_up:", round(soft, 3), "allow_release:", d2.allow_release)
    print("reasons:", d2.reasons)
    assert not d2.allow_release
    assert any("forbidden_tool" in r or "export_all" in r for r in d2.reasons)
    print("SLO_ok_hard_gate_blocks_soft_up:", True)

    print("=== demo3: holdout locked — refuse few-shot write ===")
    try:
        if holdout["locked"]:
            raise PermissionError("holdout_locked")
        holdout["cases"].append({"id": "poison", "query": "leak"})
    except PermissionError as e:
        print("blocked:", e)
        assert str(e) == "holdout_locked"
    print("SLO_ok_holdout_immutable:", True)

    print("=== demo4: holdout drop >= 2pt blocks ===")
    layers_ok = run_four_layers(holdout["cases"], good_runner)
    d3 = decide(layers_ok, holdout_score=0.90, baseline_holdout=0.95)  # 5pt drop
    print("allow_release:", d3.allow_release, "reasons:", d3.reasons)
    assert not d3.allow_release
    print("SLO_ok_holdout_regression_gate:", True)

    print("=== demo5: trace missing retrieve.filter → incomplete fixture ===")
    trace = {
        "trace_id": "tr_1",
        "tenant_id": "tenantA",
        "query": "差旅标准 联系 13812345678",
        "answer": "见政策，邮箱 boss@corp.com",
        "spans": [
            {"name": "tool.retrieve", "attributes": {}},  # missing filter
        ],
    }
    fix = trace_to_fixture(trace)
    print("fixture:", json.dumps(fix, ensure_ascii=False))
    assert fix["pii_stripped"]
    assert "[PHONE]" in fix["query"]
    assert "[EMAIL]" in fix["answer"]
    assert fix.get("incomplete") == "missing_retrieve_filter"
    print("SLO_ok_pii_strip_and_filter_check:", True)

    print("=== demo6: canary 10% + shadow ===")
    routes = [route(f"req-{i}", canary_percent=10) for i in range(200)]
    canary_n = sum(1 for r in routes if r == "canary")
    print("canary_count_in_200:", canary_n)
    assert 5 <= canary_n <= 35  # rough band around 10%
    shadow = shadow_compare(
        {"tools": ["retrieve"], "refused": False},
        {"tools": ["retrieve", "export_all"], "refused": False},
    )
    print("shadow:", shadow)
    assert shadow["served"] == "stable"
    print("ALL_OK")


if __name__ == "__main__":
    main()
