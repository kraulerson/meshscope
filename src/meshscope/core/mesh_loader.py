"""Mesh file loading: validation, parsing, and MeshDocument construction."""

from __future__ import annotations

import os
from pathlib import Path

from meshscope.core.exceptions import (
    FileNotFoundError_,
    FileNotReadableError,
    FileTooLargeError,
    UnsupportedFormatError,
)

SUPPORTED_FORMATS: dict[str, str] = {
    ".stl": "stl",
    ".obj": "obj",
    ".3mf": "3mf",
    ".ply": "ply",
}

MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500MB


def detect_format(path: Path) -> str:
    """Detect mesh format from file extension.

    Returns the trimesh file_type string.
    Raises UnsupportedFormatError if extension is not supported.
    """
    ext = path.suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        raise UnsupportedFormatError(
            f"Unsupported file format: {ext}. Supported formats: STL, OBJ, 3MF, PLY."
        )
    return SUPPORTED_FORMATS[ext]


def validate_path(path: Path) -> None:
    """Validate that the file exists, is readable, has a supported
    extension, and is within the size limit.

    Raises FileValidationError subclasses on failure.
    """
    path = Path(path)

    # Check extension first (cheapest check)
    detect_format(path)

    # Check existence
    if not path.is_file():
        raise FileNotFoundError_(f"File not found: {path}.")

    # Check readable
    if not os.access(path, os.R_OK):
        raise FileNotReadableError(f"Cannot read file: {path}. Permission denied.")

    # Check size
    size_bytes = path.stat().st_size
    if size_bytes > MAX_FILE_SIZE_BYTES:
        size_mb = size_bytes // (1024 * 1024)
        raise FileTooLargeError(
            f"File too large: {size_mb}MB. Maximum supported size: 500MB."
        )
