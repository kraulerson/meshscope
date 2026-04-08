"""Tests for mesh transform logic."""

import numpy as np

from meshscope.core.exceptions import MeshTransformError
from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.core.mesh_transform import TransformResult, _recompute_metadata


class TestMeshTransformError:
    def test_has_user_message(self) -> None:
        err = MeshTransformError("Scale factor must be greater than zero.")
        assert err.user_message == "Scale factor must be greater than zero."

    def test_is_exception(self) -> None:
        err = MeshTransformError("msg")
        assert isinstance(err, Exception)

    def test_str_matches_user_message(self) -> None:
        err = MeshTransformError("msg")
        assert str(err) == "msg"


class TestTransformResultDataclass:
    def test_creation(self) -> None:
        verts = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)

        result = TransformResult(
            mesh=mesh,
            description="Scaled by 2.0x",
            warning=None,
        )
        assert result.description == "Scaled by 2.0x"
        assert result.warning is None

    def test_is_frozen(self) -> None:
        verts = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)
        result = TransformResult(mesh, "test", None)
        try:
            result.description = "changed"  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except AttributeError:
            pass

    def test_with_warning(self) -> None:
        verts = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)
        result = TransformResult(mesh, "Scaled by 20000.0x", "Model is now very large")
        assert result.warning == "Model is now very large"


def _make_cube_vertices() -> np.ndarray:
    """Unit cube 0-10mm on each axis."""
    return np.array(
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


def _make_cube_faces() -> np.ndarray:
    """12 triangles forming a watertight cube."""
    return np.array(
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


class TestRecomputeMetadata:
    def test_bounding_box(self) -> None:
        verts = _make_cube_vertices()
        faces = _make_cube_faces()
        meta = _recompute_metadata(verts, faces, is_manifold=True)
        assert meta.bounding_box.min_x == 0.0
        assert meta.bounding_box.max_x == 10.0
        assert meta.bounding_box.min_y == 0.0
        assert meta.bounding_box.max_y == 10.0
        assert meta.bounding_box.min_z == 0.0
        assert meta.bounding_box.max_z == 10.0

    def test_vertex_and_face_counts(self) -> None:
        verts = _make_cube_vertices()
        faces = _make_cube_faces()
        meta = _recompute_metadata(verts, faces, is_manifold=True)
        assert meta.vertex_count == 8
        assert meta.face_count == 12

    def test_surface_area(self) -> None:
        verts = _make_cube_vertices()
        faces = _make_cube_faces()
        meta = _recompute_metadata(verts, faces, is_manifold=True)
        # 10mm cube: 6 faces * 100mm^2 = 600mm^2
        assert abs(meta.surface_area_mm2 - 600.0) < 0.1

    def test_volume_manifold(self) -> None:
        verts = _make_cube_vertices()
        faces = _make_cube_faces()
        meta = _recompute_metadata(verts, faces, is_manifold=True)
        # 10mm cube: 1000mm^3
        assert meta.volume_mm3 is not None
        assert abs(meta.volume_mm3 - 1000.0) < 0.1

    def test_volume_non_manifold_is_none(self) -> None:
        verts = _make_cube_vertices()
        faces = _make_cube_faces()
        meta = _recompute_metadata(verts, faces, is_manifold=False)
        assert meta.volume_mm3 is None
