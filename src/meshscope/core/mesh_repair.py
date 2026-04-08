"""Basic mesh repair: plan and apply repairs for common 3D printing issues."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import trimesh

if TYPE_CHECKING:
    from meshscope.core.mesh_analysis import MeshAnalysis
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


def plan_repair(analysis: MeshAnalysis, mesh: MeshData) -> RepairPlan:
    """Compute what repairs would be applied without modifying the mesh.

    Runs a trial repair on a copy to get accurate counts.
    """
    tm = trimesh.Trimesh(
        vertices=np.array(mesh.vertices, dtype=np.float64),
        faces=np.array(mesh.faces, dtype=np.int64),
        process=False,
    )
    original_face_count = len(tm.faces)

    trial = tm.copy()

    # 1. Remove degenerate faces
    degen = analysis.degenerate_face_count
    if degen > 0:
        trial.remove_degenerate_faces()

    # 2. Fix normals — count faces that changed winding
    faces_before_normals = trial.faces.copy()
    trimesh.repair.fix_normals(trial)
    flipped_count = int(np.sum(np.any(trial.faces != faces_before_normals, axis=1)))

    # 3. Fill holes
    holes = analysis.hole_count
    if holes > 0:
        trimesh.repair.fill_holes(trial)

    estimated_delta = len(trial.faces) - original_face_count
    high_impact = (
        abs(estimated_delta) > 0.05 * original_face_count
        if original_face_count > 0
        else False
    )

    logger.info(
        "Repair plan: flipped=%d holes=%d degen=%d delta=%d",
        flipped_count,
        holes,
        degen,
        estimated_delta,
    )

    return RepairPlan(
        flipped_normal_count=flipped_count,
        holes_to_fill=holes,
        degenerate_faces_to_remove=degen,
        estimated_face_delta=estimated_delta,
        high_impact_warning=high_impact,
    )
