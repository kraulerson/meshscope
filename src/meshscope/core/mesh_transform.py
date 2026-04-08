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
