"""Basic mesh repair: plan and apply repairs for common 3D printing issues."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from meshscope.core.mesh_data import MeshData

logger = logging.getLogger("meshscope.core.mesh_repair")


@dataclass(frozen=True)
class RepairPlan:
    """Summary of planned repair operations."""

    flipped_normal_count: int
    holes_to_fill: int
    degenerate_faces_to_remove: int
    estimated_face_delta: int
    high_impact_warning: bool


@dataclass(frozen=True)
class RepairResult:
    """Result of applying mesh repairs."""

    mesh: MeshData
    normals_fixed: int
    holes_filled: int
    degenerate_faces_removed: int
    fully_repaired: bool
    remaining_issues: str | None
