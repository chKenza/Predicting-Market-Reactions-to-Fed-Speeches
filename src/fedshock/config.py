"""Load config.yaml and resolve paths relative to the repository root."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config.yaml"

load_dotenv(ROOT / ".env")


@lru_cache
def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


def path(key: str) -> Path:
    """Absolute path for an entry under `paths:` in config.yaml."""
    return ROOT / load_config()["paths"][key]
