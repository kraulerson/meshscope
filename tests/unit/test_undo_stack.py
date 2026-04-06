"""Tests for UndoStack."""

import numpy as np

from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.core.undo_stack import UndoStack


def _make_mesh(vertex_val: float = 0.0) -> MeshData:
    """Create a minimal MeshData for testing."""
    vertices = np.array([[vertex_val, 0, 0]], dtype=np.float32)
    faces = np.array([[0, 0, 0]], dtype=np.uint32)
    normals = np.array([[0, 0, 1]], dtype=np.float32)
    bb = BoundingBox(0, 0, 0, vertex_val, 0, 0)
    meta = MeshMetadata(1, 1, bb, 0.0, None, False)
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


class TestUndoStack:
    def test_empty_stack(self) -> None:
        stack = UndoStack(max_entries=10)
        assert stack.can_undo() is False
        assert stack.can_redo() is False
        assert stack.undo() is None
        assert stack.redo() is None

    def test_push_and_undo(self) -> None:
        stack = UndoStack(max_entries=10)
        mesh_v1 = _make_mesh(1.0)
        stack.push(mesh_v1)
        assert stack.can_undo() is True
        result = stack.undo()
        assert result is mesh_v1
        assert stack.can_undo() is False

    def test_undo_and_redo(self) -> None:
        stack = UndoStack(max_entries=10)
        mesh_v1 = _make_mesh(1.0)
        mesh_v2 = _make_mesh(2.0)
        stack.push(mesh_v1)
        stack.push(mesh_v2)
        assert stack.undo() is mesh_v2
        assert stack.can_redo() is True
        assert stack.redo() is mesh_v2

    def test_push_clears_redo_history(self) -> None:
        stack = UndoStack(max_entries=10)
        stack.push(_make_mesh(1.0))
        stack.push(_make_mesh(2.0))
        stack.undo()
        stack.push(_make_mesh(3.0))
        assert stack.can_redo() is False

    def test_max_entries_evicts_oldest(self) -> None:
        stack = UndoStack(max_entries=3)
        stack.push(_make_mesh(1.0))
        stack.push(_make_mesh(2.0))
        stack.push(_make_mesh(3.0))
        stack.push(_make_mesh(4.0))  # evicts mesh 1.0
        results = []
        while stack.can_undo():
            results.append(stack.undo())
        assert len(results) == 3
        assert results[0].vertices[0][0] == 4.0
        assert results[2].vertices[0][0] == 2.0  # mesh 1.0 was evicted

    def test_memory_bytes_tracks_usage(self) -> None:
        stack = UndoStack(max_entries=10)
        assert stack.memory_bytes == 0
        stack.push(_make_mesh(1.0))
        assert stack.memory_bytes > 0
