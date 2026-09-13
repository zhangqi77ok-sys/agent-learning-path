"""Eval version triplet: eval_set × agent_config × model."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


@dataclass(frozen=True)
class VersionTriplet:
    eval_set: str
    agent_config: str
    model: str

    def key(self) -> str:
        raw = f"{self.eval_set}|{self.agent_config}|{self.model}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def as_dict(self) -> dict:
        return {
            "eval_set": self.eval_set,
            "agent_config": self.agent_config,
            "model": self.model,
            "key": self.key(),
        }


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)
