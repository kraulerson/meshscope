# Format Conversion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Export As functionality to save the current mesh to STL (binary), OBJ, 3MF, or PLY with atomic writes, symlink detection, and pre-export warning dialogs.

**Architecture:** New `mesh_exporter.py` module converts MeshData → trimesh.Trimesh → file via trimesh.export(). Atomic write pattern (temp file + os.replace). MainWindow adds Export As action with QFileDialog and pre-export validation dialogs.

**Tech Stack:** trimesh (export), PySide6 (QFileDialog, QMessageBox), Python stdlib (tempfile, os)

---

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/meshscope/core/mesh_exporter.py` | MeshData → trimesh conversion, atomic file write, symlink detection, post-export validation |
| Modify | `src/meshscope/core/exceptions.py` | Add MeshExportError exception class |
| Modify | `src/meshscope/ui/main_window.py` | Export As action, QFileDialog, pre-export warning dialogs, status bar feedback |
| Create | `tests/unit/test_mesh_exporter.py` | Unit tests for export_mesh function |
| Modify | `tests/ui/test_main_window.py` | Integration tests for Export As action and menu |

---

### Task 1: MeshExportError exception

**Files:**
- Modify: `src/meshscope/core/exceptions.py`
- Create: `tests/unit/test_mesh_exporter.py` (started)

- [ ] **Step 1: Write failing test for MeshExportError**

Create `tests/unit/test_mesh_exporter.py`:

```python
"""Tests for mesh export functionality."""

from meshscope.core.exceptions import MeshExportError


class TestMeshExportError:
    def test_is_exception(self) -> None:
        err = MeshExportError("test error")
        assert isinstance(err, Exception)

    def test_has_user_message(self) -> None:
        err = MeshExportError("Export failed: permission denied")
        assert err.user_message == "Export failed: permission denied"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_mesh_exporter.py -v`
Expected: FAIL — `ImportError: cannot import name 'MeshExportError'`

- [ ] **Step 3: Add MeshExportError to exceptions.py**

Append to `src/meshscope/core/exceptions.py` after the `EmptyMeshError` class:

```python
class MeshExportError(Exception):
    """Base exception for all mesh export failures."""

    def __init__(self, user_message: str) -> None:
        self.user_message = user_message
        super().__init__(user_message)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_mesh_exporter.py -v`
Expected: All 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/core/exceptions.py tests/unit/test_mesh_exporter.py
git commit -m "feat(export): add MeshExportError exception class"
```

---

### Task 2: Core export_mesh function

**Files:**
- Modify: `tests/unit/test_mesh_exporter.py`
- Create: `src/meshscope/core/mesh_exporter.py`

- [ ] **Step 1: Write failing tests for export_mesh**

Append to `tests/unit/test_mesh_exporter.py`:

