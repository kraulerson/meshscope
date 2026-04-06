"""Immutable data structures for mesh geometry and metadata."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt


@dataclass(frozen=True)
class BoundingBox:
    """Axis-aligned bounding box in mm."""

    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    @property
    def size_x(self) -> float:
        return self.max_x - self.min_x

    @property
    def size_y(self) -> float:
        return self.max_y - self.min_y

    @property
    def size_z(self) -> float:
        return self.max_z - self.min_z

    @property
    def center(self) -> tuple[float, float, float]:
        return (
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2,
            (self.min_z + self.max_z) / 2,
        )


@dataclass(frozen=True)
class MeshMetadata:
    """Computed mesh properties."""

    vertex_count: int
    face_count: int
    bounding_box: BoundingBox
    surface_area_mm2: float
    volume_mm3: float | None  # None if non-manifold
    is_manifold: bool


@dataclass(frozen=True)
class MeshData:
    """Immutable mesh geometry with computed metadata.

    vertices: float32, shape (N, 3) — positions in mm
    faces: uint32, shape (M, 3) — triangle vertex indices (0-based)
    normals: float32, shape (M, 3) — per-face unit normals
    """

    vertices: npt.NDArray[np.float32]
    faces: npt.NDArray[np.uint32]
    normals: npt.NDArray[np.float32]
    metadata: MeshMetadata
