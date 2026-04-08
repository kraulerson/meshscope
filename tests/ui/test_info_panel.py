"""Tests for the Mesh Info Panel."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDockWidget

from meshscope.core.mesh_analysis import MeshAnalysis
from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.core.mesh_document import MeshDocument
from meshscope.ui.info_panel import CollapsibleSection, InfoPanel


def _make_document(
    *,
    is_manifold: bool = True,
    volume: float | None = 1000.0,
    warnings: list[str] | None = None,
) -> MeshDocument:
    """Create a MeshDocument with known metadata for testing."""
    bb = BoundingBox(
        min_x=0.0,
        min_y=0.0,
        min_z=0.0,
        max_x=10.0,
        max_y=20.0,
        max_z=30.0,
    )
    meta = MeshMetadata(
        vertex_count=8,
        face_count=12,
        bounding_box=bb,
        surface_area_mm2=600.0,
        volume_mm3=volume if is_manifold else None,
        is_manifold=is_manifold,
    )
    vertices = np.zeros((8, 3), dtype=np.float32)
    faces = np.zeros((12, 3), dtype=np.uint32)
    normals = np.zeros((12, 3), dtype=np.float32)
    mesh = MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)
    return MeshDocument(
        mesh=mesh,
        source_path="/tmp/test/bracket.stl",
        source_format="stl",
        source_size_bytes=4200000,
        warnings=warnings,
    )


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


class TestInfoPanelFileSection:
    def test_shows_filename(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document())
        assert "bracket.stl" in panel.file_section_text()

    def test_shows_format_uppercased(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document())
        assert "STL" in panel.file_section_text()

    def test_shows_file_size_human_readable(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document())
        assert "4.0 MB" in panel.file_section_text()


class TestInfoPanelGeometrySection:
    def test_shows_vertex_count(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document())
        assert "8" in panel.geometry_section_text()

    def test_shows_face_count(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document())
        assert "12" in panel.geometry_section_text()

    def test_shows_surface_area(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document())
        text = panel.geometry_section_text()
        assert "600.0" in text
        assert "mm" in text


class TestInfoPanelDimensionsSection:
    def test_shows_size_xyz(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document())
        text = panel.dimensions_section_text()
        assert "10.0" in text
        assert "20.0" in text
        assert "30.0" in text

    def test_min_max_sub_section_exists(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document())
        assert panel.has_min_max_subsection()


class TestInfoPanelStatusSection:
    def test_manifold_yes(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document(is_manifold=True))
        text = panel.status_section_text()
        assert "Yes" in text

    def test_manifold_no(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document(is_manifold=False))
        text = panel.status_section_text()
        assert "No" in text

    def test_volume_shown_when_manifold(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document(is_manifold=True, volume=1000.0))
        text = panel.status_section_text()
        assert "1,000.0" in text
        assert "mm" in text

    def test_volume_na_when_non_manifold(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document(is_manifold=False))
        text = panel.status_section_text()
        assert "N/A" in text


class TestInfoPanelUpdateClear:
    def test_update_clears_empty_state(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document())
        assert panel.is_empty is False

    def test_clear_after_update_resets_to_empty(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document())
        panel.clear()
        assert panel.is_empty is True


class TestInfoPanelUnitWarning:
    def test_no_warning_when_no_mismatch(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document(warnings=[]))
        assert panel.warning_banner_visible() is False

    def test_warning_shown_when_unit_mismatch(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        doc = _make_document(
            warnings=[
                "Dimensions may indicate a unit mismatch. Consider scaling by 25.4"
            ]
        )
        panel.set_document(doc)
        assert panel.warning_banner_visible() is True

    def test_warning_banner_text_contains_message(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        doc = _make_document(
            warnings=[
                "Dimensions may indicate a unit mismatch. Consider scaling by 25.4"
            ]
        )
        panel.set_document(doc)
        assert "unit mismatch" in panel.warning_banner_text().lower()

    def test_inline_warning_shown_in_dimensions(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        doc = _make_document(
            warnings=[
                "Dimensions may indicate a unit mismatch. Consider scaling by 25.4"
            ]
        )
        panel.set_document(doc)
        assert panel.inline_unit_warning_visible() is True

    def test_warning_cleared_on_clear(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        doc = _make_document(
            warnings=[
                "Dimensions may indicate a unit mismatch. Consider scaling by 25.4"
            ]
        )
        panel.set_document(doc)
        panel.clear()
        assert panel.warning_banner_visible() is False

    def test_warning_hidden_on_update_without_mismatch(
        self, qapp: QApplication
    ) -> None:
        panel = InfoPanel()
        doc_warn = _make_document(
            warnings=[
                "Dimensions may indicate a unit mismatch. Consider scaling by 25.4"
            ]
        )
        panel.set_document(doc_warn)
        assert panel.warning_banner_visible() is True
        panel.set_document(_make_document(warnings=[]))
        assert panel.warning_banner_visible() is False

    def test_non_unit_warnings_do_not_trigger_banner(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        doc = _make_document(warnings=["OBJ: material library not supported"])
        panel.set_document(doc)
        assert panel.warning_banner_visible() is False


class TestInfoPanelAccessibility:
    def test_dock_widget_accessible_name(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        assert panel.accessibleName() == "Mesh Info Panel"

    def test_section_headers_have_accessible_names(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        for section in (
            panel._file_section,
            panel._geometry_section,
            panel._dimensions_section,
            panel._status_section,
        ):
            name = section.header_button.accessibleName()
            assert "section" in name.lower()
            assert "expanded" in name.lower() or "collapsed" in name.lower()

    def test_manifold_status_has_accessible_name(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document(is_manifold=True))
        assert "Yes" in panel._manifold_label.accessibleName()

    def test_non_manifold_status_has_accessible_name(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document(is_manifold=False))
        assert "No" in panel._manifold_label.accessibleName()

    def test_warning_banner_has_accessible_name(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        assert panel._warning_banner.accessibleName() == "Unit mismatch warning"

    def test_section_header_keyboard_focusable(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        for section in (
            panel._file_section,
            panel._geometry_section,
            panel._dimensions_section,
            panel._status_section,
        ):
            assert section.header_button.focusPolicy() == Qt.FocusPolicy.StrongFocus


def _make_clean_analysis() -> MeshAnalysis:
    return MeshAnalysis(
        is_manifold=True,
        is_watertight=True,
        hole_count=0,
        open_edge_count=0,
        degenerate_face_count=0,
        non_manifold_edge_count=0,
        open_edge_indices=np.zeros((0, 2), dtype=np.int64),
        non_manifold_edge_indices=np.zeros((0, 2), dtype=np.int64),
        degenerate_face_indices=np.zeros((0,), dtype=np.int64),
    )


def _make_problem_analysis() -> MeshAnalysis:
    return MeshAnalysis(
        is_manifold=False,
        is_watertight=False,
        hole_count=2,
        open_edge_count=3,
        degenerate_face_count=1,
        non_manifold_edge_count=2,
        open_edge_indices=np.array([[0, 1], [1, 2], [2, 3]], dtype=np.int64),
        non_manifold_edge_indices=np.array([[0, 2], [1, 3]], dtype=np.int64),
        degenerate_face_indices=np.array([0], dtype=np.int64),
    )


class TestInfoPanelAnalysisSection:
    def test_analysis_section_hidden_by_default(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        assert panel.analysis_section_visible() is False

    def test_show_analysis_makes_section_visible(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.show_analysis(_make_clean_analysis())
        assert panel.analysis_section_visible() is True

    def test_clean_analysis_shows_watertight_yes(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.show_analysis(_make_clean_analysis())
        text = panel.analysis_section_text()
        assert "Yes" in text
        assert "Watertight" in text

    def test_problem_analysis_shows_counts(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.show_analysis(_make_problem_analysis())
        text = panel.analysis_section_text()
        assert "3" in text  # open_edge_count
        assert "2" in text  # hole_count / non_manifold
        assert "1" in text  # degenerate_face_count

    def test_problem_analysis_shows_watertight_no(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.show_analysis(_make_problem_analysis())
        text = panel.analysis_section_text()
        assert "No" in text
        assert "Watertight" in text

    def test_clear_analysis_hides_section(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.show_analysis(_make_clean_analysis())
        panel.clear_analysis()
        assert panel.analysis_section_visible() is False

    def test_clear_also_clears_analysis(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.show_analysis(_make_clean_analysis())
        panel.clear()
        assert panel.analysis_section_visible() is False

    def test_has_highlight_checkbox(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        assert panel.has_highlight_checkbox() is True
