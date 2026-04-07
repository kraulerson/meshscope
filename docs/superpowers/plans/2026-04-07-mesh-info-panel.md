# Mesh Info Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a dockable info panel that displays mesh metadata (file info, geometry counts, bounding box dimensions, manifold/volume status) with collapsible sections and a unit mismatch warning banner.

**Architecture:** Direct method call pattern — MainWindow calls `info_panel.update(doc)` after load, `info_panel.clear()` on error. InfoPanel is a QDockWidget with four collapsible sections implemented via togglable QWidget visibility. No signals or observer pattern.

**Tech Stack:** PySide6 (QDockWidget, QLabel, QVBoxLayout, QFrame), Python stdlib

---

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/meshscope/ui/info_panel.py` | InfoPanel QDockWidget with collapsible sections, update/clear methods |
| Modify | `src/meshscope/ui/main_window.py` | Create InfoPanel, dock it, wire update/clear into load flow, add View menu toggle + shortcut |
| Create | `tests/ui/test_info_panel.py` | All info panel unit and integration tests |

---

### Task 1: InfoPanel skeleton with empty state

**Files:**
- Create: `tests/ui/test_info_panel.py`
- Create: `src/meshscope/ui/info_panel.py`

- [ ] **Step 1: Write failing tests for InfoPanel construction and empty state**

```python
"""Tests for the Mesh Info Panel."""

