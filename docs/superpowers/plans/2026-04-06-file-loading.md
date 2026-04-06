# File Loading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Load STL, OBJ, 3MF, and PLY mesh files into an in-memory MeshDocument with full validation, error handling, and computed metadata.

**Architecture:** Pure data layer with no UI. `load_mesh(path)` validates, parses via trimesh, and returns a `MeshDocument` or raises a typed exception. MeshData is an immutable frozen dataclass; MeshDocument is the mutable session wrapper.

**Tech Stack:** Python 3.13, trimesh 4.7.4, numpy 2.2.6, pytest 8.4.1

---

## File Structure

| File | Responsibility |
|---|---|
| Create: `src/meshscope/core/exceptions.py` | Custom exception hierarchy with user-facing messages |
| Create: `src/meshscope/core/mesh_data.py` | BoundingBox, MeshMetadata, MeshData frozen dataclasses |
| Create: `src/meshscope/core/undo_stack.py` | UndoStack ring buffer (shell for Features 7-8) |
| Create: `src/meshscope/core/mesh_document.py` | MeshDocument mutable session wrapper |
| Create: `src/meshscope/core/mesh_loader.py` | validate_path, detect_format, parse_mesh, load_mesh |
| Create: `tests/unit/test_exceptions.py` | Exception hierarchy and user_message behavior |
| Create: `tests/unit/test_mesh_data.py` | Dataclass construction and metadata |
| Create: `tests/unit/test_undo_stack.py` | UndoStack push/undo/redo/cap |
| Create: `tests/unit/test_mesh_validation.py` | validate_path edge cases |
| Create: `tests/unit/test_mesh_loading.py` | load_mesh success paths and parse failures |
| Create: `tests/fixtures/valid/cube.stl` | Generated: binary STL cube |
| Create: `tests/fixtures/valid/cube_ascii.stl` | Generated: ASCII STL cube |
| Create: `tests/fixtures/valid/cube.obj` | Generated: minimal OBJ cube |
| Create: `tests/fixtures/valid/cube.ply` | Generated: ASCII PLY cube |
| Create: `tests/fixtures/valid/cube.3mf` | Generated: minimal 3MF cube archive |
| Create: `tests/fixtures/valid/cube_with_materials.obj` | OBJ with mtllib/usemtl directives |
| Create: `tests/fixtures/invalid/corrupt.stl` | Truncated binary STL |
| Create: `tests/fixtures/invalid/zero_faces.stl` | Valid header, 0 triangles |
| Create: `tests/fixtures/invalid/bad_archive.3mf` | Not a valid ZIP |
| Create: `tests/fixtures/invalid/empty_file.ply` | 0 bytes |
| Create: `tests/fixtures/generate_test_meshes.py` | Script to regenerate all test fixtures |

---

### Task 1: Exception Hierarchy

**Files:**
- Create: `src/meshscope/core/exceptions.py`
- Create: `tests/unit/test_exceptions.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_exceptions.py
"""Tests for mesh loading exception hierarchy."""

from meshscope.core.exceptions import (
    CorruptFileError,
    EmptyMeshError,
    FileNotFoundError_,
    FileNotReadableError,
    FileTooLargeError,
    FileValidationError,
    MeshLoadError,
    MeshParseError,
    UnsupportedFormatError,
)


class TestExceptionHierarchy:
    def test_mesh_load_error_is_base(self) -> None:
        err = MeshLoadError("something broke")
        assert isinstance(err, Exception)
        assert err.user_message == "something broke"
        assert str(err) == "something broke"

    def test_file_validation_error_inherits_mesh_load_error(self) -> None:
        err = FileValidationError("validation failed")
        assert isinstance(err, MeshLoadError)
        assert err.user_message == "validation failed"

    def test_unsupported_format_error(self) -> None:
        err = UnsupportedFormatError(
            "Unsupported file format: .step. Supported formats: STL, OBJ, 3MF, PLY."
        )
        assert isinstance(err, FileValidationError)
        assert ".step" in err.user_message

    def test_file_too_large_error(self) -> None:
        err = FileTooLargeError(
            "File too large: 512MB. Maximum supported size: 500MB."
        )
        assert isinstance(err, FileValidationError)
        assert "512MB" in err.user_message

    def test_file_not_found_error(self) -> None:
        err = FileNotFoundError_("File not found: /tmp/missing.stl.")
        assert isinstance(err, FileValidationError)
        assert "/tmp/missing.stl" in err.user_message

    def test_file_not_readable_error(self) -> None:
        err = FileNotReadableError(
            "Cannot read file: /tmp/secret.stl. Permission denied."
        )
        assert isinstance(err, FileValidationError)
        assert "Permission denied" in err.user_message

    def test_mesh_parse_error_inherits_mesh_load_error(self) -> None:
        err = MeshParseError("parse failed")
        assert isinstance(err, MeshLoadError)

    def test_corrupt_file_error(self) -> None:
        err = CorruptFileError(
            "Invalid STL: unexpected EOF at byte 4096."
        )
        assert isinstance(err, MeshParseError)
        assert "EOF" in err.user_message

    def test_empty_mesh_error(self) -> None:
        err = EmptyMeshError(
            "File parsed successfully but contains no geometry (0 faces)."
        )
        assert isinstance(err, MeshParseError)
        assert "0 faces" in err.user_message
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_exceptions.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'meshscope.core.exceptions'`

- [ ] **Step 3: Write the implementation**

```python
# src/meshscope/core/exceptions.py
"""Custom exception hierarchy for mesh loading failures.

Each exception carries a user_message attribute containing
text suitable for direct display in error dialogs.
"""


class MeshLoadError(Exception):
    """Base exception for all mesh loading failures."""

    def __init__(self, user_message: str) -> None:
        self.user_message = user_message
        super().__init__(user_message)


# --- File validation errors ---


class FileValidationError(MeshLoadError):
    """File failed pre-parse validation (path, size, format)."""


class UnsupportedFormatError(FileValidationError):
    """File extension is not in the supported set."""


class FileTooLargeError(FileValidationError):
    """File exceeds the maximum supported size."""


class FileNotFoundError_(FileValidationError):
    """File does not exist at the given path."""


class FileNotReadableError(FileValidationError):
    """File exists but cannot be read (permission denied)."""


# --- Mesh parse errors ---


class MeshParseError(MeshLoadError):
    """File passed validation but could not be parsed into a mesh."""


class CorruptFileError(MeshParseError):
    """File is corrupt or contains invalid data for its format."""


class EmptyMeshError(MeshParseError):
    """File parsed successfully but contains no geometry."""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_exceptions.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/core/exceptions.py tests/unit/test_exceptions.py
git commit -m "feat: add mesh loading exception hierarchy with user messages"
```

