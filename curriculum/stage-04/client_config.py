"""Resolve OpenAI-compatible client settings from environment."""
from __future__ import annotations
import os
from dataclasses import dataclass
@dataclass(frozen=True)
class LLMConfig:
    api_key: str
    base_url: str
    model: str
def load_config() -> LLMConfig:
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("AGENTROUTER_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("AGENTROUTER_BASE_URL") or "https://api.openai.com/v1"
    model = os.environ.get("OPENAI_MODEL") or os.environ.get("AGENTROUTER_MODEL") or "gpt-4o-mini"
    if not api_key:
        raise SystemExit("缺少 API Key：请设置 OPENAI_API_KEY（或 AGENTROUTER_API_KEY）")
    return LLMConfig(api_key=api_key, base_url=base_url.rstrip("/"), model=model)
