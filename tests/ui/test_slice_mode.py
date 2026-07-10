"""Tests for slice mode UI: SliceOverlayWidget and MainWindow integration."""

import pytest
from PySide6.QtWidgets import QApplication, QPushButton

from meshscope.ui.main_window import MainWindow
from meshscope.ui.slice_overlay import SliceOverlayWidget
from meshscope.ui.viewport_widget import ViewportWidget

from ._native_window import requires_native_window

# These tests construct MainWindow/ViewportWidget, which build a VTK render
# window from QWidget.winId(). That handle is not dereferenceable under the
# offscreen QPA plugin, so the process segfaults instead of raising.
pytestmark = requires_native_window


@pytest.fixture()
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestSliceOverlayWidgetConstruction:
    def test_creates_without_parent(self, qapp: QApplication) -> None:
        widget = SliceOverlayWidget(None)
        assert widget is not None
        widget.close()

    def test_has_preset_buttons(self, qapp: QApplication) -> None:
        widget = SliceOverlayWidget(None)
        x_btn = widget.findChild(QPushButton, "btn_x")
        y_btn = widget.findChild(QPushButton, "btn_y")
        z_btn = widget.findChild(QPushButton, "btn_z")
        assert x_btn is not None
        assert y_btn is not None
        assert z_btn is not None
        widget.close()

    def test_has_reset_button(self, qapp: QApplication) -> None:
        widget = SliceOverlayWidget(None)
        reset_btn = widget.findChild(QPushButton, "btn_reset")
        assert reset_btn is not None
        widget.close()

    def test_initially_hidden(self, qapp: QApplication) -> None:
        widget = SliceOverlayWidget(None)
        assert not widget.isVisible()
        widget.close()


class TestSliceOverlayWidgetSignals:
    def test_x_button_emits_preset_signal(self, qapp: QApplication) -> None:
        widget = SliceOverlayWidget(None)
        received: list[str] = []
        widget.preset_clicked.connect(lambda axis: received.append(axis))

        x_btn = widget.findChild(QPushButton, "btn_x")
        x_btn.click()
        assert received == ["x"]
        widget.close()

    def test_y_button_emits_preset_signal(self, qapp: QApplication) -> None:
        widget = SliceOverlayWidget(None)
        received: list[str] = []
        widget.preset_clicked.connect(lambda axis: received.append(axis))

        y_btn = widget.findChild(QPushButton, "btn_y")
        y_btn.click()
        assert received == ["y"]
        widget.close()

    def test_z_button_emits_preset_signal(self, qapp: QApplication) -> None:
        widget = SliceOverlayWidget(None)
        received: list[str] = []
        widget.preset_clicked.connect(lambda axis: received.append(axis))

        z_btn = widget.findChild(QPushButton, "btn_z")
        z_btn.click()
        assert received == ["z"]
        widget.close()

    def test_reset_button_emits_reset_signal(self, qapp: QApplication) -> None:
        widget = SliceOverlayWidget(None)
        received: list[bool] = []
        widget.reset_clicked.connect(lambda: received.append(True))

        reset_btn = widget.findChild(QPushButton, "btn_reset")
        reset_btn.click()
        assert received == [True]
        widget.close()


class TestSliceOverlayWidgetActivePreset:
    def test_set_active_preset_x(self, qapp: QApplication) -> None:
        widget = SliceOverlayWidget(None)
        widget.set_active_preset("x")
        x_btn = widget.findChild(QPushButton, "btn_x")
        assert x_btn.property("active") is True
        widget.close()

    def test_set_active_preset_clears_others(self, qapp: QApplication) -> None:
        widget = SliceOverlayWidget(None)
        widget.set_active_preset("x")
        y_btn = widget.findChild(QPushButton, "btn_y")
        z_btn = widget.findChild(QPushButton, "btn_z")
        assert y_btn.property("active") is not True
        assert z_btn.property("active") is not True
        widget.close()

    def test_set_active_preset_none_clears_all(self, qapp: QApplication) -> None:
        widget = SliceOverlayWidget(None)
        widget.set_active_preset("x")
        widget.set_active_preset(None)
        x_btn = widget.findChild(QPushButton, "btn_x")
        assert x_btn.property("active") is not True
        widget.close()


class TestSliceOverlayWidgetVisibility:
    def test_show_overlay(self, qapp: QApplication) -> None:
        widget = SliceOverlayWidget(None)
        widget.show_overlay()
        assert widget.isVisible()
        widget.close()

    def test_hide_overlay(self, qapp: QApplication) -> None:
        widget = SliceOverlayWidget(None)
        widget.show_overlay()
        widget.hide_overlay()
        assert not widget.isVisible()
        widget.close()


class TestViewportWidgetSliceOverlay:
    def test_has_slice_overlay(self, qapp: QApplication) -> None:
        vp = ViewportWidget()
        assert vp.slice_overlay is not None
        vp.close()

    def test_slice_overlay_initially_hidden(self, qapp: QApplication) -> None:
        vp = ViewportWidget()
        assert not vp.slice_overlay.isVisible()
        vp.close()

    def test_slice_overlay_is_child_of_viewport(self, qapp: QApplication) -> None:
        vp = ViewportWidget()
        assert vp.slice_overlay.parent() is vp
        vp.close()


@pytest.fixture()
def window(qapp: QApplication) -> MainWindow:
    w = MainWindow()
    yield w
    w.close()


class TestMainWindowSliceAction:
    def test_has_slice_action(self, window: MainWindow) -> None:
        assert window.slice_action is not None

    def test_slice_action_is_checkable(self, window: MainWindow) -> None:
        assert window.slice_action.isCheckable()

    def test_slice_action_disabled_initially(self, window: MainWindow) -> None:
        assert not window.slice_action.isEnabled()

    def test_slice_action_shortcut_is_c(self, window: MainWindow) -> None:
        assert window.slice_action.shortcut().toString() == "C"

    def test_slice_action_enabled_after_load(self, window: MainWindow) -> None:
        window._set_state_success("test.stl", 1000)
        assert window.slice_action.isEnabled()

    def test_slice_action_disabled_after_error(self, window: MainWindow) -> None:
        window._set_state_success("test.stl", 1000)
        window._set_state_error("File corrupt")
        assert not window.slice_action.isEnabled()

    def test_slice_activates_with_loaded_mesh(self, window: MainWindow) -> None:
        """Regression: slice must activate when interactor is passed directly."""
        from pathlib import Path

        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        window.slice_action.setChecked(True)
        assert window._viewport.scene_manager.slice_active is True

    def test_slice_deactivates_on_uncheck(self, window: MainWindow) -> None:
        """Regression: slice must deactivate cleanly."""
        from pathlib import Path

        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        window.slice_action.setChecked(True)
        window.slice_action.setChecked(False)
        assert window._viewport.scene_manager.slice_active is False
