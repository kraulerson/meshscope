"""Mesh file loading: validation, parsing, and MeshDocument construction."""

from __future__ import annotations

import logging
import os
import struct
import zipfile
from pathlib import Path

import numpy as np
import trimesh

from meshscope.core.exceptions import (
    CorruptFileError,
    EmptyMeshError,
    FileNotFoundError_,
    FileNotReadableError,
    FileTooLargeError,
    UnsupportedFormatError,
)
from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.core.mesh_document import MeshDocument

logger = logging.getLogger("meshscope.core.mesh_loader")

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


OBJ_UNSUPPORTED_DIRECTIVES: dict[str, str] = {
    "mtllib": "materials",
    "usemtl": "materials",
    "vt": "texture coordinates",
    "g": "groups",
    "s": "smooth shading",
    "cstype": "curves",
    "curv": "curves",
    "surf": "surfaces",
}


def _detect_obj_warnings(path: Path) -> list[str]:
    """Scan an OBJ file for unsupported directives."""
    found: set[str] = set()
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                directive = stripped.split()[0]
                if directive in OBJ_UNSUPPORTED_DIRECTIVES:
                    found.add(OBJ_UNSUPPORTED_DIRECTIVES[directive])
    except OSError:
        pass  # File reading issues handled elsewhere
    if found:
        items = ", ".join(sorted(found))
        return [
            f"This OBJ file contains {items} which are not supported. "
            "These will be ignored."
        ]
    return []


def _check_unit_mismatch(metadata: MeshMetadata) -> str | None:
    """Return a warning string if dimensions suggest a unit mismatch."""
    if metadata.face_count == 0:
        return None

    bb = metadata.bounding_box
    all_tiny = bb.size_x < 1.0 and bb.size_y < 1.0 and bb.size_z < 1.0
    any_huge = bb.size_x > 10000 or bb.size_y > 10000 or bb.size_z > 10000

    if all_tiny or any_huge:
        return (
            "Dimensions may indicate a unit mismatch. "
            "Consider scaling by 25.4 (inches to mm) or 0.0394 (mm to inches)."
        )
    return None


def _validate_binary_stl(path: Path) -> None:
    """Pre-parse validation for binary STL files.

    Binary STL format: 80-byte header + 4-byte triangle count (uint32)
    + N * 50 bytes (triangle data). If the declared triangle count
    does not match the actual file size, the file is corrupt.
    If the declared count is 0, the mesh is empty.

    ASCII STL files (starting with 'solid') are skipped.

    Raises CorruptFileError or EmptyMeshError as appropriate.
    """
    file_size = path.stat().st_size

    # Too small to even have a binary STL header
    if file_size < 84:
        raise CorruptFileError(f"Invalid STL: file is too small ({file_size} bytes).")

    with open(path, "rb") as f:
        header = f.read(80)
        # If header starts with 'solid', this might be ASCII STL — skip
        # binary validation (trimesh will handle ASCII parsing)
        if header.lstrip(b"\x00").startswith(b"solid"):
            return
        count_bytes = f.read(4)

    triangle_count = struct.unpack("<I", count_bytes)[0]

    if triangle_count == 0:
        raise EmptyMeshError(
            "File parsed successfully but contains no geometry (0 faces)."
        )

    expected_size = 84 + triangle_count * 50
    if file_size < expected_size:
        raise CorruptFileError(
            f"Invalid STL: header declares {triangle_count} triangles "
            f"but file is truncated ({file_size} bytes, "
            f"expected {expected_size})."
        )


