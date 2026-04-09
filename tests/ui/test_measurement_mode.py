"""Tests for measurement mode UI: info panel, main window, and integration."""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QMouseEvent
from PySide6.QtWidgets import QApplication

from meshscope.core.mesh_data import Measurement
from meshscope.ui.info_panel import InfoPanel
from meshscope.ui.main_window import MainWindow


@pytest.fixture()
def info_panel(qapp: QApplication) -> InfoPanel:
    panel = InfoPanel()
    yield panel
    panel.close()


class TestInfoPanelMeasurementsSection:
    def test_measurements_section_hidden_initially(self, info_panel: InfoPanel) -> None:
        assert info_panel.measurements_section_visible() is False

    def test_show_measurements_makes_section_visible(
        self, info_panel: InfoPanel
    ) -> None:
        measurements = [
            Measurement(
                point_a=(0.0, 0.0, 0.0),
                point_b=(10.0, 0.0, 0.0),
                distance_mm=10.0,
                index=1,
            )
        ]
        info_panel.show_measurements(measurements)
        assert info_panel.measurements_section_visible() is True

    def test_show_measurements_displays_distance(self, info_panel: InfoPanel) -> None:
        measurements = [
            Measurement(
                point_a=(0.0, 0.0, 0.0),
                point_b=(42.7, 0.0, 0.0),
                distance_mm=42.7,
                index=1,
            )
        ]
        info_panel.show_measurements(measurements)
        text = info_panel.measurements_section_text()
        assert "42.7 mm" in text

    def test_show_measurements_displays_coordinates(
        self, info_panel: InfoPanel
    ) -> None:
        measurements = [
            Measurement(
                point_a=(12.3, 45.6, 7.8),
                point_b=(1.0, 2.0, 3.0),
                distance_mm=50.0,
                index=1,
            )
        ]
        info_panel.show_measurements(measurements)
        text = info_panel.measurements_section_text()
        assert "12.3" in text
        assert "45.6" in text
        assert "7.8" in text

    def test_show_measurements_displays_index(self, info_panel: InfoPanel) -> None:
        measurements = [
            Measurement(
                point_a=(0.0, 0.0, 0.0),
                point_b=(10.0, 0.0, 0.0),
                distance_mm=10.0,
                index=2,
            )
        ]
        info_panel.show_measurements(measurements)
        text = info_panel.measurements_section_text()
        assert "#2" in text

    def test_show_three_measurements(self, info_panel: InfoPanel) -> None:
        measurements = [
            Measurement(
                point_a=(0.0, 0.0, 0.0),
                point_b=(10.0, 0.0, 0.0),
                distance_mm=10.0,
                index=1,
            ),
            Measurement(
                point_a=(0.0, 0.0, 0.0),
                point_b=(20.0, 0.0, 0.0),
                distance_mm=20.0,
                index=2,
            ),
            Measurement(
                point_a=(0.0, 0.0, 0.0),
                point_b=(30.0, 0.0, 0.0),
                distance_mm=30.0,
                index=3,
            ),
        ]
        info_panel.show_measurements(measurements)
        text = info_panel.measurements_section_text()
        assert "10.0 mm" in text
        assert "20.0 mm" in text
        assert "30.0 mm" in text

    def test_clear_measurements_hides_section(self, info_panel: InfoPanel) -> None:
        measurements = [
            Measurement(
                point_a=(0.0, 0.0, 0.0),
                point_b=(10.0, 0.0, 0.0),
                distance_mm=10.0,
                index=1,
            )
        ]
        info_panel.show_measurements(measurements)
        info_panel.clear_measurements()
        assert info_panel.measurements_section_visible() is False

    def test_clear_all_also_clears_measurements(self, info_panel: InfoPanel) -> None:
        measurements = [
            Measurement(
                point_a=(0.0, 0.0, 0.0),
                point_b=(10.0, 0.0, 0.0),
                distance_mm=10.0,
                index=1,
            )
        ]
        info_panel.show_measurements(measurements)
        info_panel.clear()
        assert info_panel.measurements_section_visible() is False

    def test_show_empty_list_hides_section(self, info_panel: InfoPanel) -> None:
        info_panel.show_measurements([])
        assert info_panel.measurements_section_visible() is False


# --- MainWindow tests ---


@pytest.fixture()
def window(qapp: QApplication) -> MainWindow:
    w = MainWindow()
    yield w
    w.close()


