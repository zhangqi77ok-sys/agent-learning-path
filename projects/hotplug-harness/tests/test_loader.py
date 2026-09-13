from __future__ import annotations

from pathlib import Path

from hotplug_harness.loader import discover_py_files, load_default, load_plugins

ROOT = Path(__file__).resolve().parent.parent


def test_discover_tools():
    files = discover_py_files(ROOT / "plugins" / "tools")
    stems = {p.stem for p in files}
    assert "echo" in stems
    assert "flaky" in stems


def test_load_default_registry():
    reg = load_default(ROOT)
    assert "echo" in reg.tools
    assert "flaky" in reg.tools
    assert "scripted_happy" in reg.models
    assert "infinite_same_tool" in reg.models
    assert "allowlist" in reg.policies


def test_load_temp_tool(tmp_path: Path):
    py = tmp_path / "ping.py"
    py.write_text(
        """
from dataclasses import dataclass
@dataclass
class PingTool:
    name: str = "ping"
    def run(self, call, state):
        return "pong"
def create_tool():
    return PingTool()
""",
        encoding="utf-8",
    )
    reg = load_plugins(tools_dir=tmp_path)
    assert reg.get_tool("ping") is not None
    assert reg.get_tool("ping").run(None, None) == "pong"
