"""On-demand mesh topology analysis."""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt
import trimesh

if TYPE_CHECKING:
    from meshscope.core.mesh_data import MeshData

logger = logging.getLogger("meshscope.core.mesh_analysis")


@dataclass(frozen=True)
class MeshAnalysis:
    """Results of mesh topology analysis."""

    is_manifold: bool
    is_watertight: bool
    hole_count: int
    open_edge_count: int
    degenerate_face_count: int
    non_manifold_edge_count: int
    open_edge_indices: npt.NDArray[np.int64]  # shape (N, 2) vertex index pairs
    non_manifold_edge_indices: npt.NDArray[np.int64]  # shape (N, 2) vertex index pairs
    degenerate_face_indices: npt.NDArray[np.int64]  # shape (N,) face indices


def analyze_mesh(mesh: MeshData) -> MeshAnalysis:
    """Analyze mesh topology and return detailed diagnostics."""
    tm = trimesh.Trimesh(
        vertices=np.array(mesh.vertices, dtype=np.float64),
        faces=np.array(mesh.faces, dtype=np.int64),
        process=False,
    )

    is_manifold = bool(tm.is_volume)
    is_watertight = bool(tm.is_watertight)

    # Edge analysis: count faces per edge
    all_edges = tm.edges.copy()
    all_edges.sort(axis=1)
    edge_tuples = [tuple(e) for e in all_edges]
    edge_counts = Counter(edge_tuples)

    # Open edges: shared by exactly 1 face
    open_edges = np.array(
        [list(e) for e, c in edge_counts.items() if c == 1],
        dtype=np.int64,
    ).reshape(-1, 2)

    # Non-manifold edges: shared by >2 faces
    nm_edges = np.array(
        [list(e) for e, c in edge_counts.items() if c > 2],
        dtype=np.int64,
    ).reshape(-1, 2)

    # Degenerate faces: zero area
    areas = tm.area_faces
    degen_indices = np.where(areas < 1e-10)[0]

    # Hole count: connected components of open/boundary edges
    hole_count = _count_holes(open_edges) if len(open_edges) > 0 else 0

    logger.info(
        "Analysis: manifold=%s watertight=%s holes=%d open=%d nm=%d degen=%d",
        is_manifold,
        is_watertight,
        hole_count,
        len(open_edges),
        len(nm_edges),
        len(degen_indices),
    )

    return MeshAnalysis(
        is_manifold=is_manifold,
        is_watertight=is_watertight,
        hole_count=hole_count,
        open_edge_count=len(open_edges),
        degenerate_face_count=len(degen_indices),
        non_manifold_edge_count=len(nm_edges),
        open_edge_indices=open_edges,
        non_manifold_edge_indices=nm_edges,
        degenerate_face_indices=degen_indices,
    )


def _count_holes(boundary_edges: npt.NDArray[np.int64]) -> int:
    """Count boundary loops (holes) from boundary edge array."""
    if len(boundary_edges) == 0:
        return 0

    # Build adjacency from boundary edges
    adj: dict[int, set[int]] = {}
    for v0, v1 in boundary_edges:
        adj.setdefault(int(v0), set()).add(int(v1))
        adj.setdefault(int(v1), set()).add(int(v0))

    # Count connected components via BFS
    visited: set[int] = set()
    components = 0
    for start in adj:
        if start in visited:
            continue
        components += 1
        queue = [start]
        while queue:
            node = queue.pop()
            if node in visited:
                continue
            visited.add(node)
            queue.extend(adj.get(node, set()) - visited)
    return components
