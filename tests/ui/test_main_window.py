"""Tests for MainWindow — toolbar, menus, status bar, state management."""

import pytest
from PySide6.QtWidgets import QApplication

from meshscope.ui.main_window import MainWindow


@pytest.fixture()
def window(qapp: QApplication) -> MainWindow:
    w = MainWindow()
    yield w
    w.close()


class TestMainWindowConstruction:
    def test_window_title(self, window: MainWindow) -> None:
        assert window.windowTitle() == "meshscope"

    def test_has_viewport(self, window: MainWindow) -> None:
        assert window.viewport is not None

    def test_status_bar_shows_ready(self, window: MainWindow) -> None:
        assert window.statusBar().currentMessage() == "Ready"


class TestMainWindowMenus:
    def test_file_menu_exists(self, window: MainWindow) -> None:
        menus = [a.text() for a in window.menuBar().actions()]
        assert any("File" in m for m in menus)

    def test_view_menu_exists(self, window: MainWindow) -> None:
        menus = [a.text() for a in window.menuBar().actions()]
        assert any("View" in m for m in menus)

    def test_help_menu_exists(self, window: MainWindow) -> None:
        menus = [a.text() for a in window.menuBar().actions()]
        assert any("Help" in m for m in menus)

    def test_file_menu_has_open(self, window: MainWindow) -> None:
        assert window.open_action is not None
        assert "Open" in window.open_action.text()


class TestMainWindowToolbar:
    def test_toolbar_exists(self, window: MainWindow) -> None:
        toolbars = window.findChildren(window.toolbar.__class__)
        assert len(toolbars) >= 1

    def test_open_button_exists(self, window: MainWindow) -> None:
        assert window.open_action is not None

    def test_wireframe_button_exists(self, window: MainWindow) -> None:
        assert window.wireframe_action is not None
        assert window.wireframe_action.isCheckable()

    def test_shading_button_exists(self, window: MainWindow) -> None:
        assert window.shading_action is not None
        assert window.shading_action.isCheckable()

    def test_fit_button_exists(self, window: MainWindow) -> None:
        assert window.fit_action is not None

    def test_render_actions_disabled_initially(self, window: MainWindow) -> None:
        assert not window.wireframe_action.isEnabled()
        assert not window.shading_action.isEnabled()
        assert not window.fit_action.isEnabled()


class TestMainWindowStateManagement:
    def test_initial_state_is_empty(self, window: MainWindow) -> None:
        assert window.viewport.state == "empty"
        assert not window.wireframe_action.isEnabled()

    def test_set_loaded_state_enables_actions(self, window: MainWindow) -> None:
        window._set_state_success("test.stl", 1000)
        assert window.wireframe_action.isEnabled()
        assert window.shading_action.isEnabled()
        assert window.fit_action.isEnabled()
        assert "test.stl" in window.statusBar().currentMessage()
        assert "1,000" in window.statusBar().currentMessage()

    def test_set_error_state_disables_render_actions(self, window: MainWindow) -> None:
        window._set_state_success("test.stl", 1000)
        window._set_state_error("File corrupt")
        assert not window.wireframe_action.isEnabled()
        assert not window.shading_action.isEnabled()
        assert "File corrupt" in window.statusBar().currentMessage()


class TestMainWindowDragDrop:
    def test_accepts_drops(self, window: MainWindow) -> None:
        assert window.acceptDrops()
