"""Tests for the Mesh Info Panel."""

from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import QApplication, QDockWidget

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
        panel.update(_make_document())
        assert "bracket.stl" in panel.file_section_text()

    def test_shows_format_uppercased(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.update(_make_document())
        assert "STL" in panel.file_section_text()

    def test_shows_file_size_human_readable(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.update(_make_document())
        assert "4.0 MB" in panel.file_section_text()


class TestInfoPanelGeometrySection:
    def test_shows_vertex_count(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.update(_make_document())
        assert "8" in panel.geometry_section_text()

    def test_shows_face_count(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.update(_make_document())
        assert "12" in panel.geometry_section_text()

    def test_shows_surface_area(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.update(_make_document())
        text = panel.geometry_section_text()
        assert "600.0" in text
        assert "mm" in text


class TestInfoPanelDimensionsSection:
    def test_shows_size_xyz(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.update(_make_document())
        text = panel.dimensions_section_text()
        assert "10.0" in text
        assert "20.0" in text
        assert "30.0" in text

    def test_min_max_sub_section_exists(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.update(_make_document())
        assert panel.has_min_max_subsection()


class TestInfoPanelStatusSection:
    def test_manifold_yes(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.update(_make_document(is_manifold=True))
        text = panel.status_section_text()
        assert "Yes" in text

    def test_manifold_no(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.update(_make_document(is_manifold=False))
        text = panel.status_section_text()
        assert "No" in text

    def test_volume_shown_when_manifold(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.update(_make_document(is_manifold=True, volume=1000.0))
        text = panel.status_section_text()
        assert "1,000.0" in text
        assert "mm" in text

    def test_volume_na_when_non_manifold(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.update(_make_document(is_manifold=False))
        text = panel.status_section_text()
        assert "N/A" in text


class TestInfoPanelUpdateClear:
    def test_update_clears_empty_state(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.update(_make_document())
        assert panel.is_empty is False

    def test_clear_after_update_resets_to_empty(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.update(_make_document())
        panel.clear()
        assert panel.is_empty is True