```python
from pathlib import Path

import numpy as np

from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.core.mesh_exporter import export_mesh


def _make_mesh() -> MeshData:
    """Create a simple triangle MeshData for export testing."""
    vertices = np.array(
        [[0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0]],
        dtype=np.float32,
    )
    faces = np.array([[0, 1, 2], [0, 2, 3]], dtype=np.uint32)
    normals = np.array([[0, 0, 1], [0, 0, 1]], dtype=np.float32)
    bb = BoundingBox(0.0, 0.0, 0.0, 10.0, 10.0, 0.0)
    meta = MeshMetadata(
        vertex_count=4,
        face_count=2,
        bounding_box=bb,
        surface_area_mm2=100.0,
        volume_mm3=None,
        is_manifold=False,
    )
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


class TestExportMeshSTL:
    def test_export_stl_creates_file(self, tmp_path: Path) -> None:
        out = tmp_path / "output.stl"
        export_mesh(_make_mesh(), out, "stl")
        assert out.exists()
        assert out.stat().st_size > 0

    def test_export_stl_binary_format(self, tmp_path: Path) -> None:
        out = tmp_path / "output.stl"
        export_mesh(_make_mesh(), out, "stl")
        # Binary STL: 80-byte header + 4-byte count + N*50 bytes
        data = out.read_bytes()
        assert len(data) == 80 + 4 + 2 * 50  # 2 triangles


class TestExportMeshOBJ:
    def test_export_obj_creates_file(self, tmp_path: Path) -> None:
        out = tmp_path / "output.obj"
        export_mesh(_make_mesh(), out, "obj")
        assert out.exists()
        assert out.stat().st_size > 0

    def test_export_obj_contains_vertices(self, tmp_path: Path) -> None:
        out = tmp_path / "output.obj"
        export_mesh(_make_mesh(), out, "obj")
        content = out.read_text()
        assert "v " in content
        assert "f " in content


class TestExportMesh3MF:
    def test_export_3mf_creates_file(self, tmp_path: Path) -> None:
        out = tmp_path / "output.3mf"
        export_mesh(_make_mesh(), out, "3mf")
        assert out.exists()
        assert out.stat().st_size > 0


class TestExportMeshPLY:
    def test_export_ply_creates_file(self, tmp_path: Path) -> None:
        out = tmp_path / "output.ply"
        export_mesh(_make_mesh(), out, "ply")
        assert out.exists()
        assert out.stat().st_size > 0


class TestExportMeshAtomicWrite:
    def test_no_temp_file_left_on_success(self, tmp_path: Path) -> None:
        out = tmp_path / "output.stl"
        export_mesh(_make_mesh(), out, "stl")
        # Only the output file should exist, no .tmp files
        files = list(tmp_path.iterdir())
        assert len(files) == 1
        assert files[0].name == "output.stl"

    def test_export_to_readonly_dir_raises(self, tmp_path: Path) -> None:
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)
        out = readonly_dir / "output.stl"
        try:
            export_mesh(_make_mesh(), out, "stl")
            assert False, "Should have raised MeshExportError"
        except MeshExportError as e:
            assert "Cannot write" in e.user_message or "Permission" in e.user_message or "denied" in e.user_message.lower() or "Export failed" in e.user_message
        finally:
            readonly_dir.chmod(0o755)


class TestExportMeshUnsupportedFormat:
    def test_unsupported_format_raises(self, tmp_path: Path) -> None:
        out = tmp_path / "output.xyz"
        try:
            export_mesh(_make_mesh(), out, "xyz")
            assert False, "Should have raised MeshExportError"
        except MeshExportError as e:
            assert "Unsupported" in e.user_message
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_mesh_exporter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'meshscope.core.mesh_exporter'`

- [ ] **Step 3: Implement export_mesh**

Create `src/meshscope/core/mesh_exporter.py`:

```python
"""Mesh export: MeshData → file with atomic write and validation."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import trimesh

from meshscope.core.exceptions import MeshExportError

if TYPE_CHECKING:
    from meshscope.core.mesh_data import MeshData

logger = logging.getLogger("meshscope.core.mesh_exporter")

SUPPORTED_EXPORT_FORMATS = {"stl", "obj", "3mf", "ply"}


def export_mesh(mesh: MeshData, path: Path, file_type: str) -> None:
    """Export mesh data to a file using atomic write.

    Converts MeshData to a trimesh.Trimesh, exports to a temp file,
    validates the output, then atomically renames to the final path.

    Raises MeshExportError on any failure.
    """
    if file_type not in SUPPORTED_EXPORT_FORMATS:
        raise MeshExportError(
            f"Unsupported export format: {file_type}. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXPORT_FORMATS))}"
        )

    # Convert MeshData → trimesh.Trimesh
    tm_mesh = trimesh.Trimesh(
        vertices=np.array(mesh.vertices, dtype=np.float64),
        faces=np.array(mesh.faces, dtype=np.int64),
        face_normals=np.array(mesh.normals, dtype=np.float64),
        process=False,
    )

    # Atomic write: temp file in same directory → rename
    target_dir = path.parent
    temp_fd = None
    temp_path = None

    try:
        temp_fd, temp_path_str = tempfile.mkstemp(
            suffix=f".{file_type}.tmp",
            dir=target_dir,
        )
        os.close(temp_fd)
        temp_fd = None
        temp_path = Path(temp_path_str)

        # Export via trimesh
        tm_mesh.export(str(temp_path), file_type=file_type)

        # Post-export validation
        if not temp_path.exists() or temp_path.stat().st_size == 0:
            raise MeshExportError(
                "Export produced empty file — mesh data may be corrupt."
            )

        # Atomic rename
        os.replace(str(temp_path), str(path))
        temp_path = None  # Prevent cleanup of renamed file

        logger.info("Exported %s as %s (%d bytes)", path.name, file_type, path.stat().st_size)

    except MeshExportError:
        raise
    except PermissionError as e:
        raise MeshExportError(f"Cannot write to {path}: Permission denied") from e
    except OSError as e:
        raise MeshExportError(f"Export failed: {e}") from e
    except Exception as e:
        raise MeshExportError(f"Export failed: {e}") from e
    finally:
        # Clean up temp file if it still exists
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass


def check_symlink(path: Path) -> Path | None:
    """Check if path contains a symlink. Returns resolved path if different, None if safe."""
    resolved = Path(os.path.realpath(path))
    if resolved != path.resolve():
        return resolved
    return None


def get_format_warning(file_type: str) -> str | None:
    """Return a warning message if the format has data loss implications."""
    warnings = {
        "obj": "OBJ format may recalculate face normals.",
    }
    return warnings.get(file_type)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_mesh_exporter.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/core/mesh_exporter.py tests/unit/test_mesh_exporter.py
git commit -m "feat(export): implement export_mesh with atomic write and format validation"
```

