"""Basic mesh repair: plan and apply repairs for common 3D printing issues."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import trimesh

from meshscope.core.exceptions import MeshRepairError
from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata

if TYPE_CHECKING:
    from meshscope.core.mesh_analysis import MeshAnalysis

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
    trimesh.repair.fix_normals(trial)  # type: ignore[no-untyped-call]
    flipped_count = int(np.sum(np.any(trial.faces != faces_before_normals, axis=1)))

    # 3. Fill holes
    holes = analysis.hole_count
    if holes > 0:
        trimesh.repair.fill_holes(trial)  # type: ignore[no-untyped-call]

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


def apply_repair(mesh: MeshData, plan: RepairPlan) -> RepairResult:
    """Apply planned repairs to a mesh and return the repaired result.

    Operations are applied in order:
    1. Remove degenerate faces (zero-area)
    2. Fix normals (consistent outward orientation)
    3. Fill holes

    Raises MeshRepairError if all operations fail.
    """
    tm = trimesh.Trimesh(
        vertices=np.array(mesh.vertices, dtype=np.float64),
        faces=np.array(mesh.faces, dtype=np.int64),
        process=False,
    )

    normals_fixed = 0
    holes_filled = 0
    degenerate_removed = 0
    remaining: list[str] = []

    # 1. Remove degenerate faces
    if plan.degenerate_faces_to_remove > 0:
        faces_before = len(tm.faces)
        try:
            tm.remove_degenerate_faces()
            degenerate_removed = faces_before - len(tm.faces)
        except Exception:
            remaining.append("Could not remove degenerate faces")
            logger.exception("Failed to remove degenerate faces")

    # 2. Fix normals
    if plan.flipped_normal_count > 0:
        try:
            faces_before_fix = tm.faces.copy()
            trimesh.repair.fix_normals(tm)  # type: ignore[no-untyped-call]
            normals_fixed = int(np.sum(np.any(tm.faces != faces_before_fix, axis=1)))
        except Exception:
            remaining.append("Could not fix normals")
            logger.exception("Failed to fix normals")

    # 3. Fill holes
    if plan.holes_to_fill > 0:
        try:
            faces_before_fill = len(tm.faces)
            trimesh.repair.fill_holes(tm)  # type: ignore[no-untyped-call]
            faces_added = len(tm.faces) - faces_before_fill
            if faces_added > 0:
                holes_filled = plan.holes_to_fill
            else:
                remaining.append("Holes could not be filled (too large or complex)")
        except Exception:
            remaining.append("Could not fill holes")
            logger.exception("Failed to fill holes")

    # Check if all operations failed
    total_fixed = normals_fixed + holes_filled + degenerate_removed
    if total_fixed == 0 and remaining:
        raise MeshRepairError(
            "All repair operations failed. Original mesh is unchanged."
        )

    # Build new MeshData from repaired trimesh
    repaired_vertices = np.asarray(tm.vertices, dtype=np.float32)
    repaired_faces = np.asarray(tm.faces, dtype=np.uint32)
    repaired_normals = np.asarray(tm.face_normals, dtype=np.float32)

    if np.any(np.isnan(repaired_vertices)):
        raise MeshRepairError(
            "Repair produced invalid geometry. Original mesh is unchanged."
        )

    bounds = tm.bounds
    bbox = BoundingBox(
        min_x=float(bounds[0][0]),
        min_y=float(bounds[0][1]),
        min_z=float(bounds[0][2]),
        max_x=float(bounds[1][0]),
        max_y=float(bounds[1][1]),
        max_z=float(bounds[1][2]),
    )
    is_manifold = bool(tm.is_volume)
    volume = float(tm.volume) if is_manifold else None

    metadata = MeshMetadata(
        vertex_count=len(repaired_vertices),
        face_count=len(repaired_faces),
        bounding_box=bbox,
        surface_area_mm2=float(tm.area),
        volume_mm3=volume,
        is_manifold=is_manifold,
    )

    new_mesh = MeshData(
        vertices=repaired_vertices,
        faces=repaired_faces,
        normals=repaired_normals,
        metadata=metadata,
    )

    remaining_text = "; ".join(remaining) if remaining else None

    return RepairResult(
        mesh=new_mesh,
        normals_fixed=normals_fixed,
        holes_filled=holes_filled,
        degenerate_faces_removed=degenerate_removed,
        fully_repaired=len(remaining) == 0,
        remaining_issues=remaining_text,
    )
