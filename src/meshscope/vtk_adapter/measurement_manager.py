"""VTK actors for point-to-point distance measurements."""

from __future__ import annotations

from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkLine, vtkPolyData
from vtkmodules.vtkFiltersSources import vtkRegularPolygonSource
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper

# Measurement colors by index (1-based)
MEASUREMENT_COLORS: dict[int, tuple[float, float, float]] = {
    1: (0.941, 0.753, 0.251),  # #f0c040 amber
    2: (0.251, 0.690, 0.941),  # #40b0f0 sky blue
    3: (0.376, 0.816, 0.376),  # #60d060 light green
}

MEASUREMENT_LINE_WIDTH = 2.0
ENDPOINT_MARKER_RADIUS = 0.8


class MeasurementManager:
    """Creates VTK actors for measurement visualization.

    Pattern follows HighlightManager: stateless factory that creates
    actors from measurement data. Does not own a renderer.
    """

    def create_measurement_actors(
        self,
        point_a: tuple[float, float, float],
        point_b: tuple[float, float, float],
        index: int,
    ) -> list[vtkActor]:
        """Create line + endpoint marker actors for one measurement.

        Returns a list of 3 actors: [line_actor, endpoint_a_actor, endpoint_b_actor].
        """
        color = MEASUREMENT_COLORS.get(index, MEASUREMENT_COLORS[1])

        line_actor = self._create_line_actor(point_a, point_b, color)
        endpoint_a = self._create_endpoint_marker(point_a, index, color)
        endpoint_b = self._create_endpoint_marker(point_b, index, color)

        return [line_actor, endpoint_a, endpoint_b]

    def create_pending_point_actor(
        self,
        point: tuple[float, float, float],
        index: int,
    ) -> vtkActor:
        """Create a single endpoint marker for point A before point B is placed."""
        color = MEASUREMENT_COLORS.get(index, MEASUREMENT_COLORS[1])
        return self._create_endpoint_marker(point, index, color)

    def _create_line_actor(
        self,
        point_a: tuple[float, float, float],
        point_b: tuple[float, float, float],
        color: tuple[float, float, float],
    ) -> vtkActor:
        """Create a solid line between two points."""
        points = vtkPoints()
        p0 = points.InsertNextPoint(*point_a)
        p1 = points.InsertNextPoint(*point_b)

        line = vtkLine()
        line.GetPointIds().SetId(0, p0)
        line.GetPointIds().SetId(1, p1)

        lines = vtkCellArray()
        lines.InsertNextCell(line)

        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetLineWidth(MEASUREMENT_LINE_WIDTH)
        return actor

    def _create_endpoint_marker(
        self,
        point: tuple[float, float, float],
        index: int,
        color: tuple[float, float, float],
    ) -> vtkActor:
        """Create a numbered circle marker at the given point."""
        circle = vtkRegularPolygonSource()
        circle.SetNumberOfSides(24)
        circle.SetRadius(ENDPOINT_MARKER_RADIUS)
        circle.SetCenter(0.0, 0.0, 0.0)
        circle.GeneratePolygonOn()
        circle.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(circle.GetOutputPort())

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetAmbient(1.0)
        actor.GetProperty().SetDiffuse(0.0)
        actor.SetPosition(*point)
        return actor
