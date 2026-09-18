"""Minimal sandbox: only allow writes under an allowlisted root; no network."""

from __future__ import annotations

from pathlib import Path


class Sandbox:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def write_text(self, relative: str, content: str) -> str:
        # reject absolute / traversal
        if relative.startswith("/") or ".." in Path(relative).parts:
            raise PermissionError("sandbox_escape")
        target = (self.root / relative).resolve()
        if not str(target).startswith(str(self.root)):
            raise PermissionError("sandbox_escape")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return str(target)