---

### Task 3: Symlink detection and format warning tests

**Files:**
- Modify: `tests/unit/test_mesh_exporter.py`

- [ ] **Step 1: Write tests for check_symlink and get_format_warning**

Append to `tests/unit/test_mesh_exporter.py`:

```python
from meshscope.core.mesh_exporter import check_symlink, get_format_warning


class TestCheckSymlink:
    def test_regular_path_returns_none(self, tmp_path: Path) -> None:
        target = tmp_path / "output.stl"
        assert check_symlink(target) is None

    def test_symlink_returns_resolved_path(self, tmp_path: Path) -> None:
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        link = tmp_path / "link"
        link.symlink_to(real_dir)
        target = link / "output.stl"
        resolved = check_symlink(target)
        assert resolved is not None
        assert "real" in str(resolved)


class TestGetFormatWarning:
    def test_obj_has_warning(self) -> None:
        warning = get_format_warning("obj")
        assert warning is not None
        assert "normal" in warning.lower()

    def test_stl_has_no_warning(self) -> None:
        assert get_format_warning("stl") is None

    def test_3mf_has_no_warning(self) -> None:
        assert get_format_warning("3mf") is None

    def test_ply_has_no_warning(self) -> None:
        assert get_format_warning("ply") is None
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_mesh_exporter.py -v`
Expected: All 16 tests PASS (10 existing + 6 new)

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_mesh_exporter.py
git commit -m "test(export): add symlink detection and format warning tests"
```

---

### Task 4: Round-trip tests (load → export → reload)

**Files:**
- Modify: `tests/unit/test_mesh_exporter.py`

- [ ] **Step 1: Write round-trip tests**

Append to `tests/unit/test_mesh_exporter.py`:

```python
from meshscope.core.mesh_loader import load_mesh


