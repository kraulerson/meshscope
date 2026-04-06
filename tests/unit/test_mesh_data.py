"""Tests for mesh data structures."""

import typing

import numpy as np

from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata


class TestBoundingBox:
    def test_construction(self) -> None:
        bb = BoundingBox(
            min_x=0.0,
            min_y=0.0,
            min_z=0.0,
            max_x=10.0,
            max_y=20.0,
            max_z=30.0,
        )
        assert bb.min_x == 0.0
        assert bb.max_z == 30.0

    def test_size_properties(self) -> None:
        bb = BoundingBox(
            min_x=-5.0,
            min_y=-10.0,
            min_z=-15.0,
            max_x=5.0,
            max_y=10.0,
            max_z=15.0,
        )
        assert bb.size_x == 10.0
        assert bb.size_y == 20.0
        assert bb.size_z == 30.0

    def test_center_property(self) -> None:
        bb = BoundingBox(
            min_x=0.0,
            min_y=0.0,
            min_z=0.0,
            max_x=10.0,
            max_y=20.0,
            max_z=30.0,
        )
        cx, cy, cz = bb.center
        assert cx == 5.0
        assert cy == 10.0
        assert cz == 15.0

    def test_is_frozen(self) -> None:
        bb = BoundingBox(
            min_x=0.0,
            min_y=0.0,
            min_z=0.0,
            max_x=1.0,
            max_y=1.0,
            max_z=1.0,
        )
        try:
            bb.min_x = 99.0  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except AttributeError:
            pass


class TestMeshMetadata:
    def test_construction(self) -> None:
        bb = BoundingBox(
            min_x=0.0,
            min_y=0.0,
            min_z=0.0,
            max_x=10.0,
            max_y=10.0,
            max_z=10.0,
        )
        meta = MeshMetadata(
            vertex_count=8,
            face_count=12,
            bounding_box=bb,
            surface_area_mm2=600.0,
            volume_mm3=1000.0,
            is_manifold=True,
        )
        assert meta.vertex_count == 8
        assert meta.face_count == 12
        assert meta.volume_mm3 == 1000.0
        assert meta.is_manifold is True

    def test_non_manifold_volume_is_none(self) -> None:
        bb = BoundingBox(
            min_x=0.0,
            min_y=0.0,
            min_z=0.0,
            max_x=1.0,
            max_y=1.0,
            max_z=1.0,
        )
        meta = MeshMetadata(
            vertex_count=4,
            face_count=2,
            bounding_box=bb,
            surface_area_mm2=1.0,
            volume_mm3=None,
            is_manifold=False,
        )
        assert meta.volume_mm3 is None
        assert meta.is_manifold is False


class TestMeshData:
    def test_construction(self) -> None:
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float32)
        faces = np.array([[0, 1, 2]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(
            min_x=0.0,
            min_y=0.0,
            min_z=0.0,
            max_x=1.0,
            max_y=1.0,
            max_z=0.0,
        )
        meta = MeshMetadata(
            vertex_count=3,
            face_count=1,
            bounding_box=bb,
            surface_area_mm2=0.5,
            volume_mm3=None,
            is_manifold=False,
        )
        mesh = MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)
        assert mesh.vertices.shape == (3, 3)
        assert mesh.faces.shape == (1, 3)
        assert mesh.normals.shape == (1, 3)
        assert mesh.metadata.vertex_count == 3

    def test_vertex_dtype_is_float32(self) -> None:
        vertices = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)
        assert mesh.vertices.dtype == np.float32

    def test_face_dtype_is_uint32(self) -> None:
        vertices = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)
        assert mesh.faces.dtype == np.uint32

    def test_ndarray_fields_have_dtype_type_parameters(self) -> None:
        """Regression: bare np.ndarray fails mypy strict — must use NDArray[dtype]."""
        hints = typing.get_type_hints(MeshData)
        for field in ("vertices", "faces", "normals"):
            assert hasattr(hints[field], "__args__"), (
                f"MeshData.{field}: use npt.NDArray[dtype], not bare np.ndarray"
            )
