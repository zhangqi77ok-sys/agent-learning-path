"""FastAPI control plane — wraps hotplug_harness, does not replace it.

Students can hit these endpoints (or the Vite console) and see:
  Model proposes → Harness owns loop / budget / circuit / policy.
No real LLM keys; scripted model plugins only.
"""

from __future__ import annotations

import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hotplug_harness import Budget, CircuitBreaker, Harness, load_default  # noqa: E402
from hotplug_harness.contracts import RunState  # noqa: E402

MAX_STORED_RUNS = 50

DEMOS: dict[str, dict[str, Any]] = {
    "happy": {
        "label": "Happy path",
        "proves": "脚本模型 echo 两次后收工，status=succeeded",
        "model_name": "scripted_happy",
        "tenant_id": "t1",
        "user_id": "u1",
        "thread_id": "th-happy",
        "max_steps": 8,
        "max_wall_ms": 30_000,
        "max_tool_calls": 16,
        "circuit_limit": 3,
    },
    "circuit": {
        "label": "Circuit open",
        "proves": "同一 tool signature 连打，熔断 circuit_open",
        "model_name": "infinite_same_tool",
        "tenant_id": "t1",
        "user_id": "u1",
        "thread_id": "th-circuit",
        "max_steps": 8,
        "max_wall_ms": 30_000,
        "max_tool_calls": 100,
        "circuit_limit": 3,
    },
    "budget": {
        "label": "Budget exceeded",
        "proves": "每次不同 signature，打满步数后 budget_exceeded",
        "model_name": "unique_infinite",
        "tenant_id": "t1",
        "user_id": "u1",
        "thread_id": "th-budget",
        "max_steps": 5,
        "max_wall_ms": 30_000,
        "max_tool_calls": 100,
        "circuit_limit": 3,
    },
    "policy": {
        "label": "Policy blocked",
        "proves": "allowlist 拦下 drop_db，status=policy_blocked",
        "model_name": "forbidden_tool",
        "tenant_id": "t1",
        "user_id": "u1",
        "thread_id": "th-policy",
        "max_steps": 8,
        "max_wall_ms": 30_000,
        "max_tool_calls": 16,
        "circuit_limit": 3,
    },
}


class RunRequest(BaseModel):
    tenant_id: str = "t1"
    user_id: str = "u1"
    thread_id: str = "th-manual"
    model_name: str
    max_steps: int | None = None
    max_wall_ms: int | None = None
    max_tool_calls: int | None = None
    circuit_limit: int | None = None
    policy_names: list[str] | None = None


def _fresh_registry():
    """Reload from disk so stateful scripted models start clean."""
    return load_default(ROOT)


def serialize_run(state: RunState, *, model_name: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "run_id": state.run_id,
        "status": state.status.value,
        "final": state.final,
        "step": state.step,
        "tool_calls": state.tool_calls,
        "model_name": model_name,
        "cancel_requested": state.cancel_requested,
        "isolation": {
            "tenant_id": state.tenant_id,
            "user_id": state.user_id,
            "thread_id": state.thread_id,
            "run_id": state.run_id,
        },
        "events": [
            {
                "step": e.step,
                "kind": e.kind,
                "detail": e.detail,
                "ts_ms": e.ts_ms,
            }
            for e in state.events
        ],
    }
    if extra:
        payload.update(extra)
    return payload


class AppState:
    """In-memory demo store. Fine for teaching; not a product."""

    def __init__(self) -> None:
        self.registry = _fresh_registry()
        self.runs: OrderedDict[str, dict[str, Any]] = OrderedDict()

    def remember(self, payload: dict[str, Any]) -> None:
        rid = payload["run_id"]
        if rid in self.runs:
            self.runs.move_to_end(rid)
        self.runs[rid] = payload
        while len(self.runs) > MAX_STORED_RUNS:
            self.runs.popitem(last=False)


store = AppState()

app = FastAPI(title="Hot-pluggable Harness Console API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "hotplug-harness",
        "plugins": store.registry.summary(),
        "stored_runs": len(store.runs),
    }


@app.get("/api/plugins")
def list_plugins() -> dict[str, Any]:
    return store.registry.summary()


@app.post("/api/plugins/reload")
def reload_plugins() -> dict[str, Any]:
    store.registry = _fresh_registry()
    return {"reloaded": True, **store.registry.summary()}