class TestExportRoundTrip:
    """Load a fixture, export to each format, reload, verify geometry preserved."""

    def test_roundtrip_stl(self, tmp_path: Path) -> None:
        doc = load_mesh(Path("tests/fixtures/valid/cube.stl"))
        out = tmp_path / "cube_export.stl"
        export_mesh(doc.mesh, out, "stl")
        reloaded = load_mesh(out)
        assert reloaded.mesh.metadata.vertex_count == doc.mesh.metadata.vertex_count
        assert reloaded.mesh.metadata.face_count == doc.mesh.metadata.face_count

    def test_roundtrip_obj(self, tmp_path: Path) -> None:
        doc = load_mesh(Path("tests/fixtures/valid/cube.stl"))
        out = tmp_path / "cube_export.obj"
        export_mesh(doc.mesh, out, "obj")
        reloaded = load_mesh(out)
        assert reloaded.mesh.metadata.face_count == doc.mesh.metadata.face_count

    def test_roundtrip_ply(self, tmp_path: Path) -> None:
        doc = load_mesh(Path("tests/fixtures/valid/cube.stl"))
        out = tmp_path / "cube_export.ply"
        export_mesh(doc.mesh, out, "ply")
        reloaded = load_mesh(out)
        assert reloaded.mesh.metadata.face_count == doc.mesh.metadata.face_count

    def test_roundtrip_3mf(self, tmp_path: Path) -> None:
        doc = load_mesh(Path("tests/fixtures/valid/cube.stl"))
        out = tmp_path / "cube_export.3mf"
        export_mesh(doc.mesh, out, "3mf")
        reloaded = load_mesh(out)
        assert reloaded.mesh.metadata.face_count == doc.mesh.metadata.face_count
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_mesh_exporter.py::TestExportRoundTrip -v`
Expected: All 4 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/unit/test_mesh_exporter.py
git commit -m "test(export): add load-export-reload round-trip tests for all formats"
```

---

### Task 5: MainWindow Export As action and menu

**Files:**
- Modify: `tests/ui/test_main_window.py`
- Modify: `src/meshscope/ui/main_window.py`

- [ ] **Step 1: Write failing tests for Export As integration**

Append to `tests/ui/test_main_window.py`:

```python
class TestMainWindowExportAction:
    def test_export_action_exists(self, window: MainWindow) -> None:
        assert hasattr(window, "export_action")

    def test_export_action_disabled_initially(self, window: MainWindow) -> None:
        assert not window.export_action.isEnabled()

    def test_export_action_enabled_after_load(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert window.export_action.isEnabled()

    def test_export_action_disabled_after_error(
        self, window: MainWindow, tmp_path: Path
    ) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert window.export_action.isEnabled()
        bad = tmp_path / "bad.stl"
        bad.write_bytes(b"not a real stl file")
        window._load_file(bad)
        assert not window.export_action.isEnabled()

    def test_export_action_in_file_menu(self, window: MainWindow) -> None:
        file_menu = None
        for action in window.menuBar().actions():
            if "File" in action.text():
                file_menu = action.menu()
                break
        assert file_menu is not None
        action_texts = [a.text() for a in file_menu.actions()]
        assert any("Export" in t for t in action_texts)

    def test_export_shortcut_is_ctrl_shift_s(self, window: MainWindow) -> None:
        assert window.export_action.shortcut() == QKeySequence("Ctrl+Shift+S")

    def test_export_action_in_toolbar(self, window: MainWindow) -> None:
        toolbar_actions = [a.text() for a in window.toolbar.actions()]
        assert any("Export" in t for t in toolbar_actions)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_main_window.py::TestMainWindowExportAction -v`
Expected: FAIL — `AttributeError: 'MainWindow' object has no attribute 'export_action'`

- [ ] **Step 3: Add Export As action to MainWindow**

Modify `src/meshscope/ui/main_window.py`:

Add import at top (after existing imports):
```python
from meshscope.core.mesh_exporter import check_symlink, export_mesh, get_format_warning
```

Add `QMessageBox` to the PySide6.QtWidgets import:
```python
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QStatusBar,
    QToolBar,
)
```

Add constant after FILE_FILTER:
```python
EXPORT_FILTER = (
    "STL Files (*.stl);;"
    "OBJ Files (*.obj);;"
    "3MF Files (*.3mf);;"
    "PLY Files (*.ply)"
)

EXPORT_FILTER_TO_TYPE = {
    "STL Files (*.stl)": "stl",
    "OBJ Files (*.obj)": "obj",
    "3MF Files (*.3mf)": "3mf",
    "PLY Files (*.ply)": "ply",
}
```

In `_create_actions`, after exit_action (line 114):
```python
        self.export_action = QAction("Export As...", self)
        self.export_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.export_action.setEnabled(False)
        self.export_action.setToolTip("Export mesh to another format")
        self.export_action.triggered.connect(self._on_export)
```

