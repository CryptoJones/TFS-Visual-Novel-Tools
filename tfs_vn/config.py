"""Shared config and filesystem helpers for the toolkit."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when a user-facing config file is missing required shape."""


def load_json(path: str | Path) -> dict[str, Any]:
    src = Path(path).expanduser().resolve()
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"cannot read {src}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{src}: invalid JSON at line {exc.lineno}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{src}: top-level JSON value must be an object")
    return data


def write_json(path: str | Path, data: Any) -> None:
    dst = Path(path)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def resolve_path(base: Path, value: str | Path | None) -> Path | None:
    if value in (None, ""):
        return None
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = base / p
    return p.resolve()


def slugify(value: str, fallback: str = "item") -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = value.strip("_")
    return value or fallback


def titleize_slug(value: str) -> str:
    return slugify(value).replace("_", " ").title()


def as_object(value: Any, name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"{name} must be an object")
    return value


def as_list(value: Any, name: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ConfigError(f"{name} must be a list")
    return value


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def engine_template(default: str | Path | None = None) -> Path:
    if default:
        candidate = Path(default).expanduser().resolve()
    else:
        candidate = repo_root() / "engine"
    if not (candidate / "project.godot").exists():
        raise ConfigError(
            "engine template not found; pass --template or set TFS_VN_ENGINE_TEMPLATE"
        )
    return candidate


def godot_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)