---

### Task 2: BoundingBox and MeshMetadata Dataclasses

**Files:**
- Create: `src/meshscope/core/mesh_data.py`
- Create: `tests/unit/test_mesh_data.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_mesh_data.py
"""Tests for mesh data structures."""

import numpy as np

from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata


class TestBoundingBox:
    def test_construction(self) -> None:
        bb = BoundingBox(
            min_x=0.0, min_y=0.0, min_z=0.0,
            max_x=10.0, max_y=20.0, max_z=30.0,
        )
        assert bb.min_x == 0.0
        assert bb.max_z == 30.0

    def test_size_properties(self) -> None:
        bb = BoundingBox(
            min_x=-5.0, min_y=-10.0, min_z=-15.0,
            max_x=5.0, max_y=10.0, max_z=15.0,
        )
        assert bb.size_x == 10.0
        assert bb.size_y == 20.0
        assert bb.size_z == 30.0

    def test_center_property(self) -> None:
        bb = BoundingBox(
            min_x=0.0, min_y=0.0, min_z=0.0,
            max_x=10.0, max_y=20.0, max_z=30.0,
        )
        cx, cy, cz = bb.center
        assert cx == 5.0
        assert cy == 10.0
        assert cz == 15.0

    def test_is_frozen(self) -> None:
        bb = BoundingBox(
            min_x=0.0, min_y=0.0, min_z=0.0,
            max_x=1.0, max_y=1.0, max_z=1.0,
        )
        try:
            bb.min_x = 99.0  # type: ignore[misc]
            assert False, "Should have raised"
        except AttributeError:
            pass


class TestMeshMetadata:
    def test_construction(self) -> None:
        bb = BoundingBox(
            min_x=0.0, min_y=0.0, min_z=0.0,
            max_x=10.0, max_y=10.0, max_z=10.0,
        )
        meta = MeshMetadata(
            vertex_count=8,
            face_count=12,
            bounding_box=bb,
            surface_area_mm2=600.0,
            volume_mm3=1000.0,
            is_manifold=True,
        )
        assert meta.vertex_count == 8
        assert meta.face_count == 12
        assert meta.volume_mm3 == 1000.0
        assert meta.is_manifold is True

    def test_non_manifold_volume_is_none(self) -> None:
        bb = BoundingBox(
            min_x=0.0, min_y=0.0, min_z=0.0,
            max_x=1.0, max_y=1.0, max_z=1.0,
        )
        meta = MeshMetadata(
            vertex_count=4,
            face_count=2,
            bounding_box=bb,
            surface_area_mm2=1.0,
            volume_mm3=None,
            is_manifold=False,
        )
        assert meta.volume_mm3 is None
        assert meta.is_manifold is False


class TestMeshData:
    def test_construction(self) -> None:
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float32)
        faces = np.array([[0, 1, 2]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(
            min_x=0.0, min_y=0.0, min_z=0.0,
            max_x=1.0, max_y=1.0, max_z=0.0,
        )
        meta = MeshMetadata(
            vertex_count=3,
            face_count=1,
            bounding_box=bb,
            surface_area_mm2=0.5,
            volume_mm3=None,
            is_manifold=False,
        )
        mesh = MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)
        assert mesh.vertices.shape == (3, 3)
        assert mesh.faces.shape == (1, 3)
        assert mesh.normals.shape == (1, 3)
        assert mesh.metadata.vertex_count == 3

    def test_vertex_dtype_is_float32(self) -> None:
        vertices = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)
        assert mesh.vertices.dtype == np.float32

    def test_face_dtype_is_uint32(self) -> None:
        vertices = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)
        assert mesh.faces.dtype == np.uint32
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_mesh_data.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'meshscope.core.mesh_data'`

- [ ] **Step 3: Write the implementation**

```python
# src/meshscope/core/mesh_data.py
"""Immutable data structures for mesh geometry and metadata."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BoundingBox:
    """Axis-aligned bounding box in mm."""

    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    @property
    def size_x(self) -> float:
        return self.max_x - self.min_x

    @property
    def size_y(self) -> float:
        return self.max_y - self.min_y

    @property
    def size_z(self) -> float:
        return self.max_z - self.min_z

    @property
    def center(self) -> tuple[float, float, float]:
        return (
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2,
            (self.min_z + self.max_z) / 2,
        )


@dataclass(frozen=True)
class MeshMetadata:
    """Computed mesh properties."""

    vertex_count: int
    face_count: int
    bounding_box: BoundingBox
    surface_area_mm2: float
    volume_mm3: float | None  # None if non-manifold
    is_manifold: bool


@dataclass(frozen=True)
class MeshData:
    """Immutable mesh geometry with computed metadata.

    vertices: float32, shape (N, 3) — positions in mm
    faces: uint32, shape (M, 3) — triangle vertex indices (0-based)
    normals: float32, shape (M, 3) — per-face unit normals
    """

    vertices: np.ndarray
    faces: np.ndarray
    normals: np.ndarray
    metadata: MeshMetadata
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_mesh_data.py -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/core/mesh_data.py tests/unit/test_mesh_data.py
git commit -m "feat: add BoundingBox, MeshMetadata, and MeshData dataclasses"
```

---

### Task 3: UndoStack

