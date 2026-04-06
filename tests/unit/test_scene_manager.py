"""Tests for SceneManager — actor, lighting, and render mode management."""

from vtkmodules.vtkCommonCore import vtkFloatArray, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPolyData, vtkTriangle
from vtkmodules.vtkRenderingCore import vtkRenderer

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