from PySide6.QtCore import Qt
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_info_panel.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'meshscope.ui.info_panel'`

- [ ] **Step 3: Implement InfoPanel skeleton**

```python
"""Dockable info panel displaying mesh metadata."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


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

        # Placeholder label for empty state
        self._placeholder = QLabel("No mesh loaded")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setAccessibleName("No mesh loaded")
        self._layout.addWidget(self._placeholder)

        self._layout.addStretch()
        self._scroll.setWidget(self._content)

        self._is_empty = True

    @property
    def is_empty(self) -> bool:
        return self._is_empty

    def clear(self) -> None:
        """Reset panel to empty state."""
        self._placeholder.setVisible(True)
        self._is_empty = True
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_info_panel.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/ui/test_info_panel.py src/meshscope/ui/info_panel.py
git commit -m "feat(info-panel): add InfoPanel skeleton with empty state"
```

---

### Task 2: Collapsible section widget

**Files:**
- Modify: `tests/ui/test_info_panel.py`
- Modify: `src/meshscope/ui/info_panel.py`

- [ ] **Step 1: Write failing tests for collapsible section**

Append to `tests/ui/test_info_panel.py`:

```python
from meshscope.ui.info_panel import CollapsibleSection


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_info_panel.py::TestCollapsibleSection -v`
Expected: FAIL — `ImportError: cannot import name 'CollapsibleSection'`

- [ ] **Step 3: Implement CollapsibleSection**

Add to `src/meshscope/ui/info_panel.py` before the `InfoPanel` class:

```python
from PySide6.QtWidgets import (
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


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
        arrow = "\u25BC" if self._expanded else "\u25B6"
        self._header.setText(f"{arrow} {self._title.upper()}")
        state = "expanded" if self._expanded else "collapsed"
        self._header.setAccessibleName(f"{self._title} section, {state}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_info_panel.py -v`
Expected: All 11 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/ui/test_info_panel.py src/meshscope/ui/info_panel.py
git commit -m "feat(info-panel): add CollapsibleSection widget"
```

---

### Task 3: Four data sections with update() method

**Files:**
- Modify: `tests/ui/test_info_panel.py`
- Modify: `src/meshscope/ui/info_panel.py`

This task populates all four sections (File, Geometry, Dimensions, Status) in a single pass, since they all follow the same label-value pattern and share the same `update(doc)` entry point.

- [ ] **Step 1: Write failing tests for update()**

Append to `tests/ui/test_info_panel.py`:

```python
import numpy as np

from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.core.mesh_document import MeshDocument


def _make_document(
    *,
    is_manifold: bool = True,
    volume: float | None = 1000.0,
    warnings: list[str] | None = None,
) -> MeshDocument:
    """Create a MeshDocument with known metadata for testing."""
    bb = BoundingBox(
        min_x=0.0, min_y=0.0, min_z=0.0,
        max_x=10.0, max_y=20.0, max_z=30.0,
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
        # 4200000 bytes = 4.0 MB
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
        assert "10.0" in text  # size_x
        assert "20.0" in text  # size_y
        assert "30.0" in text  # size_z

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_info_panel.py -v`
Expected: FAIL — `AttributeError: 'InfoPanel' object has no attribute 'update'`

- [ ] **Step 3: Implement update(), clear(), and data sections**

Replace the `InfoPanel` class in `src/meshscope/ui/info_panel.py` with the full implementation. Key additions:

- Four `CollapsibleSection` instances created in `__init__`
- `update(doc: MeshDocument)` method that reads metadata and populates labels
- `clear()` method that hides sections and shows placeholder
- Helper `_format_file_size()` for human-readable bytes
- Section text accessor methods for testing: `file_section_text()`, `geometry_section_text()`, `dimensions_section_text()`, `status_section_text()`, `has_min_max_subsection()`

```python
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

        # Warning banner (hidden by default)
        self._warning_banner = QLabel()
        self._warning_banner.setWordWrap(True)
        self._warning_banner.setAccessibleName("Unit mismatch warning")
        self._warning_banner.setVisible(False)
        self._layout.addWidget(self._warning_banner)

        # Sections
        self._file_section = CollapsibleSection("File")
        self._geometry_section = CollapsibleSection("Geometry")
        self._dimensions_section = CollapsibleSection("Dimensions")
        self._status_section = CollapsibleSection("Status")

        # Section data labels — File
        self._file_name = QLabel()
        self._file_format = QLabel()
        self._file_size = QLabel()
        self._file_section.content_layout.addWidget(self._file_name)
        self._file_section.content_layout.addWidget(self._file_format)
        self._file_section.content_layout.addWidget(self._file_size)

        # Section data labels — Geometry
        self._vertex_count = QLabel()
        self._face_count = QLabel()
        self._surface_area = QLabel()
        self._geometry_section.content_layout.addWidget(self._vertex_count)
        self._geometry_section.content_layout.addWidget(self._face_count)
        self._geometry_section.content_layout.addWidget(self._surface_area)

        # Section data labels — Dimensions
        self._size_x = QLabel()
        self._size_y = QLabel()
        self._size_z = QLabel()
        self._dimensions_section.content_layout.addWidget(self._size_x)
        self._dimensions_section.content_layout.addWidget(self._size_y)
        self._dimensions_section.content_layout.addWidget(self._size_z)

        # Min/max collapsible sub-section
        self._min_max_section = CollapsibleSection("Min/Max Coordinates", expanded=False)
        self._min_max_x = QLabel()
        self._min_max_y = QLabel()
        self._min_max_z = QLabel()
        self._min_max_section.content_layout.addWidget(self._min_max_x)
        self._min_max_section.content_layout.addWidget(self._min_max_y)
        self._min_max_section.content_layout.addWidget(self._min_max_z)
        self._dimensions_section.content_layout.addWidget(self._min_max_section)

        # Inline unit warning (within dimensions section)
        self._inline_unit_warning = QLabel()
        self._inline_unit_warning.setWordWrap(True)
        self._inline_unit_warning.setVisible(False)
        self._dimensions_section.content_layout.addWidget(self._inline_unit_warning)

        # Section data labels — Status
        self._manifold_status = QLabel()
        self._volume = QLabel()
        self._status_section.content_layout.addWidget(self._manifold_status)
        self._status_section.content_layout.addWidget(self._volume)

        # Add sections to layout
        for section in (
            self._file_section,
            self._geometry_section,
            self._dimensions_section,
            self._status_section,
        ):
            section.setVisible(False)
            self._layout.addWidget(section)

        # Placeholder label for empty state
        self._placeholder = QLabel("No mesh loaded")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setAccessibleName("No mesh loaded")
        self._layout.addWidget(self._placeholder)

        self._layout.addStretch()
        self._scroll.setWidget(self._content)

        self._is_empty = True

    @property
    def is_empty(self) -> bool:
        return self._is_empty

    def update(self, doc: MeshDocument) -> None:
        """Populate panel from a loaded MeshDocument."""
        from pathlib import Path

        meta = doc.mesh.metadata
        bb = meta.bounding_box

        # File section
        self._file_name.setText(f"Name: {Path(doc.source_path).name}")
        self._file_format.setText(f"Format: {doc.source_format.upper()}")
        self._file_size.setText(f"Size: {_format_file_size(doc.source_size_bytes)}")

        # Geometry section
        self._vertex_count.setText(f"Vertices: {meta.vertex_count:,}")
        self._face_count.setText(f"Faces: {meta.face_count:,}")
        self._surface_area.setText(
            f"Surface area: {meta.surface_area_mm2:,.1f} mm\u00B2"
        )

        # Dimensions section
        self._size_x.setText(f"Size X: {bb.size_x:,.1f} mm")
        self._size_y.setText(f"Size Y: {bb.size_y:,.1f} mm")
        self._size_z.setText(f"Size Z: {bb.size_z:,.1f} mm")

        self._min_max_x.setText(f"X: [{bb.min_x:,.1f}, {bb.max_x:,.1f}]")
        self._min_max_y.setText(f"Y: [{bb.min_y:,.1f}, {bb.max_y:,.1f}]")
        self._min_max_z.setText(f"Z: [{bb.min_z:,.1f}, {bb.max_z:,.1f}]")

        # Status section
        if meta.is_manifold:
            self._manifold_status.setText("\u2713 Manifold: Yes")
            self._manifold_status.setAccessibleName("Manifold: Yes")
        else:
            self._manifold_status.setText("\u26A0 Manifold: No")
            self._manifold_status.setAccessibleName("Manifold: No")

        if meta.volume_mm3 is not None:
            self._volume.setText(f"Volume: {meta.volume_mm3:,.1f} mm\u00B3")
        else:
            self._volume.setText("Volume: N/A (non-manifold)")

        # Unit mismatch warnings
        unit_warnings = [w for w in doc.warnings if "unit" in w.lower() or "mismatch" in w.lower()]
        if unit_warnings:
            warning_text = unit_warnings[0]
            self._warning_banner.setText(f"\u26A0 {warning_text}")
            self._warning_banner.setVisible(True)
            self._inline_unit_warning.setText(f"\u26A0 {warning_text}")
            self._inline_unit_warning.setVisible(True)
        else:
            self._warning_banner.setVisible(False)
            self._inline_unit_warning.setVisible(False)

        # Show sections, hide placeholder
        self._placeholder.setVisible(False)
        for section in (
            self._file_section,
            self._geometry_section,
            self._dimensions_section,
            self._status_section,
        ):
            section.setVisible(True)

        self._is_empty = False

    def clear(self) -> None:
        """Reset panel to empty state."""
        self._placeholder.setVisible(True)
        self._warning_banner.setVisible(False)
        self._inline_unit_warning.setVisible(False)
        for section in (
            self._file_section,
            self._geometry_section,
            self._dimensions_section,
            self._status_section,
        ):
            section.setVisible(False)
        self._is_empty = True

    # --- Test accessors ---

    def file_section_text(self) -> str:
        return (
            f"{self._file_name.text()} {self._file_format.text()} "
            f"{self._file_size.text()}"
        )

    def geometry_section_text(self) -> str:
        return (
            f"{self._vertex_count.text()} {self._face_count.text()} "
            f"{self._surface_area.text()}"
        )

    def dimensions_section_text(self) -> str:
        return (
            f"{self._size_x.text()} {self._size_y.text()} {self._size_z.text()}"
        )

    def status_section_text(self) -> str:
        return f"{self._manifold_status.text()} {self._volume.text()}"

    def has_min_max_subsection(self) -> bool:
        return self._min_max_section is not None and self._min_max_x.text() != ""


def _format_file_size(size_bytes: int) -> str:
    """Format bytes as human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_info_panel.py -v`
Expected: All 24 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/ui/test_info_panel.py src/meshscope/ui/info_panel.py
git commit -m "feat(info-panel): populate all four data sections with update/clear"
```

