"""Mesh export: MeshData → file with atomic write and validation."""

from __future__ import annotations

import contextlib
import logging
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import trimesh

from meshscope.core.exceptions import MeshExportError

if TYPE_CHECKING:
    from meshscope.core.mesh_data import MeshData

logger = logging.getLogger("meshscope.core.mesh_exporter")

SUPPORTED_EXPORT_FORMATS = {"stl", "obj", "3mf", "ply"}


def export_mesh(mesh: MeshData, path: Path, file_type: str) -> None:
    """Export mesh data to a file using atomic write.

    Converts MeshData to a trimesh.Trimesh, exports to a temp file,
    validates the output, then atomically renames to the final path.

    Raises MeshExportError on any failure.
    """
    if file_type not in SUPPORTED_EXPORT_FORMATS:
        raise MeshExportError(
            f"Unsupported export format: {file_type}. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXPORT_FORMATS))}"
        )

    # Convert MeshData → trimesh.Trimesh
    tm_mesh = trimesh.Trimesh(
        vertices=np.array(mesh.vertices, dtype=np.float64),
        faces=np.array(mesh.faces, dtype=np.int64),
        face_normals=np.array(mesh.normals, dtype=np.float64),
        process=False,
    )

    # Atomic write: temp file in same directory → rename
    target_dir = path.parent
    temp_fd = None
    temp_path = None

    try:
        temp_fd, temp_path_str = tempfile.mkstemp(
            suffix=f".{file_type}.tmp",
            dir=target_dir,
        )
        os.close(temp_fd)
        temp_fd = None
        temp_path = Path(temp_path_str)

        # Export via trimesh
        tm_mesh.export(str(temp_path), file_type=file_type)

        # Post-export validation
        if not temp_path.exists() or temp_path.stat().st_size == 0:
            raise MeshExportError(
                "Export produced empty file — mesh data may be corrupt."
            )

        # Atomic rename
        os.replace(str(temp_path), str(path))
        temp_path = None  # Prevent cleanup of renamed file

        logger.info(
            "Exported %s as %s (%d bytes)", path.name, file_type, path.stat().st_size
        )

    except MeshExportError:
        raise
    except PermissionError as e:
        raise MeshExportError(f"Cannot write to {path}: Permission denied") from e
    except OSError as e:
        raise MeshExportError(f"Export failed: {e}") from e
    except Exception as e:
        raise MeshExportError(f"Export failed: {e}") from e
    finally:
        # Clean up temp file if it still exists
        if temp_path is not None:
            with contextlib.suppress(OSError):
                temp_path.unlink(missing_ok=True)


def check_symlink(path: Path) -> Path | None:
    """Check if path contains a symlink.

    Returns resolved path if different from input path, None if safe.
    """
    resolved = Path(os.path.realpath(path))
    if resolved != path.resolve():
        return resolved
    return None


def get_format_warning(file_type: str) -> str | None:
    """Return a warning message if the format has data loss implications."""
    warnings = {
        "obj": "OBJ format may recalculate face normals.",
    }
    return warnings.get(file_type)
