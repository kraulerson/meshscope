# File Loading — Implementation Design

**Feature:** #1 File Loading (FRD Section 1)
**Date:** 2026-04-06
**Status:** Approved
**Scope:** Data layer only — no UI, no rendering. Viewport integration comes with Feature 2.

---

## Goal

Load STL, OBJ, 3MF, and PLY mesh files from disk into an in-memory `MeshDocument`, with full validation, error handling, and computed metadata. The UI layer consumes the result; this feature has no GUI dependency.

## Architecture

### Components

**`MeshData`** (`src/meshscope/core/mesh_data.py`)
Immutable data class holding the parsed mesh geometry and computed metadata.

```python
@dataclass(frozen=True)
class BoundingBox:
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    @property
    def size_x(self) -> float: ...  # max_x - min_x

    @property
    def size_y(self) -> float: ...

    @property
    def size_z(self) -> float: ...

    @property
    def center(self) -> tuple[float, float, float]: ...

@dataclass(frozen=True)
class MeshMetadata:
    vertex_count: int
    face_count: int
    bounding_box: BoundingBox
    surface_area_mm2: float
    volume_mm3: float | None  # None if non-manifold
    is_manifold: bool

@dataclass(frozen=True)
class MeshData:
    vertices: np.ndarray     # float32, shape (N, 3)
    faces: np.ndarray        # uint32, shape (M, 3)
    normals: np.ndarray      # float32, shape (M, 3) — per-face
    metadata: MeshMetadata
```

**`MeshDocument`** (`src/meshscope/core/mesh_document.py`)
Mutable session wrapper. Holds current mesh, original mesh for reset, undo stack, source file info, and user-visible warnings.

```python
class MeshDocument:
    mesh: MeshData                    # Current state (post-transforms)
    original_mesh: MeshData           # Immutable copy from load time
    source_path: str                  # Original file path
    source_format: str                # "stl_binary", "stl_ascii", "obj", "3mf", "ply_ascii", "ply_binary"
    source_size_bytes: int            # Original file size
    undo_stack: UndoStack             # Empty at creation, populated by Features 7-8
    warnings: list[str]              # User-visible warnings (OBJ directives, unit mismatch, etc.)
```

**`load_mesh()`** (`src/meshscope/core/mesh_loader.py`)
The public API. Validates path, parses via trimesh, constructs MeshDocument.

```python
def load_mesh(path: str | Path) -> MeshDocument:
    """Load a mesh file and return a MeshDocument.

    Raises MeshLoadError subclasses on failure.
    """
```

**`UndoStack`** (`src/meshscope/core/undo_stack.py`)
Ring buffer for mesh state snapshots. Created empty by MeshDocument. Populated by Features 7 (Repair) and 8 (Transforms). Included here because MeshDocument references it, but its logic is exercised later.

```python
class UndoStack:
    def __init__(self, max_entries: int = 10) -> None: ...
    def push(self, mesh: MeshData) -> None: ...
    def undo(self) -> MeshData | None: ...
    def redo(self) -> MeshData | None: ...
    def can_undo(self) -> bool: ...
    def can_redo(self) -> bool: ...
    @property
    def memory_bytes(self) -> int: ...
```

**`exceptions`** (`src/meshscope/core/exceptions.py`)
Custom exception hierarchy. Each exception carries a `user_message` attribute with the exact text from the FRD failure states table, ready for direct display in the UI.

```python
class MeshLoadError(Exception):
    """Base exception for all mesh loading failures."""
    def __init__(self, user_message: str) -> None:
        self.user_message = user_message
        super().__init__(user_message)

class FileValidationError(MeshLoadError): ...
class UnsupportedFormatError(FileValidationError): ...
class FileTooLargeError(FileValidationError): ...
class FileNotFoundError_(FileValidationError): ...  # Trailing underscore avoids shadowing builtin
class FileNotReadableError(FileValidationError): ...

class MeshParseError(MeshLoadError): ...
class CorruptFileError(MeshParseError): ...
class EmptyMeshError(MeshParseError): ...
```

---

## Data Flow

```
path (str | Path)
  → validate_path(path: Path) -> ValidatedPath
      checks: exists, is_file, readable, extension in SUPPORTED_FORMATS, size ≤ 500MB
      raises: FileValidationError subclass with user_message

  → detect_format(path: Path) -> str
      extension map (case-insensitive):
        .stl → "stl", .obj → "obj", .3mf → "3mf", .ply → "ply"

  → parse_mesh(path: Path, file_type: str) -> tuple[MeshData, list[str]]
      calls: trimesh.load(str(path), file_type=file_type)
      handles: trimesh exceptions → CorruptFileError
      validates: result.faces > 0 or raise EmptyMeshError
      detects: OBJ unsupported directives → warning string
      detects: 3MF multiple meshes → warning string
      converts: trimesh.Trimesh → MeshData (vertices, faces, normals, metadata)
      returns: (MeshData, warnings)

  → check_unit_mismatch(metadata: MeshMetadata) -> str | None
      if all bbox dimensions < 1mm → warning
      if any bbox dimension > 10,000mm → warning
      else → None

  → MeshDocument(mesh, original_mesh=copy, source_path, source_format, source_size, warnings)
```