---

### Task 4: Unit mismatch warning banner

**Files:**
- Modify: `tests/ui/test_info_panel.py`
- Modify: `src/meshscope/ui/info_panel.py` (already implemented in Task 3 — this task adds tests)

- [ ] **Step 1: Write failing tests for warning banner**

Append to `tests/ui/test_info_panel.py`:

```python
class TestInfoPanelUnitWarning:
    def test_no_warning_when_no_mismatch(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.update(_make_document(warnings=[]))
        assert panel.warning_banner_visible() is False

    def test_warning_shown_when_unit_mismatch(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        doc = _make_document(
            warnings=["Dimensions may indicate a unit mismatch. Consider scaling by 25.4"]
        )
        panel.update(doc)
        assert panel.warning_banner_visible() is True

    def test_warning_banner_text_contains_message(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        doc = _make_document(
            warnings=["Dimensions may indicate a unit mismatch. Consider scaling by 25.4"]
        )
        panel.update(doc)
        assert "unit mismatch" in panel.warning_banner_text().lower()

    def test_inline_warning_shown_in_dimensions(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        doc = _make_document(
            warnings=["Dimensions may indicate a unit mismatch. Consider scaling by 25.4"]
        )
        panel.update(doc)
        assert panel.inline_unit_warning_visible() is True

    def test_warning_cleared_on_clear(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        doc = _make_document(
            warnings=["Dimensions may indicate a unit mismatch. Consider scaling by 25.4"]
        )
        panel.update(doc)
        panel.clear()
        assert panel.warning_banner_visible() is False

    def test_warning_hidden_on_update_without_mismatch(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        doc_warn = _make_document(
            warnings=["Dimensions may indicate a unit mismatch. Consider scaling by 25.4"]
        )
        panel.update(doc_warn)
        assert panel.warning_banner_visible() is True
        # Load a new mesh with no warnings
        panel.update(_make_document(warnings=[]))
        assert panel.warning_banner_visible() is False

    def test_non_unit_warnings_do_not_trigger_banner(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        doc = _make_document(warnings=["OBJ: material library not supported"])
        panel.update(doc)
        assert panel.warning_banner_visible() is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_info_panel.py::TestInfoPanelUnitWarning -v`
