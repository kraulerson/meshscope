"""Structured JSON logging for meshscope."""

import json
import logging
import logging.handlers
import platform
import uuid
from pathlib import Path
from typing import Any


def _get_config_dir() -> Path:
    """Return OS-standard config directory for meshscope."""
    system = platform.system()
    if system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    elif system == "Windows":
        base = Path(
            __import__("os").environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
        )
    else:
        base = Path(
            __import__("os").environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
        )
    return base / "meshscope"


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S.%f"),
            "level": record.levelname,
            "component": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for tracking an operation."""
    return uuid.uuid4().hex[:12]


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure structured logging with rotating file handler.

    Returns the root meshscope logger.
    """
    log_dir = _get_config_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "meshscope.log"

    logger = logging.getLogger("meshscope")
    logger.setLevel(level)

    if not logger.handlers:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)

        # Set file permissions to user-only on Unix
        if platform.system() != "Windows":
            log_file.chmod(0o600)

    return logger
