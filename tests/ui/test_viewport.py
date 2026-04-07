"""Tests for ViewportWidget."""

import inspect

import pytest
from PySide6.QtWidgets import QApplication

from meshscope.ui.viewport_widget import ViewportWidget


@pytest.fixture()
def widget(qapp: QApplication) -> ViewportWidget:
    w = ViewportWidget()
    w.show()
    yield w
    w.close()


class TestViewportWidgetCreation:
    def test_creates_without_error(self, widget: ViewportWidget) -> None:
        assert widget is not None

    def test_has_renderer(self, widget: ViewportWidget) -> None:
        assert widget.renderer is not None

    def test_has_scene_manager(self, widget: ViewportWidget) -> None:
        assert widget.scene_manager is not None

    def test_starts_in_empty_state(self, widget: ViewportWidget) -> None:
        assert widget.state == "empty"


class TestViewportWidgetStates:
    def test_empty_state_shows_prompt(self, widget: ViewportWidget) -> None:
        assert widget.state == "empty"
        assert widget.empty_label.isVisible()

    def test_error_state(self, widget: ViewportWidget) -> None:
        widget.show_error("OpenGL not available")
        assert widget.state == "error"
        assert widget.empty_label.isVisible()
        assert "OpenGL" in widget.empty_label.text()

    def test_success_state_hides_prompt(self, widget: ViewportWidget) -> None:
        widget.set_state("success")
        assert widget.state == "success"
        assert not widget.empty_label.isVisible()

    def test_loading_state(self, widget: ViewportWidget) -> None:
        widget.set_state("loading")
        assert widget.state == "loading"


class TestViewportWidgetOpenGL2Backend:
    """Regression: VTK requires OpenGL2 factory imports to render."""

    def test_opengl2_renderer_factory_registered(self, widget: ViewportWidget) -> None:
        """vtkRenderingOpenGL2 must be imported so VTK can render with OpenGL."""
        import vtkmodules.vtkRenderingOpenGL2 as gl2

        assert gl2 is not None

    def test_interaction_style_factory_registered(self, widget: ViewportWidget) -> None:
        """vtkInteractionStyle must be imported for mouse interaction."""
        import vtkmodules.vtkInteractionStyle as style

        assert style is not None


class TestViewportWidgetVTKInitialization:
    """Regression: VTK must not be initialized before widget is shown."""

    def test_vtk_not_initialized_before_show(self, qapp: QApplication) -> None:
        """VTK interactor must defer initialization until first showEvent."""
        w = ViewportWidget()
        assert w._vtk_initialized is False
        w.close()

    def test_vtk_initialized_after_show(self, widget: ViewportWidget) -> None:
        """VTK interactor must be initialized after widget is shown."""
        assert widget._vtk_initialized is True

    def test_vtk_render_triggers_initialization(self, qapp: QApplication) -> None:
        """vtk_render() must initialize VTK if not yet initialized."""
        w = ViewportWidget()
        assert w._vtk_initialized is False
        w.vtk_render()
        assert w._vtk_initialized is True
        w.close()


class TestViewportWidgetApiContract:
    """Regression: vtk_render not render, resizeEvent takes QResizeEvent."""

    def test_vtk_render_exists_and_render_not_overridden(
        self, widget: ViewportWidget
    ) -> None:
        assert hasattr(widget, "vtk_render"), "Must use vtk_render(), not render()"
        # render must NOT be defined on ViewportWidget (would shadow QWidget.render)
        assert "render" not in ViewportWidget.__dict__, (
            "ViewportWidget must not override render() — use vtk_render() instead"
        )

    def test_resize_event_accepts_qresizeevent(self, widget: ViewportWidget) -> None:
        hints = inspect.get_annotations(ViewportWidget.resizeEvent)
        assert hints.get("event") == "QResizeEvent"
