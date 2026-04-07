"""Mesh Info Panel dock widget."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
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
        self._header.setFocusPolicy(Qt.FocusPolicy.TabFocus)
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
        self._size_xyz_label = QLabel()
        self._dimensions_section.content_layout.addWidget(self._size_xyz_label)

        # Inline unit warning inside Dimensions
        self._inline_unit_warning = QLabel(
            f"{_WARNING} Possible unit mismatch — dimensions may be in mm vs inches"
        )
        self._inline_unit_warning.setWordWrap(True)
        self._inline_unit_warning.setVisible(False)
        self._dimensions_section.content_layout.addWidget(self._inline_unit_warning)

        # Min/max collapsible sub-section inside Dimensions
        self._minmax_section = CollapsibleSection("Min / Max", expanded=False)
        self._minmax_label = QLabel()
        self._minmax_section.content_layout.addWidget(self._minmax_label)
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

        self._layout.addStretch()
        self._scroll.setWidget(self._content)

        self._is_empty = True

    @property
    def is_empty(self) -> bool:
        return self._is_empty

    def load(self, doc: MeshDocument) -> None:
        """Populate all sections with data from doc."""
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
        sep = " \u00d7 "
        self._size_xyz_label.setText(
            f"W{sep}D{sep}H: {x:.1f}{sep}{y:.1f}{sep}{z:.1f} mm"
        )
        self._minmax_label.setText(
            f"Min: ({bb.min_x:.1f}, {bb.min_y:.1f}, {bb.min_z:.1f})\n"
            f"Max: ({bb.max_x:.1f}, {bb.max_y:.1f}, {bb.max_z:.1f})"
        )

        # Status section
        manifold_str = "Yes" if meta.is_manifold else "No"
        self._manifold_label.setText(f"Manifold: {manifold_str}")
        if meta.is_manifold and meta.volume_mm3 is not None:
            volume_str = f"{meta.volume_mm3:,.1f} mm{_SUPERSCRIPT_3}"
        else:
            volume_str = "N/A"
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

    def update(self, doc: MeshDocument) -> None:  # type: ignore[override]
        """Populate all sections with data from the given MeshDocument."""
        self._populate(doc)

    def clear(self) -> None:
        """Reset panel to empty state."""
        self._placeholder.setVisible(True)
        self._file_section.setVisible(False)
        self._geometry_section.setVisible(False)
        self._dimensions_section.setVisible(False)
        self._status_section.setVisible(False)
        self._warning_banner.setVisible(False)
        self._inline_unit_warning.setVisible(False)
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
                self._size_xyz_label.text(),
                self._minmax_label.text(),
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
