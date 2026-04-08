"""Mutable session wrapper for a loaded mesh."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from meshscope.core.undo_stack import UndoStack

if TYPE_CHECKING:
    from meshscope.core.mesh_analysis import MeshAnalysis
    from meshscope.core.mesh_data import MeshData, Measurement


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
        self.analysis: MeshAnalysis | None = None
        self.measurements: list[Measurement] = []

    def add_measurement(self, measurement: Measurement) -> None:
        """Add a measurement. If 3 already exist, remove the oldest (FIFO)."""
        if len(self.measurements) >= 3:
            self.measurements.pop(0)
        self.measurements.append(measurement)

    def clear_measurements(self) -> None:
        """Remove all measurements."""
        self.measurements.clear()

    def next_measurement_index(self) -> int:
        """Return the next available measurement index (1, 2, or 3).

        If fewer than 3 measurements exist, returns the lowest unused index.
        If 3 exist, returns the index of the oldest (which will be evicted by FIFO).
        """
        if len(self.measurements) >= 3:
            return self.measurements[0].index
        used = {m.index for m in self.measurements}
        for i in (1, 2, 3):
            if i not in used:
                return i
        return 1
