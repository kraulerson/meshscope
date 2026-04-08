"""Tests for mesh transform logic."""

import numpy as np

from meshscope.core.exceptions import MeshTransformError
from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.core.mesh_transform import TransformResult


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
