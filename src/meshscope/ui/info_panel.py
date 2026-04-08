"""Mesh Info Panel dock widget."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDockWidget,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from meshscope.core.mesh_analysis import MeshAnalysis
    from meshscope.core.mesh_document import MeshDocument

# Unicode constants
_ARROW_DOWN = "\u25bc"
_ARROW_RIGHT = "\u25b6"
_CHECKMARK = "\u2713"
_WARNING = "\u26a0"
_SUPERSCRIPT_2 = "\u00b2"
_SUPERSCRIPT_3 = "\u00b3"


def _format_file_size(size_bytes: int) -> str:
    """Return a human-readable file size string (e.g. '4.0 MB')."""
    if size_bytes >= 1_073_741_824:
        return f"{size_bytes / 1_073_741_824:.1f} GB"
    if size_bytes >= 1_048_576:
        return f"{size_bytes / 1_048_576:.1f} MB"
    if size_bytes >= 1_024:
        return f"{size_bytes / 1_024:.1f} KB"
    return f"{size_bytes} B"


def _has_unit_mismatch_warning(warnings: list[str]) -> bool:
    """Return True if any warning indicates a unit mismatch."""
    for w in warnings:
        lower = w.lower()
        if "unit" in lower or "mismatch" in lower:
            return True
    return False


class CollapsibleSection(QWidget):
    """A section with a clickable header that toggles content visibility."""

    def __init__(
        self,
        title: str,
        parent: QWidget | None = None,
        *,
        expanded: bool = True,
    ) -> None:
        super().__init__(parent)
        self._expanded = expanded
        self._title = title

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header button
        self._header = QPushButton()
        self._header.setFlat(True)
        self._header.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._header.setStyleSheet(
            "QPushButton:focus { border: 2px solid #4a9eff; outline: none; }"
            "QPushButton {"
            " text-align: left; padding: 8px 10px; border: 2px solid transparent;"
            " }"
        )
        self._header.clicked.connect(self.toggle)
        self._update_header_text()
        layout.addWidget(self._header)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Plain)
        layout.addWidget(separator)

        # Content area
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(10, 6, 10, 10)
        self._content.setVisible(self._expanded)
        layout.addWidget(self._content)

    @property
    def is_expanded(self) -> bool:
        return self._expanded

    @property
    def header_button(self) -> QPushButton:
        return self._header

    @property
    def content_area(self) -> QWidget:
        return self._content

    @property
    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def toggle(self) -> None:
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        self._update_header_text()

    def _update_header_text(self) -> None:
        arrow = _ARROW_DOWN if self._expanded else _ARROW_RIGHT
        self._header.setText(f"{arrow} {self._title.upper()}")
        state = "expanded" if self._expanded else "collapsed"
        self._header.setAccessibleName(f"{self._title} section, {state}")


class InfoPanel(QDockWidget):
    """Dock widget displaying mesh file info, geometry, dimensions, and status."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Info", parent)
        self.setAccessibleName("Mesh Info Panel")
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )

        # Scroll area for content
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setWidget(self._scroll)

        # Main content widget
        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # --- Warning banner (hidden by default) ---
        self._warning_banner = QLabel()
        self._warning_banner.setWordWrap(True)
        self._warning_banner.setAccessibleName("Unit mismatch warning")
        self._warning_banner.setContentsMargins(8, 6, 8, 6)
        self._warning_banner.setVisible(False)
        self._layout.addWidget(self._warning_banner)

        # Placeholder label for empty state
        self._placeholder = QLabel("No mesh loaded")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setAccessibleName("No mesh loaded")
        self._layout.addWidget(self._placeholder)

        # --- File section ---
        self._file_section = CollapsibleSection("File")
        self._file_name_label = QLabel()
        self._file_format_label = QLabel()
        self._file_size_label = QLabel()
        self._file_section.content_layout.addWidget(self._file_name_label)
        self._file_section.content_layout.addWidget(self._file_format_label)
        self._file_section.content_layout.addWidget(self._file_size_label)
        self._file_section.setVisible(False)
        self._layout.addWidget(self._file_section)

        # --- Geometry section ---
        self._geometry_section = CollapsibleSection("Geometry")
        self._vertex_count_label = QLabel()
        self._face_count_label = QLabel()
        self._surface_area_label = QLabel()
        self._geometry_section.content_layout.addWidget(self._vertex_count_label)
        self._geometry_section.content_layout.addWidget(self._face_count_label)
        self._geometry_section.content_layout.addWidget(self._surface_area_label)
        self._geometry_section.setVisible(False)
        self._layout.addWidget(self._geometry_section)

        # --- Dimensions section ---
        self._dimensions_section = CollapsibleSection("Dimensions")
        self._size_x = QLabel()
        self._size_y = QLabel()
        self._size_z = QLabel()
        self._dimensions_section.content_layout.addWidget(self._size_x)
        self._dimensions_section.content_layout.addWidget(self._size_y)
        self._dimensions_section.content_layout.addWidget(self._size_z)

        # Inline unit warning inside Dimensions
        self._inline_unit_warning = QLabel(
            f"{_WARNING} Possible unit mismatch — dimensions may be in mm vs inches"
        )
        self._inline_unit_warning.setWordWrap(True)
        self._inline_unit_warning.setVisible(False)
        self._dimensions_section.content_layout.addWidget(self._inline_unit_warning)

        # Min/max collapsible sub-section inside Dimensions
        self._minmax_section = CollapsibleSection("Min / Max", expanded=False)
        self._min_max_x = QLabel()
        self._min_max_y = QLabel()
        self._min_max_z = QLabel()
        self._minmax_section.content_layout.addWidget(self._min_max_x)
        self._minmax_section.content_layout.addWidget(self._min_max_y)
        self._minmax_section.content_layout.addWidget(self._min_max_z)
        self._dimensions_section.content_layout.addWidget(self._minmax_section)

        self._dimensions_section.setVisible(False)
        self._layout.addWidget(self._dimensions_section)

        # --- Status section ---
        self._status_section = CollapsibleSection("Status")
        self._manifold_label = QLabel()
        self._volume_label = QLabel()
        self._status_section.content_layout.addWidget(self._manifold_label)
        self._status_section.content_layout.addWidget(self._volume_label)
        self._status_section.setVisible(False)
        self._layout.addWidget(self._status_section)

        # --- Analysis section ---
        self._analysis_section = CollapsibleSection("Analysis")
        self._watertight_label = QLabel()
        self._holes_label = QLabel()
        self._open_edges_label = QLabel()
        self._non_manifold_label = QLabel()
        self._degenerate_label = QLabel()
        self._analysis_section.content_layout.addWidget(self._watertight_label)
        self._analysis_section.content_layout.addWidget(self._holes_label)
        self._analysis_section.content_layout.addWidget(self._open_edges_label)
        self._analysis_section.content_layout.addWidget(self._non_manifold_label)
        self._analysis_section.content_layout.addWidget(self._degenerate_label)
        self._highlight_checkbox = QCheckBox("Highlight in viewport")
        self._analysis_section.content_layout.addWidget(self._highlight_checkbox)
        self._analysis_section.setVisible(False)
        self._layout.addWidget(self._analysis_section)

        self._layout.addStretch()
        self._scroll.setWidget(self._content)

        self._is_empty = True
        self._apply_styles()

    def _apply_styles(self) -> None:
        """Apply dark theme styles matching the main application."""
        self._warning_banner.setStyleSheet(
            "QLabel {"
            "  background-color: #4a3000;"
            "  border-left: 3px solid #f0a030;"
            "  padding: 8px 10px;"
            "  color: #e0e0e0;"
            "  font-size: 12px;"
            "}"
        )
        self._inline_unit_warning.setStyleSheet(
            "QLabel {"
            "  background-color: #3a3000;"
            "  padding: 4px 8px;"
            "  color: #d0a040;"
            "  font-size: 11px;"
            "}"
        )

    @property
    def is_empty(self) -> bool:
        return self._is_empty

    def set_document(self, doc: MeshDocument) -> None:
        """Populate all sections with data from the given MeshDocument."""
        self._populate(doc)

    def _populate(self, doc: MeshDocument) -> None:
        """Internal: populate all sections from a MeshDocument."""
        meta = doc.mesh.metadata
        bb = meta.bounding_box

        # File section
        filename = os.path.basename(doc.source_path)
        self._file_name_label.setText(f"Name: {filename}")
        self._file_format_label.setText(f"Format: {doc.source_format.upper()}")
        self._file_size_label.setText(
            f"Size: {_format_file_size(doc.source_size_bytes)}"
        )

        # Geometry section
        self._vertex_count_label.setText(f"Vertices: {meta.vertex_count:,}")
        self._face_count_label.setText(f"Faces: {meta.face_count:,}")
        self._surface_area_label.setText(
            f"Surface area: {meta.surface_area_mm2:.1f} mm{_SUPERSCRIPT_2}"
        )

        # Dimensions section
        x, y, z = bb.size_x, bb.size_y, bb.size_z
        self._size_x.setText(f"Size X: {x:,.1f} mm")
        self._size_y.setText(f"Size Y: {y:,.1f} mm")
        self._size_z.setText(f"Size Z: {z:,.1f} mm")
        self._min_max_x.setText(f"X: [{bb.min_x:.1f}, {bb.max_x:.1f}]")
        self._min_max_y.setText(f"Y: [{bb.min_y:.1f}, {bb.max_y:.1f}]")
        self._min_max_z.setText(f"Z: [{bb.min_z:.1f}, {bb.max_z:.1f}]")

        # Status section
        if meta.is_manifold:
            manifold_text = f"{_CHECKMARK} Manifold: Yes"
            manifold_accessible = "Manifold: Yes"
        else:
            manifold_text = f"{_WARNING} Manifold: No"
            manifold_accessible = "Manifold: No"
        self._manifold_label.setText(manifold_text)
        self._manifold_label.setAccessibleName(manifold_accessible)
        if meta.is_manifold and meta.volume_mm3 is not None:
            volume_str = f"{meta.volume_mm3:,.1f} mm{_SUPERSCRIPT_3}"
        else:
            volume_str = "N/A (non-manifold)"
        self._volume_label.setText(f"Volume: {volume_str}")

        # Unit mismatch warning
        has_mismatch = _has_unit_mismatch_warning(doc.warnings)
        if has_mismatch:
            # Find the first matching warning text for the banner
            mismatch_text = next(
                (
                    w
                    for w in doc.warnings
                    if "unit" in w.lower() or "mismatch" in w.lower()
                ),
                "Possible unit mismatch detected.",
            )
            self._warning_banner.setText(f"{_WARNING} {mismatch_text}")
            self._warning_banner.setVisible(True)
            self._inline_unit_warning.setVisible(True)
        else:
            self._warning_banner.setVisible(False)
            self._inline_unit_warning.setVisible(False)

        # Show sections, hide placeholder
        self._placeholder.setVisible(False)
        self._file_section.setVisible(True)
        self._geometry_section.setVisible(True)
        self._dimensions_section.setVisible(True)
        self._status_section.setVisible(True)

        self._is_empty = False

    def clear(self) -> None:
        """Reset panel to empty state."""
        self._placeholder.setVisible(True)
        self._file_section.setVisible(False)
        self._geometry_section.setVisible(False)
        self._dimensions_section.setVisible(False)
        self._status_section.setVisible(False)
        self._warning_banner.setVisible(False)
        self._inline_unit_warning.setVisible(False)
        self.clear_analysis()
        self._is_empty = True

    # --- Test accessor methods ---

    def file_section_text(self) -> str:
        """Return combined text of all file section labels (for testing)."""
        return "\n".join(
            [
                self._file_name_label.text(),
                self._file_format_label.text(),
                self._file_size_label.text(),
            ]
        )

    def geometry_section_text(self) -> str:
        """Return combined text of all geometry section labels (for testing)."""
        return "\n".join(
            [
                self._vertex_count_label.text(),
                self._face_count_label.text(),
                self._surface_area_label.text(),
            ]
        )

    def dimensions_section_text(self) -> str:
        """Return combined text of dimensions section labels (for testing)."""
        return "\n".join(
            [
                self._size_x.text(),
                self._size_y.text(),
                self._size_z.text(),
                self._min_max_x.text(),
                self._min_max_y.text(),
                self._min_max_z.text(),
            ]
        )

    def status_section_text(self) -> str:
        """Return combined text of status section labels (for testing)."""
        return "\n".join(
            [
                self._manifold_label.text(),
                self._volume_label.text(),
            ]
        )

    def has_min_max_subsection(self) -> bool:
        """Return True if the min/max collapsible sub-section exists (for testing)."""
        return self._minmax_section is not None

    def warning_banner_visible(self) -> bool:
        """Return True if the warning banner is not hidden (for testing).

        Uses isHidden() rather than isVisible() because isVisible() returns
        False for any widget whose top-level parent has not been shown — which
        is the normal state during unit tests.
        """
        return not self._warning_banner.isHidden()

    def warning_banner_text(self) -> str:
        """Return the text of the warning banner (for testing)."""
        return self._warning_banner.text()

    def inline_unit_warning_visible(self) -> bool:
        """Return True if the inline unit warning in Dimensions is not hidden.

        For testing use only.
        """
        return not self._inline_unit_warning.isHidden()

    def show_analysis(self, analysis: MeshAnalysis) -> None:
        """Populate the Analysis section from a MeshAnalysis result and show it."""
        # Watertight
        if analysis.is_watertight:
            self._watertight_label.setText(f"{_CHECKMARK} Watertight: Yes")
        else:
            self._watertight_label.setText(f"{_WARNING} Watertight: No")

        # Holes
        if analysis.hole_count == 0:
            self._holes_label.setText(f"{_CHECKMARK} Holes: 0")
        else:
            self._holes_label.setText(f"{_WARNING} Holes: {analysis.hole_count}")

        # Open edges
        if analysis.open_edge_count == 0:
            self._open_edges_label.setText(f"{_CHECKMARK} Open edges: 0")
        else:
            self._open_edges_label.setText(
                f"{_WARNING} Open edges: {analysis.open_edge_count}"
            )

        # Non-manifold edges
        if analysis.non_manifold_edge_count == 0:
            self._non_manifold_label.setText(f"{_CHECKMARK} Non-manifold edges: 0")
        else:
            self._non_manifold_label.setText(
                f"{_WARNING} Non-manifold edges: {analysis.non_manifold_edge_count}"
            )

        # Degenerate faces
        if analysis.degenerate_face_count == 0:
            self._degenerate_label.setText(f"{_CHECKMARK} Degenerate faces: 0")
        else:
            self._degenerate_label.setText(
                f"{_WARNING} Degenerate faces: {analysis.degenerate_face_count}"
            )

        # Auto-check highlight if any issues found
        has_issues = (
            not analysis.is_watertight
            or analysis.hole_count > 0
            or analysis.open_edge_count > 0
            or analysis.non_manifold_edge_count > 0
            or analysis.degenerate_face_count > 0
        )
        self._highlight_checkbox.setChecked(has_issues)

        self._analysis_section.setVisible(True)

    def clear_analysis(self) -> None:
        """Hide the Analysis section and reset its state."""
        self._analysis_section.setVisible(False)
        self._highlight_checkbox.setChecked(False)

    @property
    def highlight_checkbox(self) -> QCheckBox:
        """Return the 'Highlight in viewport' checkbox."""
        return self._highlight_checkbox

    def analysis_section_visible(self) -> bool:
        """Return True if the Analysis section is not hidden (for testing)."""
        return not self._analysis_section.isHidden()

    def analysis_section_text(self) -> str:
        """Return combined text of all analysis section labels (for testing)."""
        return "\n".join(
            [
                self._watertight_label.text(),
                self._holes_label.text(),
                self._open_edges_label.text(),
                self._non_manifold_label.text(),
                self._degenerate_label.text(),
            ]
        )

    def has_highlight_checkbox(self) -> bool:
        """Return True if the highlight checkbox exists (for testing)."""
        return self._highlight_checkbox is not None
