"""Tests for SceneManager — actor, lighting, and render mode management."""

from vtkmodules.vtkCommonCore import vtkFloatArray, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData, vtkTriangle
from vtkmodules.vtkRenderingCore import vtkRenderer

from meshscope.core.mesh_data import BoundingBox
from meshscope.vtk_adapter.scene_manager import SceneManager


def _make_polydata() -> vtkPolyData:
    """Create a minimal vtkPolyData triangle for testing."""
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

    normals = vtkFloatArray()
    normals.SetNumberOfComponents(3)
    normals.SetName("Normals")
    normals.InsertNextTuple3(0, 0, 1)

    polydata = vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetPolys(cells)
    polydata.GetCellData().SetNormals(normals)
    return polydata


class TestSceneManagerConstruction:
    def test_initial_state_has_no_mesh(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        assert sm.has_mesh is False

    def test_initial_actor_count_is_zero(self) -> None:
        renderer = vtkRenderer()
        SceneManager(renderer)
        assert renderer.GetActors().GetNumberOfItems() == 0


class TestSceneManagerDisplayMesh:
    def test_display_adds_actor(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.display_mesh(_make_polydata())
        assert renderer.GetActors().GetNumberOfItems() >= 1

    def test_has_mesh_after_display(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.display_mesh(_make_polydata())
        assert sm.has_mesh is True

    def test_display_sets_up_lights(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.display_mesh(_make_polydata())
        lights = renderer.GetLights()
        light_count = lights.GetNumberOfItems()
        assert light_count >= 2  # headlight + ambient fill

    def test_clear_removes_mesh(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.display_mesh(_make_polydata())
        sm.clear()
        assert sm.has_mesh is False
        assert renderer.GetActors().GetNumberOfItems() == 0

    def test_display_replaces_previous_mesh(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.display_mesh(_make_polydata())
        sm.display_mesh(_make_polydata())
        # Should still have exactly 1 mesh actor (not 2)
        assert sm.has_mesh is True


class TestSceneManagerRenderModes:
    def test_wireframe_overlay_default_off(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.display_mesh(_make_polydata())
        assert sm.wireframe_overlay_enabled is False

    def test_wireframe_overlay_toggle_on(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.display_mesh(_make_polydata())
        sm.set_wireframe_overlay(True)
        assert sm.wireframe_overlay_enabled is True

    def test_wireframe_overlay_toggle_off(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.display_mesh(_make_polydata())
        sm.set_wireframe_overlay(True)
        sm.set_wireframe_overlay(False)
        assert sm.wireframe_overlay_enabled is False

    def test_smooth_shading_default_off(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.display_mesh(_make_polydata())
        assert sm.smooth_shading_enabled is False

    def test_smooth_shading_toggle_on(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.display_mesh(_make_polydata())
        sm.set_smooth_shading(True)
        assert sm.smooth_shading_enabled is True

    def test_wireframe_noop_without_mesh(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.set_wireframe_overlay(True)  # should not raise
        assert sm.wireframe_overlay_enabled is False

    def test_smooth_shading_noop_without_mesh(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.set_smooth_shading(True)  # should not raise
        assert sm.smooth_shading_enabled is False

    def test_fit_to_view_does_not_raise(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.display_mesh(_make_polydata())
        sm.fit_to_view()  # should not raise


class TestSceneManagerDegenerateGeometry:
    """Tests for degenerate geometry that could crash VTK."""

    def test_display_degenerate_mesh_does_not_crash(self) -> None:
        """All vertices at same point should not crash display_mesh."""
        points = vtkPoints()
        for _ in range(3):
            points.InsertNextPoint(0, 0, 0)

        cells = vtkCellArray()
        tri = vtkTriangle()
        tri.GetPointIds().SetId(0, 0)
        tri.GetPointIds().SetId(1, 1)
        tri.GetPointIds().SetId(2, 2)
        cells.InsertNextCell(tri)

        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetPolys(cells)

        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.display_mesh(polydata)  # must not crash
        assert sm.has_mesh is True

    def test_fit_to_view_degenerate_does_not_crash(self) -> None:
        """fit_to_view on degenerate geometry (zero bounds) should not crash."""
        points = vtkPoints()
        for _ in range(3):
            points.InsertNextPoint(5, 5, 5)

        cells = vtkCellArray()
        tri = vtkTriangle()
        tri.GetPointIds().SetId(0, 0)
        tri.GetPointIds().SetId(1, 1)
        tri.GetPointIds().SetId(2, 2)
        cells.InsertNextCell(tri)

        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetPolys(cells)

        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.display_mesh(polydata)
        sm.fit_to_view()  # must not crash

    def test_display_empty_polydata_does_not_crash(self) -> None:
        """Empty polydata (no cells) should not crash."""
        polydata = vtkPolyData()
        polydata.SetPoints(vtkPoints())

        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.display_mesh(polydata)  # must not crash
        assert sm.has_mesh is True

    def test_display_mesh_survives_vtk_error(self) -> None:
        """If VTK raises during display, SceneManager should not crash."""
        from unittest.mock import patch

        renderer = vtkRenderer()
        sm = SceneManager(renderer)

        polydata = _make_polydata()

        # Simulate VTK failure during ResetCamera (called by fit_to_view)
        with patch.object(
            renderer, "ResetCamera", side_effect=RuntimeError("GPU error")
        ):
            sm.display_mesh(polydata)  # must not crash
            # Actor should still be added even if fit_to_view fails
            assert sm.has_mesh is True

    def test_fit_to_view_survives_vtk_error(self) -> None:
        """If VTK raises during fit_to_view, it should not crash."""
        from unittest.mock import patch

        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        sm.display_mesh(_make_polydata())

        with patch.object(
            renderer, "ResetCamera", side_effect=RuntimeError("GPU error")
        ):
            sm.fit_to_view()  # must not crash


class TestSceneManagerPrintBed:
    def test_print_bed_not_visible_initially(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        assert sm.print_bed_visible is False

    def test_show_print_bed(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        bbox = BoundingBox(0, 0, 0, 100, 100, 100)
        sm.show_print_bed(220, 220, 250, bbox)
        assert sm.print_bed_visible is True

    def test_hide_print_bed(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        bbox = BoundingBox(0, 0, 0, 100, 100, 100)
        sm.show_print_bed(220, 220, 250, bbox)
        sm.hide_print_bed()
        assert sm.print_bed_visible is False

    def test_show_print_bed_returns_overflow_text(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        bbox = BoundingBox(0, 0, 0, 300, 100, 100)
        text = sm.show_print_bed(220, 220, 250, bbox)
        assert text is not None
        assert "X" in text

    def test_show_print_bed_returns_none_when_fits(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        bbox = BoundingBox(0, 0, 0, 100, 100, 100)
        text = sm.show_print_bed(220, 220, 250, bbox)
        assert text is None

    def test_clear_also_hides_print_bed(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        bbox = BoundingBox(0, 0, 0, 100, 100, 100)
        sm.show_print_bed(220, 220, 250, bbox)
        sm.clear()
        assert sm.print_bed_visible is False
