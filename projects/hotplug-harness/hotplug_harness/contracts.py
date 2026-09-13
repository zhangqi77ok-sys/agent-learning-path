"""Protocol / ABC contracts for hot-pluggable tools, models, and policies.

Adding a plugin = drop one file under plugins/{tools,models,policies}/
that exposes a module-level factory matching the contract. No core edits.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable
import time
import uuid


class RunStatus(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    CANCELLED = "cancelled"
    CIRCUIT_OPEN = "circuit_open"
    BUDGET_EXCEEDED = "budget_exceeded"
    FAILED = "failed"
    POLICY_BLOCKED = "policy_blocked"


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any]
    signature: str = ""

    def __post_init__(self) -> None:
        if not self.signature:
            self.signature = f"{self.name}:{sorted(self.args.items())}"


@dataclass
class StepEvent:
    step: int
    kind: str  # model | tool | policy | circuit | budget | cancel
    detail: dict[str, Any] = field(default_factory=dict)
    ts_ms: float = field(default_factory=lambda: time.time() * 1000)


@dataclass
class IsolationKeys:
    """Mandatory isolation: tenant / user / thread / run on every run."""

    tenant_id: str
    user_id: str
    thread_id: str
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class RunState:
    isolation: IsolationKeys
    status: RunStatus = RunStatus.RUNNING
    step: int = 0
    tool_calls: int = 0
    started_ms: float = field(default_factory=lambda: time.time() * 1000)
    events: list[StepEvent] = field(default_factory=list)
    last_tool_signatures: list[str] = field(default_factory=list)
    cancel_requested: bool = False
    final: str = ""
    last_tool_results: list[str] = field(default_factory=list)
    user_message: str = ""  # optional Q&A input from chat /api/chat

    @property
    def tenant_id(self) -> str:
        return self.isolation.tenant_id

    @property
    def user_id(self) -> str:
        return self.isolation.user_id

    @property
    def thread_id(self) -> str:
        return self.isolation.thread_id

    @property
    def run_id(self) -> str:
        return self.isolation.run_id


@dataclass
class PolicyDecision:
    allow: bool
    reason: str = ""


@runtime_checkable
class ToolPlugin(Protocol):
    """Drop a file under plugins/tools/ that exposes `PLUGIN` or `create_tool()`."""

    name: str

    def run(self, call: ToolCall, state: RunState) -> str:
        """Execute the tool; return a short string result."""


@runtime_checkable
class ModelPlugin(Protocol):
    """Model only proposes next step — Harness owns the loop."""

    name: str

    def propose(self, state: RunState) -> tuple[str | None, list[ToolCall]]:
        """Return (final_text or None, tool_calls)."""


@runtime_checkable
class PolicyPlugin(Protocol):
    """Policy decides allow/deny before tool execution."""

    name: str

    def check(self, state: RunState, call: ToolCall) -> PolicyDecision:
        ...


class BaseTool(ABC):
    name: str

    @abstractmethod
    def run(self, call: ToolCall, state: RunState) -> str:
        ...


class BaseModel(ABC):
    name: str

    @abstractmethod
    def propose(self, state: RunState) -> tuple[str | None, list[ToolCall]]:
        ...


class BasePolicy(ABC):
    name: str

    @abstractmethod
    def check(self, state: RunState, call: ToolCall) -> PolicyDecision:
        ...