**Files:**
- Create: `src/meshscope/core/undo_stack.py`
- Create: `tests/unit/test_undo_stack.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_undo_stack.py
"""Tests for UndoStack."""

import numpy as np

from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.core.undo_stack import UndoStack


def _make_mesh(vertex_val: float = 0.0) -> MeshData:
    """Create a minimal MeshData for testing."""
    vertices = np.array([[vertex_val, 0, 0]], dtype=np.float32)
    faces = np.array([[0, 0, 0]], dtype=np.uint32)
    normals = np.array([[0, 0, 1]], dtype=np.float32)
    bb = BoundingBox(0, 0, 0, vertex_val, 0, 0)
    meta = MeshMetadata(1, 1, bb, 0.0, None, False)
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


class TestUndoStack:
    def test_empty_stack(self) -> None:
        stack = UndoStack(max_entries=10)
        assert stack.can_undo() is False
        assert stack.can_redo() is False
        assert stack.undo() is None
        assert stack.redo() is None

    def test_push_and_undo(self) -> None:
        stack = UndoStack(max_entries=10)
        mesh_v1 = _make_mesh(1.0)
        stack.push(mesh_v1)
        assert stack.can_undo() is True
        result = stack.undo()
        assert result is mesh_v1
        assert stack.can_undo() is False

    def test_undo_and_redo(self) -> None:
        stack = UndoStack(max_entries=10)
        mesh_v1 = _make_mesh(1.0)
        mesh_v2 = _make_mesh(2.0)
        stack.push(mesh_v1)
        stack.push(mesh_v2)
        assert stack.undo() is mesh_v2
        assert stack.can_redo() is True
        assert stack.redo() is mesh_v2

    def test_push_clears_redo_history(self) -> None:
        stack = UndoStack(max_entries=10)
        stack.push(_make_mesh(1.0))
        stack.push(_make_mesh(2.0))
        stack.undo()
        stack.push(_make_mesh(3.0))
        assert stack.can_redo() is False

    def test_max_entries_evicts_oldest(self) -> None:
        stack = UndoStack(max_entries=3)
        stack.push(_make_mesh(1.0))
        stack.push(_make_mesh(2.0))
        stack.push(_make_mesh(3.0))
        stack.push(_make_mesh(4.0))  # evicts mesh 1.0
        results = []
        while stack.can_undo():
            results.append(stack.undo())
        assert len(results) == 3
        assert results[0].vertices[0][0] == 4.0
        assert results[2].vertices[0][0] == 2.0  # mesh 1.0 was evicted

    def test_memory_bytes_tracks_usage(self) -> None:
        stack = UndoStack(max_entries=10)
        assert stack.memory_bytes == 0
        stack.push(_make_mesh(1.0))
        assert stack.memory_bytes > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_undo_stack.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'meshscope.core.undo_stack'`

- [ ] **Step 3: Write the implementation**

```python
# src/meshscope/core/undo_stack.py
"""Undo/redo stack for mesh state snapshots."""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from meshscope.core.mesh_data import MeshData


class UndoStack:
    """Ring buffer of MeshData snapshots supporting undo/redo.

    When max_entries is reached, the oldest entry is evicted.
    Pushing a new entry after an undo clears the redo history.
    """

    def __init__(self, max_entries: int = 10) -> None:
        self._entries: deque[MeshData] = deque(maxlen=max_entries)
        self._redo_stack: list[MeshData] = []
        self._max_entries = max_entries

    def push(self, mesh: MeshData) -> None:
        """Save a mesh state snapshot. Clears redo history."""
        self._entries.append(mesh)
        self._redo_stack.clear()

    def undo(self) -> MeshData | None:
        """Pop the most recent snapshot, moving it to redo stack."""
        if not self._entries:
            return None
        mesh = self._entries.pop()
        self._redo_stack.append(mesh)
        return mesh

    def redo(self) -> MeshData | None:
        """Restore the most recently undone snapshot."""
        if not self._redo_stack:
            return None
        mesh = self._redo_stack.pop()
        self._entries.append(mesh)
        return mesh

    def can_undo(self) -> bool:
        return len(self._entries) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    @property
    def memory_bytes(self) -> int:
        """Estimate total memory used by stored snapshots."""
        total = 0
        for mesh in self._entries:
            total += mesh.vertices.nbytes + mesh.faces.nbytes + mesh.normals.nbytes
        for mesh in self._redo_stack:
            total += mesh.vertices.nbytes + mesh.faces.nbytes + mesh.normals.nbytes
        return total
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_undo_stack.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/core/undo_stack.py tests/unit/test_undo_stack.py
git commit -m "feat: add UndoStack with max entries and redo support"
```

---

### Task 4: MeshDocument

**Files:**
- Create: `src/meshscope/core/mesh_document.py`
- Modify: `tests/unit/test_mesh_data.py` (add MeshDocument tests to a new file instead)
- Create: `tests/unit/test_mesh_document.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_mesh_document.py
"""Tests for MeshDocument."""

import copy

import numpy as np

from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.core.mesh_document import MeshDocument


def _make_mesh() -> MeshData:
    vertices = np.array(
        [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.float32
    )
    faces = np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]], dtype=np.uint32)
    normals = np.array(
        [[0, 0, -1], [0, -1, 0], [-1, 0, 0], [0.57, 0.57, 0.57]], dtype=np.float32
    )
    bb = BoundingBox(0, 0, 0, 1, 1, 1)
    meta = MeshMetadata(4, 4, bb, 3.46, 0.167, True)
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


class TestMeshDocument:
    def test_construction(self) -> None:
        mesh = _make_mesh()
        doc = MeshDocument(
            mesh=mesh,
            source_path="/tmp/test.stl",
            source_format="stl_binary",
            source_size_bytes=1234,
        )
        assert doc.mesh is mesh
        assert doc.source_path == "/tmp/test.stl"
        assert doc.source_format == "stl_binary"
        assert doc.source_size_bytes == 1234
        assert doc.warnings == []

    def test_original_mesh_is_independent_copy(self) -> None:
        mesh = _make_mesh()
        doc = MeshDocument(
            mesh=mesh,
            source_path="/tmp/test.stl",
            source_format="stl_binary",
            source_size_bytes=1234,
        )
        assert doc.original_mesh is not doc.mesh
        assert np.array_equal(doc.original_mesh.vertices, doc.mesh.vertices)

    def test_warnings_stored(self) -> None:
        mesh = _make_mesh()
        doc = MeshDocument(
            mesh=mesh,
            source_path="/tmp/test.obj",
            source_format="obj",
            source_size_bytes=500,
            warnings=["This OBJ file contains materials which are not supported."],
        )
        assert len(doc.warnings) == 1
        assert "materials" in doc.warnings[0]

    def test_undo_stack_exists_and_empty(self) -> None:
        mesh = _make_mesh()
        doc = MeshDocument(
            mesh=mesh,
            source_path="/tmp/test.stl",
            source_format="stl_binary",
            source_size_bytes=1234,
        )
        assert doc.undo_stack.can_undo() is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_mesh_document.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'meshscope.core.mesh_document'`

