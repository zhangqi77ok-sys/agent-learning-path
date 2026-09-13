"""FastAPI control plane — wraps hotplug_harness, does not replace it.

Students can chat (Q&A) or hit demo endpoints and see:
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
from hotplug_harness.contracts import RunState, RunStatus  # noqa: E402

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

# Sample questions for the console chips (fill input only).
SAMPLE_CHIPS: list[dict[str, str]] = [
    {
        "id": "happy",
        "label": "正常问答",
        "fill": "请用一句话解释什么是 Agent Harness？",
    },
    {
        "id": "circuit",
        "label": "触发熔断",
        "fill": "请演示死循环熔断：模型不停调用同一工具",
    },
    {
        "id": "budget",
        "label": "超预算",
        "fill": "请演示超步数预算耗尽：每次不同工具签名一直跑",
    },
    {
        "id": "policy",
        "label": "越权工具",
        "fill": "请尝试越权调用 forbidden 的 drop_db 工具",
    },
]


class RunRequest(BaseModel):
    tenant_id: str = "t1"
    user_id: str = "u1"
    thread_id: str = "th-manual"
    model_name: str
    message: str | None = None
    max_steps: int | None = None
    max_wall_ms: int | None = None
    max_tool_calls: int | None = None
    circuit_limit: int | None = None
    policy_names: list[str] | None = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    tenant_id: str = "t1"
    user_id: str = "u1"
    thread_id: str = "th-chat"
    model_name: str | None = None
    max_steps: int | None = None
    max_wall_ms: int | None = None
    max_tool_calls: int | None = None
    circuit_limit: int | None = None
    policy_names: list[str] | None = None


def _fresh_registry():
    """Reload from disk so stateful scripted models start clean."""
    return load_default(ROOT)


def _route_from_message(message: str) -> dict[str, Any]:
    """Keyword → scripted model + budget/circuit knobs (teaching paths)."""
    text = message
    lower = message.lower()

    if any(k in text for k in ("死循环", "熔断")) or "circuit" in lower:
        return {
            "route": "circuit",
            "model_name": "infinite_same_tool",
            "max_steps": 8,
            "max_wall_ms": 30_000,
            "max_tool_calls": 100,
            "circuit_limit": 3,
            "thread_hint": "th-chat-circuit",
        }
    if any(k in text for k in ("预算", "超步")) or "budget" in lower:
        return {
            "route": "budget",
            "model_name": "unique_infinite",
            "max_steps": 5,
            "max_wall_ms": 30_000,
            "max_tool_calls": 100,
            "circuit_limit": 3,
            "thread_hint": "th-chat-budget",
        }
    if any(k in text for k in ("越权",)) or "forbidden" in lower:
        return {
            "route": "policy",
            "model_name": "forbidden_tool",
            "max_steps": 8,
            "max_wall_ms": 30_000,
            "max_tool_calls": 16,
            "circuit_limit": 3,
            "thread_hint": "th-chat-policy",
        }
    return {
        "route": "happy",
        "model_name": "scripted_happy",
        "max_steps": 8,
        "max_wall_ms": 30_000,
        "max_tool_calls": 16,
        "circuit_limit": 3,
        "thread_hint": "th-chat-happy",
    }


def _assistant_reply(state: RunState, message: str) -> str:
    """Human-readable assistant bubble text for the chat UI."""
    status = state.status
    if status == RunStatus.SUCCEEDED:
        return state.final or "（模型未返回最终文本）"
    if status == RunStatus.CIRCUIT_OPEN:
        return (
            f"Harness 已熔断（circuit_open）：检测到重复工具签名。"
            f"你的问题是「{message}」。"
            f"控制面拦住了死循环，不是模型自己停的。"
        )
    if status == RunStatus.BUDGET_EXCEEDED:
        return (
            f"Harness 预算耗尽（budget_exceeded）：步数/工具调用超限。"
            f"你的问题是「{message}」。"
            f"Budget 强制停跑。"
        )
    if status == RunStatus.POLICY_BLOCKED:
        return (
            f"Harness 策略拦截（policy_blocked）：{state.final or 'denied'}。"
            f"你的问题是「{message}」。"
            f"越权工具从未执行。"
        )
    if status == RunStatus.CANCELLED:
        return f"运行已取消。问题：「{message}」。"
    if status == RunStatus.FAILED:
        return f"运行失败：{state.final or status.value}。问题：「{message}」。"
    return f"status={status.value} final={state.final!r}"


def serialize_run(
    state: RunState,
    *,
    model_name: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "run_id": state.run_id,
        "status": state.status.value,
        "final": state.final,
        "step": state.step,
        "tool_calls": state.tool_calls,
        "model_name": model_name,
        "cancel_requested": state.cancel_requested,
        "user_message": state.user_message,
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

app = FastAPI(title="Hot-pluggable Harness Console API", version="0.2.0")
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
        "mode": "chat-qa",
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


@app.get("/api/samples")
def list_samples() -> list[dict[str, str]]:
    """Chips that only fill the chat input — still submitted as messages."""
    return SAMPLE_CHIPS


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
    user_message: str = "",
    route: str | None = None,
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
    state = harness.start_run(
        tenant_id=tenant_id,
        user_id=user_id,
        thread_id=thread_id,
        user_message=user_message,
    )
    harness.run_until_done(state)
    reply = _assistant_reply(state, user_message) if user_message else (state.final or "")
    payload = serialize_run(
        state,
        model_name=model_name,
        extra={
            "demo": demo,
            "route": route,
            "reply": reply,
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
        user_message=body.message or "",
    )


@app.post("/api/chat")
def chat(body: ChatRequest) -> dict[str, Any]:
    """Q&A entry: message drives model selection + harness run."""
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    routed = _route_from_message(message)
    model_name = body.model_name or routed["model_name"]
    max_steps = body.max_steps if body.max_steps is not None else routed["max_steps"]
    max_wall_ms = body.max_wall_ms if body.max_wall_ms is not None else routed["max_wall_ms"]
    max_tool_calls = (
        body.max_tool_calls if body.max_tool_calls is not None else routed["max_tool_calls"]
    )
    circuit_limit = (
        body.circuit_limit if body.circuit_limit is not None else routed["circuit_limit"]
    )
    thread_id = body.thread_id
    # If client left the default chat thread, use a route-specific hint for teaching.
    if thread_id == "th-chat":
        thread_id = routed["thread_hint"]

    return _execute_run(
        tenant_id=body.tenant_id,
        user_id=body.user_id,
        thread_id=thread_id,
        model_name=model_name,
        max_steps=max_steps,
        max_wall_ms=max_wall_ms,
        max_tool_calls=max_tool_calls,
        circuit_limit=circuit_limit,
        policy_names=body.policy_names,
        user_message=message,
        route=routed["route"],
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
        route=name,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
