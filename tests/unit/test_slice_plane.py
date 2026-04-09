"""Tests for SlicePlaneManager — clipping pipeline and plane widget management."""

from unittest.mock import MagicMock

from vtkmodules.vtkCommonCore import vtkFloatArray, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData, vtkTriangle
from vtkmodules.vtkRenderingCore import vtkRenderer

from meshscope.vtk_adapter.slice_plane_manager import SlicePlaneManager


def _make_cube_polydata() -> vtkPolyData:
    """Create a simple cube polydata (12 triangles) for clipping tests.

    A proper closed surface is needed for vtkClipClosedSurface to generate caps.
    """
    points = vtkPoints()
    # 8 vertices of a unit cube centered at origin
    coords = [
        (-5, -5, -5),
        (5, -5, -5),
        (5, 5, -5),
        (-5, 5, -5),
        (-5, -5, 5),
        (5, -5, 5),
        (5, 5, 5),
        (-5, 5, 5),
    ]
    for c in coords:
        points.InsertNextPoint(*c)

    cells = vtkCellArray()
    # 12 triangles forming 6 faces of the cube
    faces = [
        (0, 1, 2),
        (0, 2, 3),  # bottom (-Z)
        (4, 6, 5),
        (4, 7, 6),  # top (+Z)
        (0, 4, 5),
        (0, 5, 1),  # front (-Y)
        (2, 6, 7),
        (2, 7, 3),  # back (+Y)
        (0, 3, 7),
        (0, 7, 4),  # left (-X)
        (1, 5, 6),
        (1, 6, 2),  # right (+X)
    ]
    for f in faces:
        tri = vtkTriangle()
        tri.GetPointIds().SetId(0, f[0])
        tri.GetPointIds().SetId(1, f[1])
        tri.GetPointIds().SetId(2, f[2])
        cells.InsertNextCell(tri)

    normals = vtkFloatArray()
    normals.SetNumberOfComponents(3)
    normals.SetName("Normals")
    for _ in faces:
        normals.InsertNextTuple3(0, 0, 1)

    polydata = vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetPolys(cells)
    polydata.GetCellData().SetNormals(normals)
    return polydata


def _make_triangle_polydata() -> vtkPolyData:
    """Create a minimal single-triangle polydata for basic tests."""
    points = vtkPoints()
    points.InsertNextPoint(0, 0, 0)
    points.InsertNextPoint(10, 0, 0)
    points.InsertNextPoint(5, 10, 0)

    cells = vtkCellArray()
    tri = vtkTriangle()
    tri.GetPointIds().SetId(0, 0)
    tri.GetPointIds().SetId(1, 1)
    tri.GetPointIds().SetId(2, 2)
    cells.InsertNextCell(tri)

    polydata = vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetPolys(cells)
    return polydata