Expected: FAIL — `AttributeError: 'InfoPanel' object has no attribute 'warning_banner_visible'`

- [ ] **Step 3: Add test accessor methods to InfoPanel**

Add to the `InfoPanel` class after the existing test accessors:

```python
    def warning_banner_visible(self) -> bool:
        return self._warning_banner.isVisible()

    def warning_banner_text(self) -> str:
        return self._warning_banner.text()

    def inline_unit_warning_visible(self) -> bool:
        return self._inline_unit_warning.isVisible()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_info_panel.py -v`
Expected: All 31 tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/ui/test_info_panel.py src/meshscope/ui/info_panel.py
git commit -m "test(info-panel): add unit mismatch warning banner tests"
```

---

### Task 5: MainWindow integration

**Files:**
- Modify: `tests/ui/test_main_window.py`
- Modify: `src/meshscope/ui/main_window.py`

- [ ] **Step 1: Write failing tests for MainWindow integration**

Append to `tests/ui/test_main_window.py`:

```python
from meshscope.ui.info_panel import InfoPanel


class TestMainWindowInfoPanel:
    def test_info_panel_exists(self, window: MainWindow) -> None:
        assert hasattr(window, "_info_panel")
        assert isinstance(window._info_panel, InfoPanel)

    def test_info_panel_starts_empty(self, window: MainWindow) -> None:
        assert window._info_panel.is_empty is True

    def test_info_panel_in_view_menu(self, window: MainWindow) -> None:
        view_menu = None
        for action in window.menuBar().actions():
            if "View" in action.text():
                view_menu = action.menu()
                break
        assert view_menu is not None
        action_texts = [a.text() for a in view_menu.actions()]
        assert any("Info" in t for t in action_texts)

    def test_info_panel_populated_after_load(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert window._info_panel.is_empty is False

    def test_info_panel_cleared_on_error(
        self, window: MainWindow, tmp_path: Path
    ) -> None:
        # First load a valid file
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert window._info_panel.is_empty is False
        # Then load a bad file
        bad = tmp_path / "bad.stl"
        bad.write_bytes(b"not a real stl file")
        window._load_file(bad)
        assert window._info_panel.is_empty is True

    def test_info_toggle_shortcut_is_i(self, window: MainWindow) -> None:
        toggle_action = window._info_panel.toggleViewAction()
        assert toggle_action.shortcut() == QKeySequence("I")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_main_window.py::TestMainWindowInfoPanel -v`
Expected: FAIL — `AttributeError: 'MainWindow' object has no attribute '_info_panel'`

- [ ] **Step 3: Integrate InfoPanel into MainWindow**

Modify `src/meshscope/ui/main_window.py`:

Add import at the top (after the `ViewportWidget` import):

```python
from meshscope.ui.info_panel import InfoPanel
```

In `__init__`, after the viewport setup (after line 50 `self.setCentralWidget(self._viewport)`) and before actions:

```python
        # Info panel (dock widget, left)
        self._info_panel = InfoPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._info_panel)
