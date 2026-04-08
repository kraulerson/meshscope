"""Mesh transforms: scale, rotate, and mirror with pure numpy."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from meshscope.core.mesh_data import MeshData

logger = logging.getLogger("meshscope.core.mesh_transform")


@dataclass(frozen=True)
class TransformResult:
    """Result of applying a mesh transform."""

    mesh: MeshData
    description: str
    warning: str | None
