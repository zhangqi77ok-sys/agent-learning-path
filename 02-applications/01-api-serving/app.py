"""Minimal FastAPI wrapper around an OpenAI-compatible chat endpoint."""

from __future__ import annotations

import time
from typing import Optional

from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field

from client_config import load_config

app = FastAPI(title="stage-01-llm-api", version="0.1.0")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    system: str = "你是简洁的助教，用中文回答。"
    temperature: float = 0.2


class ChatResponse(BaseModel):
    content: str
    model: Optional[str] = None
    latency_ms: float
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


@app.get("/health")
def health() -> dict:
    cfg = load_config()
    return {
        "ok": True,
        "base_url": cfg.base_url,
        "model": cfg.model,
        # never return api_key
    }


@app.post("/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    try:
        cfg = load_config()
    except SystemExit as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
    t0 = time.perf_counter()
    try:
        resp = client.chat.completions.create(
            model=cfg.model,
            messages=[
                {"role": "system", "content": req.system},
                {"role": "user", "content": req.message},
            ],
            temperature=req.temperature,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"upstream error: {e}") from e

    elapsed_ms = (time.perf_counter() - t0) * 1000
    usage = resp.usage
    return ChatResponse(
        content=resp.choices[0].message.content or "",
        model=resp.model,
        latency_ms=round(elapsed_ms, 1),
        prompt_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
        completion_tokens=getattr(usage, "completion_tokens", None) if usage else None,
        total_tokens=getattr(usage, "total_tokens", None) if usage else None,
    )