@app.get("/api/models")
def list_models() -> list[str]:
    return sorted(store.registry.models)


@app.get("/api/tools")
def list_tools() -> list[str]:
    return sorted(store.registry.tools)


@app.get("/api/demos")
def list_demos() -> dict[str, Any]:
    return {
        name: {
            "name": name,
            "label": spec["label"],
            "proves": spec["proves"],
            "model_name": spec["model_name"],
        }
        for name, spec in DEMOS.items()
    }


def _execute_run(
    *,
    tenant_id: str,
    user_id: str,
    thread_id: str,
    model_name: str,
    max_steps: int | None = None,
    max_wall_ms: int | None = None,
    max_tool_calls: int | None = None,
    circuit_limit: int | None = None,
    policy_names: list[str] | None = None,
    demo: str | None = None,
) -> dict[str, Any]:
    # Fresh registry per run: scripted models (e.g. remaining_echoes) must reset.
    registry = _fresh_registry()
    store.registry = registry
    model = registry.get_model(model_name)
    if model is None:
        raise HTTPException(status_code=400, detail=f"unknown model: {model_name}")

    budget = Budget(
        max_steps=max_steps if max_steps is not None else 8,
        max_wall_ms=max_wall_ms if max_wall_ms is not None else 30_000,
        max_tool_calls=max_tool_calls if max_tool_calls is not None else 16,
    )
    circuit = CircuitBreaker(circuit_limit if circuit_limit is not None else 3)
    names = tuple(policy_names) if policy_names else ("allowlist",)
    harness = Harness(
        registry=registry,
        model=model,
        budget=budget,
        circuit=circuit,
        policy_names=names,
    )
    state = harness.start_run(tenant_id=tenant_id, user_id=user_id, thread_id=thread_id)
    harness.run_until_done(state)
    payload = serialize_run(
        state,
        model_name=model_name,
        extra={
            "demo": demo,
            "budget": {
                "max_steps": budget.max_steps,
                "max_wall_ms": budget.max_wall_ms,
                "max_tool_calls": budget.max_tool_calls,
            },
            "circuit_limit": circuit.duplicate_signature_limit,
            "policy_names": list(names),
        },
    )
    store.remember(payload)
    return payload


@app.post("/api/runs")
def start_run(body: RunRequest) -> dict[str, Any]:
    return _execute_run(
        tenant_id=body.tenant_id,
        user_id=body.user_id,
        thread_id=body.thread_id,
        model_name=body.model_name,
        max_steps=body.max_steps,
        max_wall_ms=body.max_wall_ms,
        max_tool_calls=body.max_tool_calls,
        circuit_limit=body.circuit_limit,
        policy_names=body.policy_names,
    )


@app.get("/api/runs")
def list_runs() -> list[dict[str, Any]]:
    return list(reversed(store.runs.values()))


@app.get("/api/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    if run_id not in store.runs:
        raise HTTPException(status_code=404, detail=f"unknown run: {run_id}")
    return store.runs[run_id]


@app.post("/api/runs/{run_id}/cancel")
def cancel_run(run_id: str) -> dict[str, Any]:
    """Teaching stub: scripted runs finish synchronously, so this is usually a no-op."""
    if run_id not in store.runs:
        raise HTTPException(status_code=404, detail=f"unknown run: {run_id}")
    payload = store.runs[run_id]
    if payload["status"] == "running":
        payload = dict(payload)
        payload["status"] = "cancelled"
        payload["cancel_requested"] = True
        payload["events"] = list(payload["events"]) + [
            {"step": payload["step"], "kind": "cancel", "detail": {"cancel": True}, "ts_ms": 0}
        ]
        store.remember(payload)
    return payload


@app.post("/api/demos/{name}")
def run_demo(name: str) -> dict[str, Any]:
    spec = DEMOS.get(name)
    if spec is None:
        raise HTTPException(
            status_code=404,
            detail=f"unknown demo: {name}; choose one of {sorted(DEMOS)}",
        )
    return _execute_run(
        tenant_id=spec["tenant_id"],
        user_id=spec["user_id"],
        thread_id=spec["thread_id"],
        model_name=spec["model_name"],
        max_steps=spec["max_steps"],
        max_wall_ms=spec["max_wall_ms"],
        max_tool_calls=spec["max_tool_calls"],
        circuit_limit=spec["circuit_limit"],
        demo=name,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
