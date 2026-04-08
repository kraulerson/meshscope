"""Print bed volume visualization: grid floor, wireframe box, overflow hatching."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkLine, vtkPolyData
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper

if TYPE_CHECKING:
    from meshscope.core.mesh_data import BoundingBox

PRINTER_PRESETS: dict[str, dict[str, Any]] = {
    "ender_3": {"name": "Ender 3", "x": 220, "y": 220, "z": 250},
    "prusa_mk4": {"name": "Prusa MK4", "x": 250, "y": 210, "z": 210},
    "voron_2_4": {"name": "Voron 2.4", "x": 350, "y": 350, "z": 350},
    "bambu_x1c": {"name": "Bambu X1 Carbon", "x": 256, "y": 256, "z": 256},
    "bambu_p1s": {"name": "Bambu P1S", "x": 256, "y": 256, "z": 256},
}

GRID_COLOR = (0.227, 0.353, 0.227)  # #3a5a3a
BOX_COLOR = (0.353, 0.541, 0.353)  # #5a8a5a
OVERFLOW_COLOR = (0.6, 0.3, 0.3)  # muted red, hatching carries meaning

GRID_SPACING_MM = 10


def get_overflow_text(
    bed_x: int, bed_y: int, bed_z: int, bbox: BoundingBox
) -> str | None:
    """Return overflow description text, or None if model fits."""
    overflows = []
    dx = bbox.size_x - bed_x
    dy = bbox.size_y - bed_y
    dz = bbox.size_z - bed_z
    if dx > 0.01:
        overflows.append(f"X +{dx:.0f}mm")
    if dy > 0.01:
        overflows.append(f"Y +{dy:.0f}mm")
    if dz > 0.01:
        overflows.append(f"Z +{dz:.0f}mm")
    if not overflows:
        return None
    return f"Exceeds volume: {', '.join(overflows)}"


class PrintBedManager:
    """Creates VTK actors for print bed volume visualization."""

    def create_actors(self, x: int, y: int, z: int) -> list[vtkActor]:
        """Create grid floor + wireframe box actors for given bed dimensions."""
        actors = []
        actors.append(self._create_grid_floor(x, y))
        actors.append(self._create_wireframe_box(x, y, z))
        return actors

    def create_overflow_actors(
        self, bed_x: int, bed_y: int, bed_z: int, bbox: BoundingBox
    ) -> list[vtkActor]:
        """Create diagonal hatching actors for overflow regions."""
        actors = []
        dx = bbox.size_x - bed_x
        dy = bbox.size_y - bed_y
        dz = bbox.size_z - bed_z

        # Floor hatching for X/Y overflow
        if dx > 0.01:
            actors.append(self._create_hatching_rect(bed_x, 0, bed_x + dx, bed_y))
        if dy > 0.01:
            actors.append(self._create_hatching_rect(0, bed_y, bed_x, bed_y + dy))
        if dx > 0.01 and dy > 0.01:
            actors.append(
                self._create_hatching_rect(bed_x, bed_y, bed_x + dx, bed_y + dy)
            )

        # Ceiling hatching for Z overflow
        if dz > 0.01:
            actors.append(
                self._create_hatching_rect(0, 0, bed_x, bed_y, z=float(bed_z))
            )
        return actors

    def _create_grid_floor(self, x: int, y: int) -> vtkActor:
        """Create a grid of lines on the Z=0 plane at GRID_SPACING_MM intervals."""
        points = vtkPoints()
        lines = vtkCellArray()

        # X-parallel lines (along Y axis)
        nx = x // GRID_SPACING_MM + 1
        for i in range(nx):
            gx = i * GRID_SPACING_MM
            p0 = points.InsertNextPoint(gx, 0, 0)
            p1 = points.InsertNextPoint(gx, y, 0)
            line = vtkLine()
            line.GetPointIds().SetId(0, p0)
            line.GetPointIds().SetId(1, p1)
            lines.InsertNextCell(line)

        # Y-parallel lines (along X axis)
        ny = y // GRID_SPACING_MM + 1
        for i in range(ny):
            gy = i * GRID_SPACING_MM
            p0 = points.InsertNextPoint(0, gy, 0)
            p1 = points.InsertNextPoint(x, gy, 0)
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
        actor.GetProperty().SetColor(*GRID_COLOR)
        actor.GetProperty().SetLineWidth(1.0)
        return actor

    def _create_wireframe_box(self, x: int, y: int, z: int) -> vtkActor:
        """Create the 12-edge wireframe box for the print volume."""
        points = vtkPoints()
        # 8 corners of the box
        corners = [
            (0, 0, 0),
            (x, 0, 0),
            (x, y, 0),
            (0, y, 0),
            (0, 0, z),
            (x, 0, z),
            (x, y, z),
            (0, y, z),
        ]
        for c in corners:
            points.InsertNextPoint(*c)

        edges = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 0),  # bottom
            (4, 5),
            (5, 6),
            (6, 7),
            (7, 4),  # top
            (0, 4),
            (1, 5),
            (2, 6),
            (3, 7),  # verticals
        ]

        lines = vtkCellArray()
        for i0, i1 in edges:
            line = vtkLine()
            line.GetPointIds().SetId(0, i0)
            line.GetPointIds().SetId(1, i1)
            lines.InsertNextCell(line)

        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*BOX_COLOR)
        actor.GetProperty().SetLineWidth(1.5)
        return actor

    def _create_hatching_rect(
        self, x0: float, y0: float, x1: float, y1: float, *, z: float = 0.01
    ) -> vtkActor:
        """Create diagonal hatching lines in a rectangle at the given Z height."""
        points = vtkPoints()
        lines = vtkCellArray()
        spacing = GRID_SPACING_MM
        width = x1 - x0
        height = y1 - y0
        diag = width + height

        offset = spacing
        while offset < diag:
            if offset <= width:
                sx = x0 + offset
                sy = y0
            else:
                sx = x1
                sy = y0 + (offset - width)

            if offset <= height:
                ex = x0
                ey = y0 + offset
            else:
                ex = x0 + (offset - height)
                ey = y1

            p0 = points.InsertNextPoint(sx, sy, z)
            p1 = points.InsertNextPoint(ex, ey, z)
            line = vtkLine()
            line.GetPointIds().SetId(0, p0)
            line.GetPointIds().SetId(1, p1)
            lines.InsertNextCell(line)

            offset += spacing

        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*OVERFLOW_COLOR)
        actor.GetProperty().SetLineWidth(1.0)
        return actor