class TestMainWindowMeasureAction:
    def test_measure_action_exists(self, window: MainWindow) -> None:
        assert hasattr(window, "measure_action")

    def test_measure_action_disabled_initially(self, window: MainWindow) -> None:
        assert not window.measure_action.isEnabled()

    def test_measure_action_is_checkable(self, window: MainWindow) -> None:
        assert window.measure_action.isCheckable()

    def test_measure_shortcut_is_m(self, window: MainWindow) -> None:
        assert window.measure_action.shortcut() == QKeySequence("M")

    def test_measure_action_enabled_after_load(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert window.measure_action.isEnabled()

    def test_measure_action_disabled_after_error(
        self, window: MainWindow, tmp_path: Path
    ) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        bad = tmp_path / "bad.stl"
        bad.write_bytes(b"not a real stl file")
        window._load_file(bad)
        assert not window.measure_action.isEnabled()

    def test_measure_action_in_edit_menu(self, window: MainWindow) -> None:
        edit_menu = None
        for action in window.menuBar().actions():
            if "Edit" in action.text():
                edit_menu = action.menu()
                break
        assert edit_menu is not None
        action_texts = [a.text() for a in edit_menu.actions()]
        assert any("Measure" in t for t in action_texts)

    def test_measure_action_in_toolbar(self, window: MainWindow) -> None:
        toolbar_actions = [a.text() for a in window.toolbar.actions()]
        assert any("Measure" in t for t in toolbar_actions)


class TestMainWindowMeasureMode:
    def test_measure_mode_initially_off(self, window: MainWindow) -> None:
        assert window._measure_mode_active is False

    def test_toggle_measure_mode_on(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        window.measure_action.toggle()
        assert window._measure_mode_active is True

    def test_toggle_measure_mode_off(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        window.measure_action.toggle()
        window.measure_action.toggle()
        assert window._measure_mode_active is False

    def test_measure_mode_status_bar_message(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        window.measure_action.setChecked(True)
        assert "Measure mode" in window.statusBar().currentMessage()

    def test_measure_mode_discards_pending_on_exit(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        window.measure_action.setChecked(True)
        window._pending_point_a = (1.0, 2.0, 3.0)
        window.measure_action.setChecked(False)
        assert window._pending_point_a is None

    def test_event_filter_ignores_non_mouse_events(self, window: MainWindow) -> None:
        """Regression: eventFilter must handle non-QMouseEvent without error."""
        from PySide6.QtCore import QEvent

        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        window.measure_action.setChecked(True)
        non_mouse_event = QEvent(QEvent.Type.FocusIn)
        result = window.eventFilter(window._viewport.vtk_interactor, non_mouse_event)
        assert result is False

    def test_event_filter_consumes_left_press(self, window: MainWindow) -> None:
        """Regression: left-click press must be consumed to prevent VTK orbit."""
        from PySide6.QtCore import QPointF

        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        window.measure_action.setChecked(True)
        press = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPointF(100, 100),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        result = window.eventFilter(window._viewport.vtk_interactor, press)
        assert result is True  # consumed, not forwarded to VTK

    def test_event_filter_passes_right_press(self, window: MainWindow) -> None:
        """Regression: right-click must pass through for VTK zoom."""
        from PySide6.QtCore import QPointF

        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        window.measure_action.setChecked(True)
        press = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPointF(100, 100),
            Qt.MouseButton.RightButton,
            Qt.MouseButton.RightButton,
            Qt.KeyboardModifier.NoModifier,
        )
        result = window.eventFilter(window._viewport.vtk_interactor, press)
        assert result is False  # passed through to VTK


class TestMainWindowClearMeasurements:
    def test_clear_measurements_action_exists(self, window: MainWindow) -> None:
        assert hasattr(window, "clear_measurements_action")

    def test_clear_measurements_disabled_initially(self, window: MainWindow) -> None:
        assert not window.clear_measurements_action.isEnabled()

    def test_clear_measurements_in_edit_menu(self, window: MainWindow) -> None:
        edit_menu = None
        for action in window.menuBar().actions():
            if "Edit" in action.text():
                edit_menu = action.menu()
                break
        assert edit_menu is not None
        action_texts = [a.text() for a in edit_menu.actions()]
        assert any("Clear Measurements" in t for t in action_texts)


class TestMeasurementInvalidation:
    def _load_and_add_measurement(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert window._document is not None
        m = Measurement(
            point_a=(0.0, 0.0, 0.0),
            point_b=(10.0, 0.0, 0.0),
            distance_mm=10.0,
            index=1,
        )
        window._document.add_measurement(m)
        window._viewport.scene_manager.show_measurements(window._document.measurements)
        window._info_panel.show_measurements(window._document.measurements)
        window.clear_measurements_action.setEnabled(True)

    def test_invalidation_clears_measurements(self, window: MainWindow) -> None:
        self._load_and_add_measurement(window)
        assert len(window._document.measurements) == 1
        window._invalidate_measurements()
        assert len(window._document.measurements) == 0
        assert window._info_panel.measurements_section_visible() is False
        assert "Measurements cleared" in window.statusBar().currentMessage()

    def test_invalidation_disables_clear_action(self, window: MainWindow) -> None:
        self._load_and_add_measurement(window)
        window._invalidate_measurements()
        assert not window.clear_measurements_action.isEnabled()

    def test_invalidation_hides_pending_point(self, window: MainWindow) -> None:
        self._load_and_add_measurement(window)
        window._pending_point_a = (1.0, 2.0, 3.0)
        window._invalidate_measurements()
        assert window._pending_point_a is None

    def test_invalidation_exits_measure_mode(self, window: MainWindow) -> None:
        self._load_and_add_measurement(window)
        window.measure_action.setChecked(True)
        window._invalidate_measurements()
        assert window.measure_action.isChecked() is False
        assert window._measure_mode_active is False

    def test_load_new_file_clears_measurements(self, window: MainWindow) -> None:
        self._load_and_add_measurement(window)
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert len(window._document.measurements) == 0
