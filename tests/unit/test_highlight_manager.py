"""Tests for mesh problem highlight VTK actors."""

import numpy as np

from meshscope.core.mesh_analysis import MeshAnalysis
from meshscope.vtk_adapter.highlight_manager import HighlightManager


def _make_clean_analysis() -> MeshAnalysis:
    return MeshAnalysis(
        is_manifold=True,
        is_watertight=True,
        hole_count=0,
        open_edge_count=0,
        degenerate_face_count=0,
        non_manifold_edge_count=0,
        open_edge_indices=np.zeros((0, 2), dtype=np.int64),
        non_manifold_edge_indices=np.zeros((0, 2), dtype=np.int64),
        degenerate_face_indices=np.zeros((0,), dtype=np.int64),
    )


def _make_problem_analysis() -> MeshAnalysis:
    return MeshAnalysis(
        is_manifold=False,
        is_watertight=False,
        hole_count=1,
        open_edge_count=2,
        degenerate_face_count=1,
        non_manifold_edge_count=1,
        open_edge_indices=np.array([[0, 1], [1, 2]], dtype=np.int64),
        non_manifold_edge_indices=np.array([[2, 3]], dtype=np.int64),
        degenerate_face_indices=np.array([0], dtype=np.int64),
    )


def _make_vertices() -> np.ndarray:
    return np.array(
        [
            [0, 0, 0],
            [10, 0, 0],
            [10, 10, 0],
            [0, 10, 0],
        ],
        dtype=np.float32,
    )


def _make_faces() -> np.ndarray:
    return np.array([[0, 1, 2], [0, 2, 3]], dtype=np.uint32)


class TestHighlightManagerClean:
    def test_no_actors_for_clean_mesh(self) -> None:
        mgr = HighlightManager()
        actors = mgr.create_actors(
            _make_clean_analysis(), _make_vertices(), _make_faces()
        )
        assert len(actors) == 0


class TestHighlightManagerProblems:
    def test_creates_actors_for_problems(self) -> None:
        mgr = HighlightManager()
        actors = mgr.create_actors(
            _make_problem_analysis(), _make_vertices(), _make_faces()
        )
        assert len(actors) > 0

    def test_creates_actor_per_problem_type(self) -> None:
        mgr = HighlightManager()
        # Has open edges + non-manifold + degenerate = 3 actor groups
        actors = mgr.create_actors(
            _make_problem_analysis(), _make_vertices(), _make_faces()
        )
        assert len(actors) == 3

    def test_open_edges_only(self) -> None:
        analysis = MeshAnalysis(
            is_manifold=False,
            is_watertight=False,
            hole_count=1,
            open_edge_count=2,
            degenerate_face_count=0,
            non_manifold_edge_count=0,
            open_edge_indices=np.array([[0, 1], [1, 2]], dtype=np.int64),
            non_manifold_edge_indices=np.zeros((0, 2), dtype=np.int64),
            degenerate_face_indices=np.zeros((0,), dtype=np.int64),
        )
        mgr = HighlightManager()
        actors = mgr.create_actors(analysis, _make_vertices(), _make_faces())
        assert len(actors) == 1  # only open edges actor