```

In `_create_menus`, in the view_menu section (after `view_menu.addAction(self.fit_action)`, line 123), add:

```python
        view_menu.addSeparator()
        info_toggle = self._info_panel.toggleViewAction()
        info_toggle.setShortcut(QKeySequence("I"))
        view_menu.addAction(info_toggle)
```

In `_load_file`, after `self._document = doc` (line 173), add:

```python
        self._info_panel.update(doc)
```

In `_set_state_error`, after `self._document = None` (line 201), add:

```python
        self._info_panel.clear()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_main_window.py tests/ui/test_info_panel.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run the full test suite**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest -v`
Expected: All tests PASS (153 existing + new info panel tests)

- [ ] **Step 6: Commit**

```bash
git add src/meshscope/ui/main_window.py tests/ui/test_main_window.py
git commit -m "feat(info-panel): integrate InfoPanel into MainWindow with View menu toggle"
```

---

### Task 6: Accessibility pass and styling

**Files:**
- Modify: `tests/ui/test_info_panel.py`
- Modify: `src/meshscope/ui/info_panel.py`

- [ ] **Step 1: Write failing tests for accessibility**

Append to `tests/ui/test_info_panel.py`:

```python
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
        panel.update(_make_document(is_manifold=True))
        assert "Yes" in panel._manifold_status.accessibleName()

    def test_non_manifold_status_has_accessible_name(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.update(_make_document(is_manifold=False))
        assert "No" in panel._manifold_status.accessibleName()

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
            assert section.header_button.focusPolicy() == Qt.FocusPolicy.TabFocus
```

- [ ] **Step 2: Run tests to verify they pass (these should already pass from prior implementation)**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_info_panel.py::TestInfoPanelAccessibility -v`
Expected: All 6 tests PASS (accessibility was built into the implementation)

- [ ] **Step 3: Add dark theme styling to InfoPanel**

Add a `_apply_styles()` method to `InfoPanel.__init__` (call at end of `__init__`):

```python
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
```

- [ ] **Step 4: Run full test suite**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/ui/test_info_panel.py src/meshscope/ui/info_panel.py
git commit -m "feat(info-panel): add accessibility tests and dark theme styling"
```

---

### Task 7: Manual smoke test and final verification

**Files:** None (verification only)

- [ ] **Step 1: Run the full test suite**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Run linting and type checking**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && ruff check src/meshscope/ui/info_panel.py && ruff format --check src/meshscope/ui/info_panel.py && mypy src/meshscope/ui/info_panel.py`
Expected: No errors

- [ ] **Step 3: Launch the application and visually verify**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m meshscope tests/fixtures/valid/cube.stl`

Verify:
- Info panel appears docked on the left
- Four sections visible: File, Geometry, Dimensions, Status
- File shows: cube.stl, STL, correct file size
- Geometry shows: 8 vertices, 12 faces, 600.0 mm² surface area
- Dimensions shows: 10.0 x 10.0 x 10.0 mm
- Status shows: Manifold Yes with checkmark, Volume 1,000.0 mm³
- Sections collapse/expand on click
- Min/Max sub-section starts collapsed
- Press I to toggle panel visibility
- View menu has Info toggle entry

- [ ] **Step 4: Record the feature**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && bash scripts/test-gate.sh --record-feature "mesh-info-panel"`

- [ ] **Step 5: Commit any final fixes if needed**

Only if smoke test revealed issues. Otherwise skip.
