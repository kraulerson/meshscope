"""VTK actors for highlighting mesh topology problems."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy.typing as npt
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkLine, vtkPolyData
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper

if TYPE_CHECKING:
    from meshscope.core.mesh_analysis import MeshAnalysis

# Colors are supplementary — line style carries meaning
OPEN_EDGE_COLOR = (0.8, 0.267, 0.267)  # #cc4444 muted red
NON_MANIFOLD_COLOR = (0.8, 0.533, 0.267)  # #cc8844 orange
DEGENERATE_COLOR = (0.8, 0.8, 0.267)  # #cccc44 yellow


class HighlightManager:
    """Creates VTK actors for mesh problem visualization."""

    def create_actors(
        self,
        analysis: MeshAnalysis,
        vertices: npt.NDArray[Any],
        faces: npt.NDArray[Any],
    ) -> list[vtkActor]:
        """Create highlight actors for all problem types found in analysis."""
        actors: list[vtkActor] = []

        if analysis.open_edge_count > 0:
            actors.append(
                self._create_edge_actor(
                    analysis.open_edge_indices,
                    vertices,
                    color=OPEN_EDGE_COLOR,
                    line_width=3.0,
                    tubes=False,
                )
            )

        if analysis.non_manifold_edge_count > 0:
            actors.append(
                self._create_edge_actor(
                    analysis.non_manifold_edge_indices,
                    vertices,
                    color=NON_MANIFOLD_COLOR,
                    line_width=2.0,
                    tubes=True,
                )
            )

        if analysis.degenerate_face_count > 0:
            actors.append(
                self._create_face_outline_actor(
                    analysis.degenerate_face_indices,
                    vertices,
                    faces,
                    color=DEGENERATE_COLOR,
                    line_width=2.0,
                )
            )

        return actors

    def _create_edge_actor(
        self,
        edge_indices: npt.NDArray[Any],
        vertices: npt.NDArray[Any],
        *,
        color: tuple[float, float, float],
        line_width: float,
        tubes: bool,
    ) -> vtkActor:
        """Create a line actor for a set of edges."""
        points = vtkPoints()
        lines = vtkCellArray()

        for v0_idx, v1_idx in edge_indices:
            p0 = points.InsertNextPoint(*vertices[v0_idx].astype(float))
            p1 = points.InsertNextPoint(*vertices[v1_idx].astype(float))
            line = vtkLine()
            line.GetPointIds().SetId(0, p0)
            line.GetPointIds().SetId(1, p1)
            lines.InsertNextCell(line)

        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetLineWidth(line_width)
        if tubes:
            actor.GetProperty().SetRenderLinesAsTubes(True)
        return actor

    def _create_face_outline_actor(
        self,
        face_indices: npt.NDArray[Any],
        vertices: npt.NDArray[Any],
        faces: npt.NDArray[Any],
        *,
        color: tuple[float, float, float],
        line_width: float,
    ) -> vtkActor:
        """Create a dashed wireframe outline for degenerate faces."""
        points = vtkPoints()
        lines = vtkCellArray()

        for fi in face_indices:
            if fi >= len(faces):
                continue
            face = faces[fi]
            # Draw the 3 edges of the triangle
            for i in range(3):
                v0_idx = face[i]
                v1_idx = face[(i + 1) % 3]
                p0 = points.InsertNextPoint(*vertices[v0_idx].astype(float))
                p1 = points.InsertNextPoint(*vertices[v1_idx].astype(float))
                line = vtkLine()
                line.GetPointIds().SetId(0, p0)
                line.GetPointIds().SetId(1, p1)
                lines.InsertNextCell(line)

        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetLineWidth(line_width)
        actor.GetProperty().SetLineStipplePattern(0xF0F0)
        actor.GetProperty().SetLineStippleRepeatFactor(1)
        return actor
