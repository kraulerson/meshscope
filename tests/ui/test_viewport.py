"""Tests for ViewportWidget."""

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
