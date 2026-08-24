"""Metadata helpers for versioned YAML contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - dependency is optional for foundation tests
    yaml = None


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file when PyYAML is installed."""

    if yaml is None:
        raise RuntimeError("PyYAML is required to load metadata YAML files.")
    with Path(path).open() as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at top level: {path}")
    return data
