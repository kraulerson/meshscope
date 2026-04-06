"""Mutable session wrapper for a loaded mesh."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from meshscope.core.undo_stack import UndoStack

if TYPE_CHECKING:
    from meshscope.core.mesh_data import MeshData


class MeshDocument:
    """Represents a loaded mesh file with session state.

    Holds the current mesh, an immutable copy of the original,
    an undo stack, source file info, and user-visible warnings.
    """

    def __init__(
        self,
        mesh: MeshData,
        source_path: str,
        source_format: str,
        source_size_bytes: int,
        warnings: list[str] | None = None,
    ) -> None:
        self.mesh = mesh
        self.original_mesh = copy.deepcopy(mesh)
        self.source_path = source_path
        self.source_format = source_format
        self.source_size_bytes = source_size_bytes
        self.undo_stack = UndoStack()
        self.warnings: list[str] = warnings if warnings is not None else []
