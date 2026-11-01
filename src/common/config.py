"""Configuration loader and path manager for Justice AI."""

import os
from pathlib import Path
from typing import Any, Dict
import yaml

_CONFIG_CACHE = None

def get_repo_root() -> Path:
    """Returns the absolute path to the repository root."""
    return Path(__file__).resolve().parent.parent.parent

def load_config(config_path: str = None) -> Dict[str, Any]:
    """Loads configuration from YAML file and resolves paths relative to repo root."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None and config_path is None:
        return _CONFIG_CACHE

    root = get_repo_root()
    if config_path is None:
        cfg_file = root / "config.yaml"
    else:
        cfg_file = Path(config_path)
        if not cfg_file.is_absolute():
            cfg_file = root / cfg_file

    if not cfg_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {cfg_file}")

    with open(cfg_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Convert path entries to Path objects
    if "paths" in config:
        for k, v in config["paths"].items():
            if isinstance(v, str):
                p = Path(v)
                config["paths"][k] = p if p.is_absolute() else (root / p)

    if config_path is None:
        _CONFIG_CACHE = config

    return config
