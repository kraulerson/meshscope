"""Undo/redo stack for mesh state snapshots."""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from meshscope.core.mesh_data import MeshData


class UndoStack:
    """Ring buffer of MeshData snapshots supporting undo/redo.

    Usage: push the current mesh state before applying a transform;
    ``undo()`` returns it for restoration.

    When max_entries is reached, the oldest entry is evicted.
    Pushing a new entry after an undo clears the redo history.
    """

    def __init__(self, max_entries: int = 10) -> None:
        self._entries: deque[MeshData] = deque(maxlen=max_entries)
        self._redo_stack: list[MeshData] = []

    def push(self, mesh: MeshData) -> None:
        """Save a mesh state snapshot. Clears redo history."""
        self._entries.append(mesh)
        self._redo_stack.clear()

    def undo(self) -> MeshData | None:
        """Pop the most recent snapshot, moving it to redo stack."""
        if not self._entries:
            return None
        mesh = self._entries.pop()
        self._redo_stack.append(mesh)
        return mesh

    def redo(self) -> MeshData | None:
        """Restore the most recently undone snapshot."""
        if not self._redo_stack:
            return None
        mesh = self._redo_stack.pop()
        self._entries.append(mesh)
        return mesh

    def undo_swap(self, current: MeshData) -> MeshData | None:
        """Undo with proper current-state tracking.

        Pops the previous state from the undo stack, pushes the
        current state onto the redo stack, and returns the previous state.
        Returns None if nothing to undo.
        """
        if not self._entries:
            return None
        previous = self._entries.pop()
        self._redo_stack.append(current)
        return previous

    def redo_swap(self, current: MeshData) -> MeshData | None:
        """Redo with proper current-state tracking.

        Pops the next state from the redo stack, pushes the current
        state onto the undo stack, and returns the next state.
        Returns None if nothing to redo.
        """
        if not self._redo_stack:
            return None
        next_state = self._redo_stack.pop()
        self._entries.append(current)
        return next_state

    def can_undo(self) -> bool:
        return len(self._entries) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    @property
    def memory_bytes(self) -> int:
        """Estimate array memory used by stored snapshots (undo + redo)."""
        total = 0
        for mesh in self._entries:
            total += mesh.vertices.nbytes + mesh.faces.nbytes + mesh.normals.nbytes
        for mesh in self._redo_stack:
            total += mesh.vertices.nbytes + mesh.faces.nbytes + mesh.normals.nbytes
        return total