- [ ] **Step 3: Write the implementation**

```python
# src/meshscope/core/mesh_document.py
"""Mutable session wrapper for a loaded mesh."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from meshscope.core.undo_stack import UndoStack

if TYPE_CHECKING:
    from meshscope.core.mesh_data import MeshData


class MeshDocument:
    """Represents a loaded mesh file with session state.

    Holds the current mesh, an immutable copy of the original,
    an undo stack, source file info, and user-visible warnings.
    """

    def __init__(
        self,
        mesh: MeshData,
        source_path: str,
        source_format: str,
        source_size_bytes: int,
        warnings: list[str] | None = None,
    ) -> None:
        self.mesh = mesh
        self.original_mesh = copy.deepcopy(mesh)
        self.source_path = source_path
        self.source_format = source_format
        self.source_size_bytes = source_size_bytes
        self.undo_stack = UndoStack()
        self.warnings: list[str] = warnings if warnings is not None else []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_mesh_document.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/core/mesh_document.py tests/unit/test_mesh_document.py
git commit -m "feat: add MeshDocument session wrapper"
```

---

### Task 5: Test Fixture Generation

**Files:**
- Create: `tests/fixtures/generate_test_meshes.py`
- Create: `tests/fixtures/valid/` mesh files
- Create: `tests/fixtures/invalid/` mesh files

- [ ] **Step 1: Write the fixture generator script**

