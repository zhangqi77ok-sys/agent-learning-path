"""Upstream model providers with fault injection hooks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelResponse:
    text: str
    tokens: int
    model: str


@dataclass
class FakeUpstream:
    name: str
    cost_per_1k: float
    fail_with: list[str] = field(default_factory=list)  # queued errors: 429, 500
    calls: int = 0

    def chat(self, prompt: str) -> ModelResponse:
        self.calls += 1
        if self.fail_with:
            code = self.fail_with.pop(0)
            raise UpstreamError(code, f"{self.name}:{code}")
        return ModelResponse(text=f"[{self.name}] {prompt[:40]}", tokens=max(10, len(prompt) // 2), model=self.name)


class UpstreamError(Exception):
    def __init__(self, code: str, msg: str):
        super().__init__(msg)
        self.code = code