In `_create_menus`, in file_menu section, between open_action and the separator before exit (replace lines 119-122):
```python
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.export_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
```

In `_create_toolbar`, after open_action (line 149), add:
```python
        self.toolbar.addAction(self.export_action)
```

In `_set_render_actions_enabled`, add export_action:
```python
    def _set_render_actions_enabled(self, enabled: bool) -> None:
        self.wireframe_action.setEnabled(enabled)
        self.shading_action.setEnabled(enabled)
        self.fit_action.setEnabled(enabled)
        self.export_action.setEnabled(enabled)
```

Add export handler method after `_on_fit`:
```python
    def _on_export(self) -> None:
        """Handle Export As action."""
        if self._document is None:
            return

        path_str, selected_filter = QFileDialog.getSaveFileName(
            self, "Export As", "", EXPORT_FILTER
        )
        if not path_str:
            return

        path = Path(path_str)

        # Detect format from selected filter or file extension
        file_type = EXPORT_FILTER_TO_TYPE.get(selected_filter)
        if file_type is None:
            ext = path.suffix.lower().lstrip(".")
            file_type = ext if ext in {"stl", "obj", "3mf", "ply"} else None
        if file_type is None:
            QMessageBox.warning(
                self, "Export Error",
                "Could not determine export format. Use a supported extension (.stl, .obj, .3mf, .ply).",
            )
            return

        # Ensure correct extension
        expected_ext = f".{file_type}"
        if path.suffix.lower() != expected_ext:
            path = path.with_suffix(expected_ext)

        # Symlink check
        resolved = check_symlink(path)
        if resolved is not None:
            result = QMessageBox.warning(
                self, "Symlink Detected",
                f"Target resolves to:\n{resolved}\n\nContinue?",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            if result != QMessageBox.StandardButton.Ok:
                return

        # Overwrite source check
        if self._document.source_path and path.resolve() == Path(self._document.source_path).resolve():
            result = QMessageBox.warning(
                self, "Overwrite Source",
                "This will overwrite the currently loaded file. Continue?",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            if result != QMessageBox.StandardButton.Ok:
                return

        # Format data loss warning
        warning = get_format_warning(file_type)
        if warning:
            result = QMessageBox.warning(
                self, "Format Warning",
                f"{warning}\n\nContinue?",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            )
            if result != QMessageBox.StandardButton.Ok:
                return

        # Perform export
        try:
            export_mesh(self._document.mesh, path, file_type)
            self.statusBar().showMessage(f"Exported to {path.name}")
            logger.info("Exported to %s", path)
        except MeshExportError as e:
            QMessageBox.critical(self, "Export Error", e.user_message)
            logger.error("Export failed: %s", e.user_message)
```

Add `MeshExportError` to the imports:
```python
from meshscope.core.exceptions import MeshExportError, MeshLoadError
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_main_window.py tests/unit/test_mesh_exporter.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run full test suite**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/meshscope/ui/main_window.py tests/ui/test_main_window.py
git commit -m "feat(export): integrate Export As into MainWindow with dialogs and warnings"
```

---

### Task 6: Manual smoke test and final verification

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Run linting and type checking**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && ruff check src/meshscope/core/mesh_exporter.py src/meshscope/ui/main_window.py && ruff format --check src/meshscope/core/mesh_exporter.py src/meshscope/ui/main_window.py && mypy src/meshscope/core/mesh_exporter.py`
Expected: No errors

- [ ] **Step 3: Launch the application and visually verify**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m meshscope tests/fixtures/valid/cube.stl`

Verify:
- File menu has Export As... between Open and Exit
- Export As... is grayed out before loading a file
- After loading cube.stl, Export As... is enabled
- Ctrl+Shift+S opens save dialog
- STL is the default format in the dialog
- Exporting to each format creates a valid file
- Toolbar has Export button after Open

- [ ] **Step 4: Record the feature**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && bash scripts/test-gate.sh --record-feature "format-conversion"`

- [ ] **Step 5: Commit any final fixes if needed**

Only if smoke test revealed issues. Otherwise skip.
