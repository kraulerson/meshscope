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


class TestUndoSwap:
    def test_undo_swap_returns_previous_state(self) -> None:
        stack = UndoStack(max_entries=10)
        mesh_a = _make_mesh(1.0)
        mesh_b = _make_mesh(2.0)
        stack.push(mesh_a)
        result = stack.undo_swap(mesh_b)
        assert result is mesh_a

    def test_undo_swap_saves_current_for_redo(self) -> None:
        stack = UndoStack(max_entries=10)
        mesh_a = _make_mesh(1.0)
        mesh_b = _make_mesh(2.0)
        stack.push(mesh_a)
        stack.undo_swap(mesh_b)
        assert stack.can_redo() is True

    def test_undo_swap_returns_none_when_empty(self) -> None:
        stack = UndoStack(max_entries=10)
        mesh_b = _make_mesh(2.0)
        assert stack.undo_swap(mesh_b) is None
        assert stack.can_redo() is False

    def test_redo_swap_returns_forward_state(self) -> None:
        stack = UndoStack(max_entries=10)
        mesh_a = _make_mesh(1.0)
        mesh_b = _make_mesh(2.0)
        stack.push(mesh_a)
        stack.undo_swap(mesh_b)
        # Now redo should give back mesh_b (the post-modification state)
        result = stack.redo_swap(mesh_a)
        assert result is mesh_b

    def test_redo_swap_returns_none_when_empty(self) -> None:
        stack = UndoStack(max_entries=10)
        mesh_a = _make_mesh(1.0)
        assert stack.redo_swap(mesh_a) is None
        assert stack.can_undo() is False

    def test_full_undo_redo_roundtrip(self) -> None:
        """push(A), current=B -> undo -> redo should restore B."""
        stack = UndoStack(max_entries=10)
        mesh_a = _make_mesh(1.0)
        mesh_b = _make_mesh(2.0)

        stack.push(mesh_a)
        # Simulate: current is now B

        # Undo: swap B for A
        restored = stack.undo_swap(mesh_b)
        assert restored is mesh_a

        # Redo: swap A for B
        redone = stack.redo_swap(mesh_a)
        assert redone is mesh_b

    def test_two_repairs_double_undo_double_redo(self) -> None:
        """push(A), current=B, push(B), current=C -> undo x2 -> redo x2."""
        stack = UndoStack(max_entries=10)
        mesh_a = _make_mesh(1.0)
        mesh_b = _make_mesh(2.0)
        mesh_c = _make_mesh(3.0)

        stack.push(mesh_a)
        # current = B
        stack.push(mesh_b)
        # current = C

        # Undo to B
        r1 = stack.undo_swap(mesh_c)
        assert r1 is mesh_b

        # Undo to A
        r2 = stack.undo_swap(mesh_b)
        assert r2 is mesh_a

        # Redo to B
        r3 = stack.redo_swap(mesh_a)
        assert r3 is mesh_b

        # Redo to C
        r4 = stack.redo_swap(mesh_b)
        assert r4 is mesh_c

    def test_push_after_undo_swap_clears_redo(self) -> None:
        """Undo then new push should clear redo history."""
        stack = UndoStack(max_entries=10)
        mesh_a = _make_mesh(1.0)
        mesh_b = _make_mesh(2.0)

        stack.push(mesh_a)
        stack.undo_swap(mesh_b)
        assert stack.can_redo() is True

        # New modification after undo -- redo should be cleared
        stack.push(mesh_a)
        assert stack.can_redo() is False