```python
# tests/fixtures/generate_test_meshes.py
"""Generate test mesh fixtures for all supported formats.

Run: python tests/fixtures/generate_test_meshes.py
"""

import struct
import zipfile
from pathlib import Path

VALID_DIR = Path(__file__).parent / "valid"
INVALID_DIR = Path(__file__).parent / "invalid"


def generate_cube_stl_binary(path: Path) -> None:
    """Write a binary STL cube (8 vertices, 12 triangles)."""
    # Cube vertices
    v = [
        (0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0),
        (0, 0, 10), (10, 0, 10), (10, 10, 10), (0, 10, 10),
    ]
    # 12 triangles (2 per face)
    triangles = [
        # Bottom (z=0)
        ((0, 0, -1), v[0], v[2], v[1]),
        ((0, 0, -1), v[0], v[3], v[2]),
        # Top (z=10)
        ((0, 0, 1), v[4], v[5], v[6]),
        ((0, 0, 1), v[4], v[6], v[7]),
        # Front (y=0)
        ((0, -1, 0), v[0], v[1], v[5]),
        ((0, -1, 0), v[0], v[5], v[4]),
        # Back (y=10)
        ((0, 1, 0), v[2], v[3], v[7]),
        ((0, 1, 0), v[2], v[7], v[6]),
        # Left (x=0)
        ((-1, 0, 0), v[0], v[4], v[7]),
        ((-1, 0, 0), v[0], v[7], v[3]),
        # Right (x=10)
        ((1, 0, 0), v[1], v[2], v[6]),
        ((1, 0, 0), v[1], v[6], v[5]),
    ]
    with open(path, "wb") as f:
        f.write(b"\x00" * 80)  # header
        f.write(struct.pack("<I", len(triangles)))
        for normal, v0, v1, v2 in triangles:
            for coord in normal:
                f.write(struct.pack("<f", coord))
            for vert in (v0, v1, v2):
                for coord in vert:
                    f.write(struct.pack("<f", float(coord)))
            f.write(struct.pack("<H", 0))  # attribute byte count


def generate_cube_stl_ascii(path: Path) -> None:
    """Write an ASCII STL cube."""
    v = [
        (0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0),
        (0, 0, 10), (10, 0, 10), (10, 10, 10), (0, 10, 10),
    ]
    triangles = [
        ((0, 0, -1), v[0], v[2], v[1]),
        ((0, 0, -1), v[0], v[3], v[2]),
        ((0, 0, 1), v[4], v[5], v[6]),
        ((0, 0, 1), v[4], v[6], v[7]),
        ((0, -1, 0), v[0], v[1], v[5]),
        ((0, -1, 0), v[0], v[5], v[4]),
        ((0, 1, 0), v[2], v[3], v[7]),
        ((0, 1, 0), v[2], v[7], v[6]),
        ((-1, 0, 0), v[0], v[4], v[7]),
        ((-1, 0, 0), v[0], v[7], v[3]),
        ((1, 0, 0), v[1], v[2], v[6]),
        ((1, 0, 0), v[1], v[6], v[5]),
    ]
    lines = ["solid cube"]
    for normal, v0, v1, v2 in triangles:
        lines.append(f"  facet normal {normal[0]} {normal[1]} {normal[2]}")
        lines.append("    outer loop")
        for vert in (v0, v1, v2):
            lines.append(f"      vertex {vert[0]} {vert[1]} {vert[2]}")
        lines.append("    endloop")
        lines.append("  endfacet")
    lines.append("endsolid cube")
    path.write_text("\n".join(lines) + "\n")


def generate_cube_obj(path: Path) -> None:
    """Write a minimal OBJ cube."""
    lines = [
        "# Cube",
        "v 0 0 0", "v 10 0 0", "v 10 10 0", "v 0 10 0",
        "v 0 0 10", "v 10 0 10", "v 10 10 10", "v 0 10 10",
        "f 1 3 2", "f 1 4 3",
        "f 5 6 7", "f 5 7 8",
        "f 1 2 6", "f 1 6 5",
        "f 3 4 8", "f 3 8 7",
        "f 1 5 8", "f 1 8 4",
        "f 2 3 7", "f 2 7 6",
    ]
    path.write_text("\n".join(lines) + "\n")


def generate_cube_obj_with_materials(path: Path) -> None:
    """Write an OBJ cube with unsupported material directives."""
    lines = [
        "# Cube with materials",
        "mtllib cube.mtl",
        "usemtl default",
        "v 0 0 0", "v 10 0 0", "v 10 10 0", "v 0 10 0",
        "v 0 0 10", "v 10 0 10", "v 10 10 10", "v 0 10 10",
        "vt 0 0", "vt 1 0", "vt 1 1", "vt 0 1",
        "g cube_group",
        "s 1",
        "f 1 3 2", "f 1 4 3",
        "f 5 6 7", "f 5 7 8",
        "f 1 2 6", "f 1 6 5",
        "f 3 4 8", "f 3 8 7",
        "f 1 5 8", "f 1 8 4",
        "f 2 3 7", "f 2 7 6",
    ]
    path.write_text("\n".join(lines) + "\n")


def generate_cube_ply(path: Path) -> None:
    """Write an ASCII PLY cube."""
    vertices = [
        "0 0 0", "10 0 0", "10 10 0", "0 10 0",
        "0 0 10", "10 0 10", "10 10 10", "0 10 10",
    ]
    faces = [
        "3 0 2 1", "3 0 3 2",
        "3 4 5 6", "3 4 6 7",
        "3 0 1 5", "3 0 5 4",
        "3 2 3 7", "3 2 7 6",
        "3 0 4 7", "3 0 7 3",
        "3 1 2 6", "3 1 6 5",
    ]
    header = [
        "ply",
        "format ascii 1.0",
        f"element vertex {len(vertices)}",
        "property float x",
        "property float y",
        "property float z",
        f"element face {len(faces)}",
        "property list uchar int vertex_indices",
        "end_header",
    ]
    path.write_text("\n".join(header + vertices + faces) + "\n")


def generate_cube_3mf(path: Path) -> None:
    """Write a minimal valid 3MF archive."""
    model_xml = """<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources>
    <object id="1" type="model">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0" />
          <vertex x="10" y="0" z="0" />
          <vertex x="10" y="10" z="0" />
          <vertex x="0" y="10" z="0" />
          <vertex x="0" y="0" z="10" />
          <vertex x="10" y="0" z="10" />
          <vertex x="10" y="10" z="10" />
          <vertex x="0" y="10" z="10" />
        </vertices>
        <triangles>
          <triangle v1="0" v2="2" v3="1" />
          <triangle v1="0" v2="3" v3="2" />
          <triangle v1="4" v2="5" v3="6" />
          <triangle v1="4" v2="6" v3="7" />
          <triangle v1="0" v2="1" v3="5" />
          <triangle v1="0" v2="5" v3="4" />
          <triangle v1="2" v2="3" v3="7" />
          <triangle v1="2" v2="7" v3="6" />
          <triangle v1="0" v2="4" v3="7" />
          <triangle v1="0" v2="7" v3="3" />
          <triangle v1="1" v2="2" v3="6" />
          <triangle v1="1" v2="6" v3="5" />
        </triangles>
      </mesh>
    </object>
  </resources>
  <build>
    <item objectid="1" />
  </build>
</model>"""
    content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml" />
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" />
</Relationships>"""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("3D/3dmodel.model", model_xml)


def generate_invalid_fixtures() -> None:
    """Generate broken files for error testing."""
    # Truncated binary STL
    corrupt_stl = INVALID_DIR / "corrupt.stl"
    with open(corrupt_stl, "wb") as f:
        f.write(b"\x00" * 80)  # header
        f.write(struct.pack("<I", 100))  # says 100 triangles
        f.write(b"\x00" * 20)  # only partial data

    # Valid header, 0 triangles
    zero_stl = INVALID_DIR / "zero_faces.stl"
    with open(zero_stl, "wb") as f:
        f.write(b"\x00" * 80)
        f.write(struct.pack("<I", 0))

    # Not a valid ZIP
    bad_3mf = INVALID_DIR / "bad_archive.3mf"
    bad_3mf.write_text("this is not a zip file")

    # Empty file
    empty_ply = INVALID_DIR / "empty_file.ply"
    empty_ply.write_bytes(b"")


if __name__ == "__main__":
    VALID_DIR.mkdir(parents=True, exist_ok=True)
    INVALID_DIR.mkdir(parents=True, exist_ok=True)

    generate_cube_stl_binary(VALID_DIR / "cube.stl")
    generate_cube_stl_ascii(VALID_DIR / "cube_ascii.stl")
    generate_cube_obj(VALID_DIR / "cube.obj")
    generate_cube_obj_with_materials(VALID_DIR / "cube_with_materials.obj")
    generate_cube_ply(VALID_DIR / "cube.ply")
    generate_cube_3mf(VALID_DIR / "cube.3mf")
    generate_invalid_fixtures()

    print("Generated test fixtures:")
    for d in (VALID_DIR, INVALID_DIR):
        for f in sorted(d.iterdir()):
            print(f"  {f.relative_to(Path(__file__).parent)} ({f.stat().st_size} bytes)")
```

- [ ] **Step 2: Run the generator**

Run: `python tests/fixtures/generate_test_meshes.py`
Expected: prints list of generated files with sizes

- [ ] **Step 3: Verify fixtures load with trimesh**

Run:
```bash
python -c "
import trimesh
for fmt, path in [('stl', 'tests/fixtures/valid/cube.stl'),
                  ('stl', 'tests/fixtures/valid/cube_ascii.stl'),
                  ('obj', 'tests/fixtures/valid/cube.obj'),
                  ('ply', 'tests/fixtures/valid/cube.ply'),
                  ('3mf', 'tests/fixtures/valid/cube.3mf')]:
    m = trimesh.load(path, file_type=fmt)
    if hasattr(m, 'vertices'):
        print(f'{path}: {len(m.vertices)} verts, {len(m.faces)} faces')
    else:
        print(f'{path}: Scene with {len(m.geometry)} meshes')
"
```
Expected: Each file reports 8 vertices and 12 faces (or Scene for 3MF)

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/
git commit -m "feat: add test mesh fixtures for all supported formats"
```

---

### Task 6: Path Validation

**Files:**
- Create: `src/meshscope/core/mesh_loader.py` (partial — validate_path and detect_format only)
- Create: `tests/unit/test_mesh_validation.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_mesh_validation.py
"""Tests for file path validation and format detection."""

