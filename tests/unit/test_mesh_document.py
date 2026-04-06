"""Tests for MeshDocument."""

import numpy as np

from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.core.mesh_document import MeshDocument


def _make_mesh() -> MeshData:
    vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.float32)
    faces = np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]], dtype=np.uint32)
    normals = np.array(
        [[0, 0, -1], [0, -1, 0], [-1, 0, 0], [0.57, 0.57, 0.57]], dtype=np.float32
    )
    bb = BoundingBox(0, 0, 0, 1, 1, 1)
    meta = MeshMetadata(4, 4, bb, 3.46, 0.167, True)
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


class TestMeshDocument:
    def test_construction(self) -> None:
        mesh = _make_mesh()
        doc = MeshDocument(
            mesh=mesh,
            source_path="/tmp/test.stl",
            source_format="stl_binary",
            source_size_bytes=1234,
        )
        assert doc.mesh is mesh
        assert doc.source_path == "/tmp/test.stl"
        assert doc.source_format == "stl_binary"
        assert doc.source_size_bytes == 1234
        assert doc.warnings == []

    def test_original_mesh_is_independent_copy(self) -> None:
        mesh = _make_mesh()
        doc = MeshDocument(
            mesh=mesh,
            source_path="/tmp/test.stl",
            source_format="stl_binary",
            source_size_bytes=1234,
        )
        assert doc.original_mesh is not doc.mesh
        assert np.array_equal(doc.original_mesh.vertices, doc.mesh.vertices)

    def test_warnings_stored(self) -> None:
        mesh = _make_mesh()
        doc = MeshDocument(
            mesh=mesh,
            source_path="/tmp/test.obj",
            source_format="obj",
            source_size_bytes=500,
            warnings=["This OBJ file contains materials which are not supported."],
        )
        assert len(doc.warnings) == 1
        assert "materials" in doc.warnings[0]

    def test_undo_stack_exists_and_empty(self) -> None:
        mesh = _make_mesh()
        doc = MeshDocument(
            mesh=mesh,
            source_path="/tmp/test.stl",
            source_format="stl_binary",
            source_size_bytes=1234,
        )
        assert doc.undo_stack.can_undo() is False
