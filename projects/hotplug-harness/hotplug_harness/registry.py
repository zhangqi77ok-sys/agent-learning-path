"""In-memory registries for discovered plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .contracts import ModelPlugin, PolicyPlugin, ToolPlugin


@dataclass
class PluginRegistry:
    tools: dict[str, ToolPlugin] = field(default_factory=dict)
    models: dict[str, ModelPlugin] = field(default_factory=dict)
    policies: dict[str, PolicyPlugin] = field(default_factory=dict)

    def register_tool(self, tool: ToolPlugin) -> None:
        self.tools[tool.name] = tool

    def register_model(self, model: ModelPlugin) -> None:
        self.models[model.name] = model

    def register_policy(self, policy: PolicyPlugin) -> None:
        self.policies[policy.name] = policy

    def get_tool(self, name: str) -> ToolPlugin | None:
        return self.tools.get(name)

    def get_model(self, name: str) -> ModelPlugin | None:
        return self.models.get(name)

    def get_policy(self, name: str) -> PolicyPlugin | None:
        return self.policies.get(name)

    def summary(self) -> dict[str, Any]:
        return {
            "tools": sorted(self.tools),
            "models": sorted(self.models),
            "policies": sorted(self.policies),
        }
