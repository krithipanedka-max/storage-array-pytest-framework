from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class FrameworkConfig:
    raw: dict[str, Any]

    @property
    def backend(self) -> str:
        return str(self.raw.get("backend", "simulator"))

    @property
    def prefix(self) -> str:
        return str(self.raw.get("cleanup", {}).get("prefix", "pytest-"))

    def env_secret(self, key: str) -> str | None:
        env_name = self.raw.get("array", {}).get(key)
        return os.getenv(env_name) if env_name else None


def load_config(path: str | Path) -> FrameworkConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream) or {}
    if not isinstance(data, dict):
        raise ValueError("Top-level YAML configuration must be a mapping")
    return FrameworkConfig(raw=data)