from pathlib import Path
from unittest.mock import patch

import pytest

from meshscope.core.exceptions import (
    FileNotFoundError_,
    FileNotReadableError,
    FileTooLargeError,
    UnsupportedFormatError,
)
from meshscope.core.mesh_loader import detect_format, validate_path


class TestValidatePath:
    def test_valid_stl_file(self, tmp_path: Path) -> None:
        f = tmp_path / "model.stl"
        f.write_bytes(b"\x00" * 100)
        validate_path(f)  # should not raise

    def test_unsupported_extension(self, tmp_path: Path) -> None:
        f = tmp_path / "model.step"
        f.write_bytes(b"\x00" * 100)
        with pytest.raises(UnsupportedFormatError, match=r"\.step"):
            validate_path(f)

    def test_case_insensitive_extension(self, tmp_path: Path) -> None:
        f = tmp_path / "model.STL"
        f.write_bytes(b"\x00" * 100)
        validate_path(f)  # should not raise

    def test_file_not_found(self, tmp_path: Path) -> None:
        f = tmp_path / "missing.stl"
        with pytest.raises(FileNotFoundError_, match="not found"):
            validate_path(f)

    def test_path_is_directory(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError_, match="not found"):
            validate_path(tmp_path)

    def test_file_too_large(self, tmp_path: Path) -> None:
        f = tmp_path / "huge.stl"
        f.write_bytes(b"\x00" * 100)
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 501 * 1024 * 1024
            with pytest.raises(FileTooLargeError, match="500MB"):
                validate_path(f)

    def test_file_not_readable(self, tmp_path: Path) -> None:
        f = tmp_path / "secret.stl"
        f.write_bytes(b"\x00" * 100)
        f.chmod(0o000)
        try:
            with pytest.raises(FileNotReadableError, match="Permission denied"):
                validate_path(f)
        finally:
            f.chmod(0o644)


class TestDetectFormat:
    def test_stl(self) -> None:
        assert detect_format(Path("model.stl")) == "stl"

    def test_obj(self) -> None:
        assert detect_format(Path("model.obj")) == "obj"

    def test_3mf(self) -> None:
        assert detect_format(Path("model.3mf")) == "3mf"

    def test_ply(self) -> None:
        assert detect_format(Path("model.ply")) == "ply"

    def test_case_insensitive(self) -> None:
        assert detect_format(Path("MODEL.STL")) == "stl"
        assert detect_format(Path("file.OBJ")) == "obj"

    def test_unsupported_raises(self) -> None:
        with pytest.raises(UnsupportedFormatError):
            detect_format(Path("model.step"))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_mesh_validation.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'meshscope.core.mesh_loader'`

- [ ] **Step 3: Write the implementation**

```python
# src/meshscope/core/mesh_loader.py
"""Mesh file loading: validation, parsing, and MeshDocument construction."""

from __future__ import annotations

import os
from pathlib import Path

from meshscope.core.exceptions import (
    FileNotFoundError_,
    FileNotReadableError,
    FileTooLargeError,
    UnsupportedFormatError,
)

SUPPORTED_FORMATS: dict[str, str] = {
    ".stl": "stl",
    ".obj": "obj",
    ".3mf": "3mf",
    ".ply": "ply",
}

MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500MB


def detect_format(path: Path) -> str:
    """Detect mesh format from file extension.

    Returns the trimesh file_type string.
    Raises UnsupportedFormatError if extension is not supported.
    """
    ext = path.suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        raise UnsupportedFormatError(
            f"Unsupported file format: {ext}. "
            "Supported formats: STL, OBJ, 3MF, PLY."
        )
    return SUPPORTED_FORMATS[ext]