def _trimesh_to_mesh_data(tm_mesh: trimesh.Trimesh) -> MeshData:
    """Convert a trimesh.Trimesh to our MeshData.

    Validates vertex data and face indices before conversion.
    Raises CorruptFileError if data is invalid.
    """
    vertices = np.asarray(tm_mesh.vertices, dtype=np.float32)
    faces = np.asarray(tm_mesh.faces, dtype=np.uint32)

    # Validate vertices: reject NaN or Inf
    if np.any(np.isnan(vertices)):
        raise CorruptFileError("Mesh contains NaN vertex coordinates.")
    if np.any(np.isinf(vertices)):
        raise CorruptFileError("Mesh contains Inf vertex coordinates.")

    # Validate face indices: must reference existing vertices
    if len(faces) > 0 and np.max(faces) >= len(vertices):
        raise CorruptFileError(
            f"Mesh has face referencing vertex {int(np.max(faces))} "
            f"but only {len(vertices)} vertices exist."
        )

    normals = np.asarray(tm_mesh.face_normals, dtype=np.float32)

    bounds = tm_mesh.bounds  # [[min_x, min_y, min_z], [max_x, max_y, max_z]]
    bounding_box = BoundingBox(
        min_x=float(bounds[0][0]),
        min_y=float(bounds[0][1]),
        min_z=float(bounds[0][2]),
        max_x=float(bounds[1][0]),
        max_y=float(bounds[1][1]),
        max_z=float(bounds[1][2]),
    )

    is_manifold = bool(tm_mesh.is_volume)
    volume = float(tm_mesh.volume) if is_manifold else None

    metadata = MeshMetadata(
        vertex_count=len(vertices),
        face_count=len(faces),
        bounding_box=bounding_box,
        surface_area_mm2=float(tm_mesh.area),
        volume_mm3=volume,
        is_manifold=is_manifold,
    )

    return MeshData(
        vertices=vertices,
        faces=faces,
        normals=normals,
        metadata=metadata,
    )


def load_mesh(path: str | Path) -> MeshDocument:
    """Load a mesh file and return a MeshDocument.

    Validates the path, parses via trimesh, computes metadata,
    and checks for warnings (OBJ directives, unit mismatch).

    Raises MeshLoadError subclasses on failure.
    """
    path = Path(path)
    validate_path(path)
    file_type = detect_format(path)
    source_size = path.stat().st_size
    warnings: list[str] = []

    # Pre-parse validation for binary STL (trimesh silently swallows
    # corrupt/empty binary STL files as empty Scenes)
    if file_type == "stl":
        _validate_binary_stl(path)

    # OBJ directive scan (before parsing)
    if file_type == "obj":
        warnings.extend(_detect_obj_warnings(path))

    # Parse with trimesh
    try:
        result = trimesh.load(str(path), file_type=file_type)
    except zipfile.BadZipFile as e:
        raise CorruptFileError(
            "Invalid 3MF: unable to extract archive. File may be corrupt."
        ) from e
    except Exception as e:
        raise CorruptFileError(f"Invalid {file_type.upper()}: {e}") from e

    # Handle Scene (3MF returns Scene; others may too in edge cases)
    if isinstance(result, trimesh.Scene):
        geometries = list(result.geometry.values())
        if not geometries:
            raise EmptyMeshError(
                "File parsed successfully but contains no geometry (0 faces)."
            )
        if len(geometries) > 1:
            warnings.append(
                f"This 3MF file contains {len(geometries)} meshes. "
                "Only the first was loaded."
            )
        result = geometries[0]

    # Validate we have a proper mesh
    if not isinstance(result, trimesh.Trimesh):
        raise CorruptFileError(
            f"Invalid {file_type.upper()}: file did not produce a valid mesh."
        )

    if len(result.faces) == 0:
        raise EmptyMeshError(
            "File parsed successfully but contains no geometry (0 faces)."
        )

    # Convert to our data model
    mesh_data = _trimesh_to_mesh_data(result)

    # Check unit mismatch
    unit_warning = _check_unit_mismatch(mesh_data.metadata)
    if unit_warning:
        warnings.append(unit_warning)

    logger.info(
        "Loaded mesh: %s (%s, %d vertices, %d faces)",
        path.name,
        file_type,
        mesh_data.metadata.vertex_count,
        mesh_data.metadata.face_count,
    )

    return MeshDocument(
        mesh=mesh_data,
        source_path=str(path),
        source_format=file_type,
        source_size_bytes=source_size,
        warnings=warnings,
    )
