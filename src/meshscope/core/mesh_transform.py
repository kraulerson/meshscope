"""Mesh transforms: scale, rotate, and mirror with pure numpy."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

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
