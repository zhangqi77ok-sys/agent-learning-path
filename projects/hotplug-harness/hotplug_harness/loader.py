"""Discover and load Python plugin modules from plugin directories.

Convention per module (any one works, preference order):
  1. `create_tool()` / `create_model()` / `create_policy()` factory (fresh instance)
  2. module-level `PLUGIN` instance
  3. a class named ending with Tool/Model/Policy, no-arg constructible
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

from .registry import PluginRegistry


def _load_module(path: Path) -> Any:
    mod_name = f"hotplug_plugin_{path.stem}_{abs(hash(str(path.resolve())))}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load plugin: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


def _instantiate_from_module(module: Any, kind: str) -> Any | None:
    factory = getattr(module, f"create_{kind}", None)
    if callable(factory):
        return factory()

    if hasattr(module, "PLUGIN"):
        return getattr(module, "PLUGIN")

    suffix = kind.capitalize()
    for attr_name in dir(module):
        if attr_name.startswith("_"):
            continue
        obj = getattr(module, attr_name)
        if (
            isinstance(obj, type)
            and attr_name.endswith(suffix)
            and obj.__module__ == module.__name__
        ):
            try:
                return obj()
            except TypeError:
                continue
    return None


def discover_py_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        p
        for p in directory.glob("*.py")
        if p.name != "__init__.py" and not p.name.startswith("_")
    )


def load_plugins(
    *,
    tools_dir: Path | str | None = None,
    models_dir: Path | str | None = None,
    policies_dir: Path | str | None = None,
    registry: PluginRegistry | None = None,
) -> PluginRegistry:
    """Scan plugin dirs and populate a registry. Core loop never hardcodes tools."""
    reg = registry or PluginRegistry()

    def _load_kind(directory: Path | str | None, kind: str, register) -> None:
        if directory is None:
            return
        path = Path(directory)
        for py in discover_py_files(path):
            module = _load_module(py)
            instance = _instantiate_from_module(module, kind)
            if instance is None:
                raise RuntimeError(
                    f"plugin {py} has no create_{kind}() / PLUGIN / *{kind.capitalize()} class"
                )
            register(instance)

    _load_kind(tools_dir, "tool", reg.register_tool)
    _load_kind(models_dir, "model", reg.register_model)
    _load_kind(policies_dir, "policy", reg.register_policy)
    return reg


def default_plugin_roots(project_root: Path | str | None = None) -> dict[str, Path]:
    root = Path(project_root) if project_root else Path(__file__).resolve().parent.parent
    plugins = root / "plugins"
    return {
        "tools_dir": plugins / "tools",
        "models_dir": plugins / "models",
        "policies_dir": plugins / "policies",
    }


def load_default(project_root: Path | str | None = None) -> PluginRegistry:
    roots = default_plugin_roots(project_root)
    return load_plugins(**roots)
