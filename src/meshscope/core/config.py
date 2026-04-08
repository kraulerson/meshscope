"""Schema-versioned application configuration with atomic persistence."""

from __future__ import annotations

import contextlib
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger("meshscope.core.config")

CURRENT_SCHEMA_VERSION = 1

DEFAULT_CONFIG: dict[str, Any] = {
    "version": CURRENT_SCHEMA_VERSION,
    "print_bed": {
        "preset": "ender_3",
        "custom_x": 220,
        "custom_y": 220,
        "custom_z": 250,
    },
}


def _get_config_path() -> Path:
    """Return the default config file path."""
    from meshscope.core.logging import _get_config_dir

    config_dir = _get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Merge overlay into base, filling missing keys from base."""
    result = base.copy()
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class AppConfig:
    """Application configuration backed by a dict with schema version."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        if data is None:
            self._data = json.loads(json.dumps(DEFAULT_CONFIG))
        else:
            self._data = _deep_merge(json.loads(json.dumps(DEFAULT_CONFIG)), data)

    @property
    def version(self) -> int:
        return int(self._data.get("version", CURRENT_SCHEMA_VERSION))

    def get(self, section: str, key: str) -> Any:
        return self._data.get(section, {}).get(key)

    def set(self, section: str, key: str, value: Any) -> None:
        if section not in self._data:
            self._data[section] = {}
        self._data[section][key] = value

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)


def load_config(path: Path | None = None) -> AppConfig:
    """Load config from file. Returns defaults on any error."""
    if path is None:
        path = _get_config_path()
    if not path.exists():
        logger.info("Config file not found, using defaults: %s", path)
        return AppConfig()
    try:
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Corrupt config file, resetting to defaults: %s", e)
        return AppConfig()
    if not isinstance(data, dict):
        logger.warning("Config is not a dict, resetting to defaults")
        return AppConfig()
    version = data.get("version")
    if version != CURRENT_SCHEMA_VERSION:
        logger.warning("Unknown config version %s, resetting to defaults", version)
        return AppConfig()
    return AppConfig(data)


def save_config(config: AppConfig, path: Path | None = None) -> None:
    """Save config to file with atomic write."""
    if path is None:
        path = _get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_fd = None
    temp_path = None
    try:
        temp_fd, temp_path_str = tempfile.mkstemp(suffix=".json.tmp", dir=path.parent)
        os.close(temp_fd)
        temp_fd = None
        temp_path = Path(temp_path_str)
        temp_path.write_text(
            json.dumps(config.to_dict(), indent=2) + "\n", encoding="utf-8"
        )
        os.replace(str(temp_path), str(path))
        temp_path = None
        logger.info("Config saved to %s", path)
    except OSError as e:
        logger.error("Failed to save config: %s", e)
    finally:
        if temp_path is not None:
            with contextlib.suppress(OSError):
                temp_path.unlink(missing_ok=True)
