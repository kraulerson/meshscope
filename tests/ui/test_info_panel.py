"""Tests for the Mesh Info Panel."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication, QDockWidget

from meshscope.ui.info_panel import CollapsibleSection, InfoPanel


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


class TestCollapsibleSection:
    def test_starts_expanded(self, qapp: QApplication) -> None:
        section = CollapsibleSection("Geometry")
        assert section.is_expanded is True

    def test_starts_collapsed_when_specified(self, qapp: QApplication) -> None:
        section = CollapsibleSection("Details", expanded=False)
        assert section.is_expanded is False

    def test_toggle_collapses(self, qapp: QApplication) -> None:
        section = CollapsibleSection("Geometry")
        section.toggle()
        assert section.is_expanded is False

    def test_toggle_expands(self, qapp: QApplication) -> None:
        section = CollapsibleSection("Geometry", expanded=False)
        section.toggle()
        assert section.is_expanded is True

    def test_header_has_accessible_name(self, qapp: QApplication) -> None:
        section = CollapsibleSection("Geometry")
        assert "Geometry" in section.header_button.accessibleName()

    def test_content_area_exists(self, qapp: QApplication) -> None:
        section = CollapsibleSection("Geometry")
        assert section.content_area is not None