def validate_path(path: Path) -> None:
    """Validate that the file exists, is readable, has a supported
    extension, and is within the size limit.

    Raises FileValidationError subclasses on failure.
    """
    path = Path(path)

    # Check extension first (cheapest check)
    detect_format(path)

    # Check existence
    if not path.is_file():
        raise FileNotFoundError_(f"File not found: {path}.")

    # Check readable
    if not os.access(path, os.R_OK):
        raise FileNotReadableError(
            f"Cannot read file: {path}. Permission denied."
        )

    # Check size
    size_bytes = path.stat().st_size
    if size_bytes > MAX_FILE_SIZE_BYTES:
        size_mb = size_bytes // (1024 * 1024)
        raise FileTooLargeError(
            f"File too large: {size_mb}MB. Maximum supported size: 500MB."
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_mesh_validation.py -v`
Expected: 13 passed

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/core/mesh_loader.py tests/unit/test_mesh_validation.py
git commit -m "feat: add path validation and format detection"
```

---

### Task 7: Mesh Loading (load_mesh)

**Files:**
- Modify: `src/meshscope/core/mesh_loader.py` (add parse_mesh, load_mesh, OBJ warning detection, unit mismatch)
- Create: `tests/unit/test_mesh_loading.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/test_mesh_loading.py
"""Tests for load_mesh — full loading pipeline."""

from pathlib import Path

import numpy as np
import pytest

from meshscope.core.exceptions import CorruptFileError, EmptyMeshError
from meshscope.core.mesh_document import MeshDocument
from meshscope.core.mesh_loader import load_mesh

FIXTURES = Path(__file__).parent.parent / "fixtures"
VALID = FIXTURES / "valid"
INVALID = FIXTURES / "invalid"


class TestLoadMeshSuccess:
    def test_load_stl_binary(self) -> None:
        doc = load_mesh(VALID / "cube.stl")
        assert isinstance(doc, MeshDocument)
        assert doc.mesh.metadata.face_count == 12
        assert doc.mesh.metadata.vertex_count == 8
        assert doc.mesh.vertices.dtype == np.float32
        assert doc.mesh.faces.dtype == np.uint32
        assert doc.source_format == "stl"

    def test_load_stl_ascii(self) -> None:
        doc = load_mesh(VALID / "cube_ascii.stl")
        assert doc.mesh.metadata.face_count == 12
        assert doc.source_format == "stl"

    def test_load_obj(self) -> None:
        doc = load_mesh(VALID / "cube.obj")
        assert doc.mesh.metadata.face_count == 12
        assert doc.mesh.metadata.vertex_count == 8
        assert doc.source_format == "obj"

    def test_load_ply(self) -> None:
        doc = load_mesh(VALID / "cube.ply")
        assert doc.mesh.metadata.face_count == 12
        assert doc.source_format == "ply"

    def test_load_3mf(self) -> None:
        doc = load_mesh(VALID / "cube.3mf")
        assert doc.mesh.metadata.face_count == 12
        assert doc.source_format == "3mf"

    def test_bounding_box_correct(self) -> None:
        doc = load_mesh(VALID / "cube.stl")
        bb = doc.mesh.metadata.bounding_box
        assert bb.size_x == pytest.approx(10.0, abs=0.01)
        assert bb.size_y == pytest.approx(10.0, abs=0.01)
        assert bb.size_z == pytest.approx(10.0, abs=0.01)

    def test_surface_area_computed(self) -> None:
        doc = load_mesh(VALID / "cube.stl")
        # Cube 10x10x10: surface area = 6 * 100 = 600
        assert doc.mesh.metadata.surface_area_mm2 == pytest.approx(600.0, rel=0.01)

    def test_volume_computed_for_manifold(self) -> None:
        doc = load_mesh(VALID / "cube.stl")
        # Cube 10x10x10: volume = 1000
        assert doc.mesh.metadata.volume_mm3 is not None
        assert doc.mesh.metadata.volume_mm3 == pytest.approx(1000.0, rel=0.01)

    def test_manifold_status(self) -> None:
        doc = load_mesh(VALID / "cube.stl")
        assert doc.mesh.metadata.is_manifold is True

    def test_normals_shape_matches_faces(self) -> None:
        doc = load_mesh(VALID / "cube.stl")
        assert doc.mesh.normals.shape == (doc.mesh.metadata.face_count, 3)

    def test_original_mesh_preserved(self) -> None:
        doc = load_mesh(VALID / "cube.stl")
        assert np.array_equal(doc.original_mesh.vertices, doc.mesh.vertices)
        assert doc.original_mesh is not doc.mesh


class TestLoadMeshWarnings:
    def test_obj_with_materials_produces_warning(self) -> None:
        doc = load_mesh(VALID / "cube_with_materials.obj")
        assert len(doc.warnings) >= 1
        warning_text = " ".join(doc.warnings)
        assert "not supported" in warning_text.lower()

    def test_unit_mismatch_tiny_mesh(self, tmp_path: Path) -> None:
        """Mesh with all dimensions < 1mm triggers unit mismatch warning."""
        # Create a tiny OBJ (all coords < 1mm, likely inches not mm)
        tiny_obj = tmp_path / "tiny.obj"
        tiny_obj.write_text(
            "v 0 0 0\nv 0.5 0 0\nv 0.5 0.5 0\nv 0 0.5 0\n"
            "f 1 2 3\nf 1 3 4\n"
        )
        doc = load_mesh(tiny_obj)
        warning_text = " ".join(doc.warnings)
        assert "unit mismatch" in warning_text.lower()

    def test_unit_mismatch_huge_mesh(self, tmp_path: Path) -> None:
        """Mesh with any dimension > 10,000mm triggers unit mismatch warning."""
        huge_obj = tmp_path / "huge.obj"
        huge_obj.write_text(
            "v 0 0 0\nv 20000 0 0\nv 20000 20000 0\nv 0 20000 0\n"
            "f 1 2 3\nf 1 3 4\n"
        )
        doc = load_mesh(huge_obj)
        warning_text = " ".join(doc.warnings)
        assert "unit mismatch" in warning_text.lower()

    def test_no_warning_for_normal_mesh(self) -> None:
        doc = load_mesh(VALID / "cube.stl")
        warning_text = " ".join(doc.warnings)
        assert "unit mismatch" not in warning_text.lower()


class TestLoadMeshErrors:
    def test_corrupt_stl(self) -> None:
        with pytest.raises(CorruptFileError):
            load_mesh(INVALID / "corrupt.stl")

    def test_zero_faces_stl(self) -> None:
        with pytest.raises(EmptyMeshError, match="0 faces"):
            load_mesh(INVALID / "zero_faces.stl")

    def test_bad_3mf_archive(self) -> None:
        with pytest.raises(CorruptFileError):
            load_mesh(INVALID / "bad_archive.3mf")

    def test_empty_ply(self) -> None:
        with pytest.raises((CorruptFileError, EmptyMeshError)):
            load_mesh(INVALID / "empty_file.ply")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_mesh_loading.py -v`
Expected: FAIL with `ImportError: cannot import name 'load_mesh' from 'meshscope.core.mesh_loader'`

- [ ] **Step 3: Write the implementation**

Add to `src/meshscope/core/mesh_loader.py` (after the existing `validate_path` and `detect_format`):

```python
# Add these imports at the top of mesh_loader.py
import copy
import logging
import zipfile

import numpy as np
import trimesh

from meshscope.core.exceptions import (
    CorruptFileError,
    EmptyMeshError,
    FileNotFoundError_,
    FileNotReadableError,
    FileTooLargeError,
    UnsupportedFormatError,
)
from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.core.mesh_document import MeshDocument

logger = logging.getLogger("meshscope.core.mesh_loader")

# ... existing validate_path and detect_format ...

OBJ_UNSUPPORTED_DIRECTIVES = {
    "mtllib": "materials",
    "usemtl": "materials",
    "vt": "texture coordinates",
    "g": "groups",
    "s": "smooth shading",
    "cstype": "curves",
    "curv": "curves",
    "surf": "surfaces",
}


def _detect_obj_warnings(path: Path) -> list[str]:
    """Scan an OBJ file for unsupported directives."""
    found: set[str] = set()
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                directive = line.strip().split()[0] if line.strip() else ""
                if directive in OBJ_UNSUPPORTED_DIRECTIVES:
                    found.add(OBJ_UNSUPPORTED_DIRECTIVES[directive])
    except OSError:
        pass  # File reading issues handled elsewhere
    if found:
        items = ", ".join(sorted(found))
        return [
            f"This OBJ file contains {items} which are not supported. "
            "These will be ignored."
        ]
    return []


def _check_unit_mismatch(metadata: MeshMetadata) -> str | None:
    """Return a warning string if dimensions suggest a unit mismatch."""
    bb = metadata.bounding_box
    all_tiny = bb.size_x < 1.0 and bb.size_y < 1.0 and bb.size_z < 1.0
    any_huge = bb.size_x > 10000 or bb.size_y > 10000 or bb.size_z > 10000

    if metadata.face_count == 0:
        return None
    if all_tiny:
        return (
            "Dimensions may indicate a unit mismatch. "
            "Consider scaling by 25.4 (inches to mm) or 0.0394 (mm to inches)."
        )
    if any_huge:
        return (
            "Dimensions may indicate a unit mismatch. "
            "Consider scaling by 25.4 (inches to mm) or 0.0394 (mm to inches)."
        )
    return None


def _trimesh_to_mesh_data(tm_mesh: trimesh.Trimesh) -> MeshData:
    """Convert a trimesh.Trimesh to our MeshData."""
    vertices = np.asarray(tm_mesh.vertices, dtype=np.float32)
    faces = np.asarray(tm_mesh.faces, dtype=np.uint32)
    normals = np.asarray(tm_mesh.face_normals, dtype=np.float32)

    bounds = tm_mesh.bounds  # [[min_x, min_y, min_z], [max_x, max_y, max_z]]
    bounding_box = BoundingBox(
        min_x=float(bounds[0][0]),
        min_y=float(bounds[0][1]),
        min_z=float(bounds[0][2]),
        max_x=float(bounds[1][0]),
        max_y=float(bounds[1][1]),
        max_z=float(bounds[1][2]),
    )

    is_manifold = bool(tm_mesh.is_volume)
    volume = float(tm_mesh.volume) if is_manifold else None

    metadata = MeshMetadata(
        vertex_count=len(vertices),
        face_count=len(faces),
        bounding_box=bounding_box,
        surface_area_mm2=float(tm_mesh.area),
        volume_mm3=volume,
        is_manifold=is_manifold,
    )

    return MeshData(
        vertices=vertices,
        faces=faces,
        normals=normals,
        metadata=metadata,
    )


def load_mesh(path: str | Path) -> MeshDocument:
    """Load a mesh file and return a MeshDocument.

    Validates the path, parses via trimesh, computes metadata,
    and checks for warnings (OBJ directives, unit mismatch).

    Raises MeshLoadError subclasses on failure.
    """
    path = Path(path)
    validate_path(path)
    file_type = detect_format(path)
    source_size = path.stat().st_size
    warnings: list[str] = []

    # OBJ directive scan (before parsing)
    if file_type == "obj":
        warnings.extend(_detect_obj_warnings(path))

    # Parse with trimesh
    try:
        result = trimesh.load(str(path), file_type=file_type)
    except zipfile.BadZipFile:
        raise CorruptFileError(
            f"Invalid 3MF: unable to extract archive. File may be corrupt."
        )
    except Exception as e:
        raise CorruptFileError(f"Invalid {file_type.upper()}: {e}")

    # Handle Scene (3MF may return multiple meshes)
    if isinstance(result, trimesh.Scene):
        geometries = list(result.geometry.values())
        if not geometries:
            raise EmptyMeshError(
                "File parsed successfully but contains no geometry (0 faces)."
            )
        if len(geometries) > 1:
            warnings.append(
                f"This 3MF file contains {len(geometries)} meshes. "
                "Only the first was loaded."
            )
        result = geometries[0]

    # Validate we have a proper mesh
    if not isinstance(result, trimesh.Trimesh):
        raise CorruptFileError(
            f"Invalid {file_type.upper()}: file did not produce a valid mesh."
        )

    if len(result.faces) == 0:
        raise EmptyMeshError(
            "File parsed successfully but contains no geometry (0 faces)."
        )

    # Convert to our data model
    mesh_data = _trimesh_to_mesh_data(result)

    # Check unit mismatch
    unit_warning = _check_unit_mismatch(mesh_data.metadata)
    if unit_warning:
        warnings.append(unit_warning)

    logger.info(
        "Loaded mesh: %s (%s, %d vertices, %d faces)",
        path.name,
        file_type,
        mesh_data.metadata.vertex_count,
        mesh_data.metadata.face_count,
    )

    return MeshDocument(
        mesh=mesh_data,
        source_path=str(path),
        source_format=file_type,
        source_size_bytes=source_size,
        warnings=warnings,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_mesh_loading.py -v`
Expected: 19 passed (some may need adjustment based on trimesh's exact behavior with the fixtures)

- [ ] **Step 5: Run the full test suite**

Run: `pytest tests/ -v`
Expected: All tests pass (exceptions + mesh_data + undo_stack + mesh_document + validation + loading)

- [ ] **Step 6: Run linting and type checking**

Run: `ruff check src/ tests/ && mypy src/meshscope/`
Expected: Clean

- [ ] **Step 7: Commit**

```bash
git add src/meshscope/core/mesh_loader.py tests/unit/test_mesh_loading.py
git commit -m "feat: implement load_mesh with format parsing, warnings, and error handling"
```

---

## Self-Review

**1. Spec coverage:**
- Exception hierarchy: Task 1
- BoundingBox, MeshMetadata, MeshData: Task 2
- UndoStack: Task 3
- MeshDocument: Task 4
- Test fixtures for all 4 formats: Task 5
- Path validation and format detection: Task 6
- Full load_mesh pipeline (parse, warnings, unit mismatch, errors): Task 7
- OBJ unsupported directive warning: Task 7
- 3MF multi-mesh handling: Task 7
- Unit mismatch detection: Task 7
- All FRD failure states covered in test cases: Tasks 6-7

**2. Placeholder scan:** No TBDs, TODOs, or vague instructions. All code blocks are complete.

**3. Type consistency:**
- `MeshData` used consistently across all tasks (frozen dataclass, same field names)
- `MeshDocument` constructor signature matches between Task 4 (implementation) and Task 7 (usage)
- `load_mesh` returns `MeshDocument` everywhere
- `validate_path` and `detect_format` signatures consistent between Task 6 and Task 7
- Exception class names match between Task 1 (definition) and Tasks 6-7 (usage)
