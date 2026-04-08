"""Tests for mesh topology analysis."""

import numpy as np

from meshscope.core.mesh_analysis import analyze_mesh
from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata


def _make_cube_mesh() -> MeshData:
    """Create a watertight cube mesh (8 verts, 12 faces)."""
    vertices = np.array(
        [
            [0, 0, 0],
            [10, 0, 0],
            [10, 10, 0],
            [0, 10, 0],
            [0, 0, 10],
            [10, 0, 10],
            [10, 10, 10],
            [0, 10, 10],
        ],
        dtype=np.float32,
    )
    faces = np.array(
        [
            [0, 2, 1],
            [0, 3, 2],
            [4, 5, 6],
            [4, 6, 7],
            [0, 1, 5],
            [0, 5, 4],
            [2, 3, 7],
            [2, 7, 6],
            [0, 4, 7],
            [0, 7, 3],
            [1, 2, 6],
            [1, 6, 5],
        ],
        dtype=np.uint32,
    )
    normals = np.zeros((12, 3), dtype=np.float32)
    bb = BoundingBox(0, 0, 0, 10, 10, 10)
    meta = MeshMetadata(8, 12, bb, 600.0, 1000.0, True)
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


def _make_open_mesh() -> MeshData:
    """Create a mesh with open edges (remove 2 faces from cube = hole)."""
    vertices = np.array(
        [
            [0, 0, 0],
            [10, 0, 0],
            [10, 10, 0],
            [0, 10, 0],
            [0, 0, 10],
            [10, 0, 10],
            [10, 10, 10],
            [0, 10, 10],
        ],
        dtype=np.float32,
    )
    faces = np.array(
        [
            [0, 2, 1],
            [0, 3, 2],
            [4, 5, 6],
            [4, 6, 7],
            [0, 1, 5],
            [0, 5, 4],
            [2, 3, 7],
            [2, 7, 6],
            [0, 4, 7],
            [0, 7, 3],
        ],
        dtype=np.uint32,
    )
    normals = np.zeros((10, 3), dtype=np.float32)
    bb = BoundingBox(0, 0, 0, 10, 10, 10)
    meta = MeshMetadata(8, 10, bb, 500.0, None, False)
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


class TestAnalyzeMeshWatertight:
    def test_cube_is_manifold(self) -> None:
        result = analyze_mesh(_make_cube_mesh())
        assert result.is_manifold is True

    def test_cube_is_watertight(self) -> None:
        result = analyze_mesh(_make_cube_mesh())
        assert result.is_watertight is True

    def test_cube_no_holes(self) -> None:
        result = analyze_mesh(_make_cube_mesh())
        assert result.hole_count == 0

    def test_cube_no_open_edges(self) -> None:
        result = analyze_mesh(_make_cube_mesh())
        assert result.open_edge_count == 0

    def test_cube_no_degenerate_faces(self) -> None:
        result = analyze_mesh(_make_cube_mesh())
        assert result.degenerate_face_count == 0

    def test_cube_no_non_manifold_edges(self) -> None:
        result = analyze_mesh(_make_cube_mesh())
        assert result.non_manifold_edge_count == 0

    def test_cube_empty_edge_indices(self) -> None:
        result = analyze_mesh(_make_cube_mesh())
        assert len(result.open_edge_indices) == 0
        assert len(result.non_manifold_edge_indices) == 0
        assert len(result.degenerate_face_indices) == 0


class TestAnalyzeMeshOpenMesh:
    def test_open_mesh_not_manifold(self) -> None:
        result = analyze_mesh(_make_open_mesh())
        assert result.is_manifold is False

    def test_open_mesh_not_watertight(self) -> None:
        result = analyze_mesh(_make_open_mesh())
        assert result.is_watertight is False

    def test_open_mesh_has_open_edges(self) -> None:
        result = analyze_mesh(_make_open_mesh())
        assert result.open_edge_count > 0

    def test_open_mesh_has_holes(self) -> None:
        result = analyze_mesh(_make_open_mesh())
        assert result.hole_count > 0

    def test_open_edge_indices_match_count(self) -> None:
        result = analyze_mesh(_make_open_mesh())
        assert len(result.open_edge_indices) == result.open_edge_count

    def test_open_edge_indices_are_vertex_pairs(self) -> None:
        result = analyze_mesh(_make_open_mesh())
        assert result.open_edge_indices.ndim == 2
        assert result.open_edge_indices.shape[1] == 2


class TestAnalyzeMeshDegenerate:
    def test_degenerate_face_detected(self) -> None:
        """A face with zero area should be counted as degenerate."""
        vertices = np.array(
            [
                [0, 0, 0],
                [10, 0, 0],
                [10, 10, 0],
                [0, 10, 0],
                [5, 5, 0],  # degenerate: colinear with edge
            ],
            dtype=np.float32,
        )
        faces = np.array(
            [
                [0, 1, 2],
                [0, 2, 3],
                [0, 1, 0],  # degenerate face (repeated vertex)
            ],
            dtype=np.uint32,
        )
        normals = np.zeros((3, 3), dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 10, 10, 0)
        meta = MeshMetadata(5, 3, bb, 100.0, None, False)
        mesh = MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)
        result = analyze_mesh(mesh)
        assert result.degenerate_face_count >= 1
        assert len(result.degenerate_face_indices) >= 1


class TestMeshAnalysisDataclass:
    def test_is_frozen(self) -> None:
        result = analyze_mesh(_make_cube_mesh())
        try:
            result.hole_count = 99  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except AttributeError:
            pass

    def test_total_issues(self) -> None:
        result = analyze_mesh(_make_open_mesh())
        total = (
            result.open_edge_count
            + result.non_manifold_edge_count
            + result.degenerate_face_count
            + result.hole_count
        )
        assert total > 0