class TestSlicePlaneManagerConstruction:
    def test_initial_state_is_inactive(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        mgr = SlicePlaneManager(renderer, interactor)
        assert mgr.is_active is False

    def test_no_actors_initially(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        SlicePlaneManager(renderer, interactor)
        assert renderer.GetActors().GetNumberOfItems() == 0


class TestSlicePlaneManagerActivation:
    def test_activate_sets_active(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        mgr = SlicePlaneManager(renderer, interactor)
        polydata = _make_cube_polydata()
        bounds = polydata.GetBounds()
        mgr.activate(polydata, bounds)
        assert mgr.is_active is True

    def test_activate_adds_actors_to_renderer(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        mgr = SlicePlaneManager(renderer, interactor)
        polydata = _make_cube_polydata()
        bounds = polydata.GetBounds()
        mgr.activate(polydata, bounds)
        # At least the clipped mesh actor should be added
        assert renderer.GetActors().GetNumberOfItems() >= 1

    def test_deactivate_sets_inactive(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        mgr = SlicePlaneManager(renderer, interactor)
        polydata = _make_cube_polydata()
        bounds = polydata.GetBounds()
        mgr.activate(polydata, bounds)
        mgr.deactivate()
        assert mgr.is_active is False

    def test_deactivate_removes_actors(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        mgr = SlicePlaneManager(renderer, interactor)
        polydata = _make_cube_polydata()
        bounds = polydata.GetBounds()
        mgr.activate(polydata, bounds)
        mgr.deactivate()
        assert renderer.GetActors().GetNumberOfItems() == 0

    def test_deactivate_when_inactive_is_noop(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        mgr = SlicePlaneManager(renderer, interactor)
        mgr.deactivate()  # must not raise
        assert mgr.is_active is False

    def test_double_activate_does_not_duplicate_actors(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        mgr = SlicePlaneManager(renderer, interactor)
        polydata = _make_cube_polydata()
        bounds = polydata.GetBounds()
        mgr.activate(polydata, bounds)
        count_after_first = renderer.GetActors().GetNumberOfItems()
        mgr.activate(polydata, bounds)
        count_after_second = renderer.GetActors().GetNumberOfItems()
        assert count_after_second == count_after_first


class TestSlicePlaneManagerPresets:
    def test_set_preset_x(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        mgr = SlicePlaneManager(renderer, interactor)
        polydata = _make_cube_polydata()
        bounds = polydata.GetBounds()
        mgr.activate(polydata, bounds)

        mgr.set_preset("x", bounds)
        assert mgr.current_preset == "x"

    def test_set_preset_y(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        mgr = SlicePlaneManager(renderer, interactor)
        polydata = _make_cube_polydata()
        bounds = polydata.GetBounds()
        mgr.activate(polydata, bounds)

        mgr.set_preset("y", bounds)
        assert mgr.current_preset == "y"

    def test_set_preset_z(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        mgr = SlicePlaneManager(renderer, interactor)
        polydata = _make_cube_polydata()
        bounds = polydata.GetBounds()
        mgr.activate(polydata, bounds)

        mgr.set_preset("z", bounds)
        assert mgr.current_preset == "z"

    def test_preset_when_inactive_is_noop(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        mgr = SlicePlaneManager(renderer, interactor)
        mgr.set_preset("x", (-5, 5, -5, 5, -5, 5))  # must not raise
        assert mgr.is_active is False

    def test_preset_invalid_axis_ignored(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        mgr = SlicePlaneManager(renderer, interactor)
        polydata = _make_cube_polydata()
        bounds = polydata.GetBounds()
        mgr.activate(polydata, bounds)

        mgr.set_preset("q", bounds)  # invalid axis
        # Should still be at the default Z preset
        assert mgr.current_preset == "z"


class TestSlicePlaneManagerReset:
    def test_reset_keeps_orientation(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        mgr = SlicePlaneManager(renderer, interactor)
        polydata = _make_cube_polydata()
        bounds = polydata.GetBounds()
        mgr.activate(polydata, bounds)

        mgr.set_preset("x", bounds)
        assert mgr.current_preset == "x"

        mgr.reset_to_center(bounds)
        # Preset should still be "x" since reset keeps orientation
        # (current_preset is only cleared on manual drag)
        assert mgr.current_preset == "x"

    def test_reset_when_inactive_is_noop(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        mgr = SlicePlaneManager(renderer, interactor)
        mgr.reset_to_center((-5, 5, -5, 5, -5, 5))  # must not raise
        assert mgr.is_active is False


class TestSlicePlaneManagerMeshUpdate:
    def test_update_mesh_recalculates_clip(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        mgr = SlicePlaneManager(renderer, interactor)
        polydata = _make_cube_polydata()
        bounds = polydata.GetBounds()
        mgr.activate(polydata, bounds)

        mgr.update_mesh(polydata, bounds)
        actors_after = renderer.GetActors().GetNumberOfItems()
        # Should still have actors (clip recalculated, not removed)
        assert actors_after >= 1

    def test_update_mesh_when_inactive_is_noop(self) -> None:
        renderer = vtkRenderer()
        interactor = MagicMock()
        mgr = SlicePlaneManager(renderer, interactor)
        polydata = _make_cube_polydata()
        bounds = polydata.GetBounds()
        mgr.update_mesh(polydata, bounds)  # must not raise
        assert mgr.is_active is False
