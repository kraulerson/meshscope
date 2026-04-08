"""Mesh transforms: scale, rotate, and mirror with pure numpy."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from meshscope.core.exceptions import MeshTransformError
from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata

logger = logging.getLogger("meshscope.core.mesh_transform")


@dataclass(frozen=True)
class TransformResult:
    """Result of applying a mesh transform."""

    mesh: MeshData
    description: str
    warning: str | None


def _recompute_metadata(
    vertices: np.ndarray,
    faces: np.ndarray,
    *,
    is_manifold: bool,
) -> MeshMetadata:
    """Recompute mesh metadata from raw arrays.

    Uses pure numpy: bounding box from min/max, surface area from
    cross-product magnitudes, volume from signed tetrahedra.
    """
    bbox = BoundingBox(
        min_x=float(vertices[:, 0].min()),
        min_y=float(vertices[:, 1].min()),
        min_z=float(vertices[:, 2].min()),
        max_x=float(vertices[:, 0].max()),
        max_y=float(vertices[:, 1].max()),
        max_z=float(vertices[:, 2].max()),
    )

    # Surface area: sum of triangle areas
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]
    cross = np.cross(v1 - v0, v2 - v0)
    triangle_areas = np.linalg.norm(cross, axis=1) / 2.0
    surface_area = float(triangle_areas.sum())

    # Volume: signed tetrahedron method (only if manifold)
    volume: float | None = None
    if is_manifold:
        # Each triangle forms a tetrahedron with the origin
        # Volume contribution = v0 . (v1 x v2) / 6
        dot = np.einsum("ij,ij->i", v0, np.cross(v1, v2))
        volume = abs(float(dot.sum() / 6.0))

    return MeshMetadata(
        vertex_count=len(vertices),
        face_count=len(faces),
        bounding_box=bbox,
        surface_area_mm2=surface_area,
        volume_mm3=volume,
        is_manifold=is_manifold,
    )


def _recompute_normals(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """Recompute per-face unit normals from vertices and faces."""
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]
    cross = np.cross(v1 - v0, v2 - v0)
    norms = np.linalg.norm(cross, axis=1, keepdims=True)
    # Avoid division by zero for degenerate faces
    norms = np.where(norms < 1e-10, 1.0, norms)
    return (cross / norms).astype(np.float32)


def scale_mesh(mesh: MeshData, factor: float) -> TransformResult:
    """Scale all vertices by a uniform factor.

    Raises MeshTransformError if factor <= 0.
    """
    if factor <= 0:
        raise MeshTransformError("Scale factor must be greater than zero.")

    new_vertices = (mesh.vertices * factor).astype(np.float32)
    # Uniform scaling preserves normal directions — no need to recompute
    new_normals = mesh.normals.copy()
    new_meta = _recompute_metadata(
        new_vertices, mesh.faces, is_manifold=mesh.metadata.is_manifold
    )

    new_mesh = MeshData(
        vertices=new_vertices,
        faces=mesh.faces.copy(),
        normals=new_normals,
        metadata=new_meta,
    )

    warning: str | None = None
    if factor > 10000:
        max_dim = max(
            new_meta.bounding_box.max_x - new_meta.bounding_box.min_x,
            new_meta.bounding_box.max_y - new_meta.bounding_box.min_y,
            new_meta.bounding_box.max_z - new_meta.bounding_box.min_z,
        )
        warning = f"Model is now very large ({max_dim:.0f}mm on longest axis)"

    logger.info("Scale: factor=%.4f", factor)

    return TransformResult(
        mesh=new_mesh,
        description=f"Scaled by {factor}x",
        warning=warning,
    )


def rotate_mesh(mesh: MeshData, axis: str, degrees: float) -> TransformResult:
    """Rotate mesh around its center of mass by degrees around the given axis.

    Raises MeshTransformError if axis is not x, y, or z.
    """
    axis_lower = axis.lower()
    if axis_lower not in ("x", "y", "z"):
        raise MeshTransformError(f"Invalid axis '{axis}'. Must be 'x', 'y', or 'z'.")

    radians = np.radians(degrees)
    cos_a = np.cos(radians)
    sin_a = np.sin(radians)

    if axis_lower == "x":
        rot = np.array(
            [
                [1, 0, 0],
                [0, cos_a, -sin_a],
                [0, sin_a, cos_a],
            ],
            dtype=np.float64,
        )
    elif axis_lower == "y":
        rot = np.array(
            [
                [cos_a, 0, sin_a],
                [0, 1, 0],
                [-sin_a, 0, cos_a],
            ],
            dtype=np.float64,
        )
    else:  # z
        rot = np.array(
            [
                [cos_a, -sin_a, 0],
                [sin_a, cos_a, 0],
                [0, 0, 1],
            ],
            dtype=np.float64,
        )

    # Rotate around center of mass
    center = mesh.vertices.mean(axis=0).astype(np.float64)
    centered = mesh.vertices.astype(np.float64) - center
    rotated = (centered @ rot.T) + center
    new_vertices = rotated.astype(np.float32)

    new_normals = _recompute_normals(new_vertices, mesh.faces)
    new_meta = _recompute_metadata(
        new_vertices, mesh.faces, is_manifold=mesh.metadata.is_manifold
    )

    new_mesh = MeshData(
        vertices=new_vertices,
        faces=mesh.faces.copy(),
        normals=new_normals,
        metadata=new_meta,
    )

    logger.info("Rotate: axis=%s degrees=%.1f", axis_lower, degrees)

    return TransformResult(
        mesh=new_mesh,
        description=f"Rotated {degrees}\u00b0 around {axis_lower.upper()} axis",
        warning=None,
    )


def mirror_mesh(mesh: MeshData, axis: str) -> TransformResult:
    """Mirror mesh across the given axis plane through the model center.

    Reverses face winding order to maintain outward-facing normals.
    Raises MeshTransformError if axis is not x, y, or z.
    """
    axis_lower = axis.lower()
    if axis_lower not in ("x", "y", "z"):
        raise MeshTransformError(f"Invalid axis '{axis}'. Must be 'x', 'y', or 'z'.")

    axis_index = {"x": 0, "y": 1, "z": 2}[axis_lower]
    center = float(mesh.vertices[:, axis_index].mean())

    new_vertices = mesh.vertices.copy()
    new_vertices[:, axis_index] = 2 * center - new_vertices[:, axis_index]

    # Reverse face winding to fix normals (swap columns 1 and 2)
    new_faces = mesh.faces.copy()
    new_faces[:, 1], new_faces[:, 2] = mesh.faces[:, 2].copy(), mesh.faces[:, 1].copy()

    new_normals = _recompute_normals(new_vertices, new_faces)
    new_meta = _recompute_metadata(
        new_vertices, new_faces, is_manifold=mesh.metadata.is_manifold
    )

    new_mesh = MeshData(
        vertices=new_vertices,
        faces=new_faces,
        normals=new_normals,
        metadata=new_meta,
    )

    axis_labels = {"x": "YZ", "y": "XZ", "z": "XY"}
    logger.info("Mirror: axis=%s plane=%s", axis_lower, axis_labels[axis_lower])

    plane = axis_labels[axis_lower]
    ax_upper = axis_lower.upper()
    return TransformResult(
        mesh=new_mesh,
        description=f"Mirrored across {plane} plane ({ax_upper} axis)",
        warning=None,
    )
