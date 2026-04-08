"""Tests for measurement mode UI: info panel, main window, and integration."""

import pytest
from PySide6.QtWidgets import QApplication

from meshscope.core.mesh_data import Measurement
from meshscope.ui.info_panel import InfoPanel


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
