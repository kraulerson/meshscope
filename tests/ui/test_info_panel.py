"""Tests for the Mesh Info Panel."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication, QDockWidget

from meshscope.ui.info_panel import InfoPanel


class TestInfoPanelConstruction:
    def test_is_qdockwidget(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        assert isinstance(panel, QDockWidget)

    def test_has_accessible_name(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        assert panel.accessibleName() == "Mesh Info Panel"

    def test_window_title(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        assert panel.windowTitle() == "Info"


class TestInfoPanelEmptyState:
    def test_shows_placeholder_when_no_mesh(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        assert panel.is_empty is True

    def test_clear_resets_to_empty(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.clear()
        assert panel.is_empty is True