---

## Format-Specific Handling

### STL
- `trimesh.load(path, file_type="stl")` handles binary/ASCII detection
- `source_format` set to `"stl_binary"` or `"stl_ascii"` based on trimesh's detection
- Pre-parse validation: compare file size against declared triangle count for binary STL (`expected = 84 + N*50`). Reject if mismatch exceeds 1KB tolerance (accounts for non-standard padding).

### OBJ
- `trimesh.load(path, file_type="obj")` parses vertices and faces
- Scan file for unsupported directive prefixes (`mtllib`, `usemtl`, `vt`, `g`, `s`, `cstype`, `curv`, `surf`) before or after loading. Collect unique directive types found. If any: add warning "This OBJ file contains {list} which are not supported. These will be ignored."
- OBJ face indices are 1-based; trimesh converts to 0-based internally.

### 3MF
- `trimesh.load(path, file_type="3mf")` extracts mesh from ZIP archive
- If result is a `trimesh.Scene` (multiple meshes): take the first mesh, add warning "This 3MF file contains {N} meshes. Only the first was loaded."
- Catch `zipfile.BadZipFile` → CorruptFileError

### PLY
- `trimesh.load(path, file_type="ply")` handles ASCII/binary detection
- `source_format` set to `"ply_ascii"` or `"ply_binary"` based on header inspection

---

## Metadata Computation

All computed from trimesh's mesh object at load time:

| Field | Source |
|---|---|
| vertex_count | `len(mesh.vertices)` |
| face_count | `len(mesh.faces)` |
| bounding_box | `mesh.bounds` → min/max per axis |
| surface_area_mm2 | `mesh.area` |
| volume_mm3 | `mesh.volume` if `mesh.is_volume` else None |
| is_manifold | `mesh.is_volume` (trimesh's manifold check) |

---

## File Structure

```
src/meshscope/core/
├── __init__.py
├── exceptions.py        — MeshLoadError hierarchy
├── mesh_data.py         — BoundingBox, MeshMetadata, MeshData dataclasses
├── mesh_document.py     — MeshDocument class
├── mesh_loader.py       — validate_path(), detect_format(), parse_mesh(), load_mesh()
├── undo_stack.py        — UndoStack (shell — logic exercised by Features 7-8)
└── logging.py           — (existing) structured logging

tests/
├── unit/
│   ├── test_mesh_data.py       — BoundingBox, MeshMetadata, MeshData construction
│   ├── test_mesh_loading.py    — load_mesh() success and error paths
│   ├── test_mesh_validation.py — validate_path() edge cases
│   └── test_undo_stack.py      — UndoStack basic operations
├── fixtures/
│   ├── valid/
│   │   ├── cube.stl        — binary STL, simple cube (8 vertices, 12 faces)
│   │   ├── cube_ascii.stl  — ASCII STL, same cube
│   │   ├── cube.obj        — OBJ with only v/f lines
│   │   ├── cube.3mf        — valid 3MF archive
│   │   └── cube.ply        — PLY ASCII
│   └── invalid/
│       ├── corrupt.stl         — truncated binary STL
│       ├── wrong_count.stl     — header says 1000 triangles, file has 10
│       ├── zero_faces.stl      — valid header, 0 triangles
│       ├── malformed.obj       — invalid face indices
│       ├── bad_archive.3mf     — not a valid ZIP
│       └── empty_file.ply      — 0 bytes
```

---

## Test Strategy

Tests are pure Python — no GUI, no GPU, no display server needed. CI-safe on all platforms.

**Success cases:**
- Load each format (STL binary, STL ASCII, OBJ, 3MF, PLY) → correct vertex/face counts, metadata
- Metadata computation (area, volume, manifold status) matches expected values for known geometry

**Validation failures:**
- Unsupported extension → UnsupportedFormatError with correct message
- File too large (mock) → FileTooLargeError
- File not found → FileNotFoundError_
- Permission denied (mock) → FileNotReadableError

**Parse failures:**
- Corrupt file per format → CorruptFileError with format-specific message
- Zero-face file → EmptyMeshError

**Warnings:**
- OBJ with material directives → warning in MeshDocument.warnings
- Unit mismatch (tiny bounding box) → warning in MeshDocument.warnings
- Unit mismatch (huge bounding box) → warning in MeshDocument.warnings

**Data integrity:**
- Vertices are float32, shape (N,3)
- Faces are uint32, shape (M,3)
- Normals are float32, shape (M,3)
- MeshData is immutable (frozen dataclass)
- MeshDocument.original_mesh is independent copy (mutating mesh doesn't affect original)

---

## Decisions

- **Headless-only** — no UI in this feature. Viewport integration is Feature 2.
- **trimesh for all I/O** — per Bible architecture decision. Format-specific `file_type` parameter, never generic `load()`.
- **UndoStack included as shell** — empty at construction, tested with basic push/pop, full logic comes with Features 7-8.
- **Warnings as strings** — simple list of user-displayable strings. No warning severity levels for MVP.
- **No async loading in this feature** — synchronous `load_mesh()`. Threading/progress indicator is a UI concern added in Feature 2 when the viewport exists.
