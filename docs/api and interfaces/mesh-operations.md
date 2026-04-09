# Mesh Operations Interface

This document describes the public API surface for mesh loading, analysis, repair, transformation, and export operations.

## Module: `meshscope.core.mesh_data`

Core data types used throughout the application.

### `BoundingBox` (frozen dataclass)

Axis-aligned bounding box in mm.

| Field | Type | Description |
|---|---|---|
| `min_x`, `min_y`, `min_z` | `float` | Minimum coordinates |
| `max_x`, `max_y`, `max_z` | `float` | Maximum coordinates |

Properties: `size_x`, `size_y`, `size_z`, `center -> tuple[float, float, float]`

### `MeshMetadata` (frozen dataclass)

| Field | Type | Description |
|---|---|---|
| `vertex_count` | `int` | Number of vertices |
| `face_count` | `int` | Number of triangular faces |
| `bounding_box` | `BoundingBox` | Axis-aligned bounding box |
| `surface_area_mm2` | `float` | Total surface area |
| `volume_mm3` | `float \| None` | Volume (None if non-manifold) |
| `is_manifold` | `bool` | Whether mesh is manifold |

### `MeshData` (frozen dataclass)

| Field | Type | Description |
|---|---|---|
| `vertices` | `NDArray[float32]` shape (N, 3) | Vertex positions in mm |
| `faces` | `NDArray[uint32]` shape (M, 3) | Triangle vertex indices |
| `normals` | `NDArray[float32]` shape (M, 3) | Per-face unit normals |
| `metadata` | `MeshMetadata` | Computed properties |

---

## Module: `meshscope.core.mesh_loader`

### Constants

- `SUPPORTED_FORMATS: dict[str, str]` — Extension-to-trimesh-type mapping (`.stl`, `.obj`, `.3mf`, `.ply`)
- `MAX_FILE_SIZE_BYTES: int` — 500 MB limit

### Functions

```python
def detect_format(path: Path) -> str
```
Detect mesh format from file extension. Raises `UnsupportedFormatError`.

```python
def validate_path(path: Path) -> None
```
Validate file exists, is readable, has supported extension, within size limit. Raises `FileValidationError` subclasses.

```python
def load_mesh(path: str | Path) -> MeshDocument
```
Load a mesh file and return a `MeshDocument`. Validates, parses via trimesh with format-specific loader, computes metadata, checks for warnings.

---

## Module: `meshscope.core.mesh_exporter`

### Constants

- `SUPPORTED_EXPORT_FORMATS: set[str]` — `{"stl", "obj", "3mf", "ply"}`

### Functions

```python
def export_mesh(mesh: MeshData, path: Path, file_type: str) -> None
```
Export mesh to file using atomic write (temp file + rename). Raises `MeshExportError`.

```python
def check_symlink(path: Path) -> Path | None
```
Returns the realpath if any path component is a symlink, None otherwise.

```python
def get_format_warning(file_type: str) -> str | None
```
Returns data loss warning for the given format, or None.

---

## Module: `meshscope.core.mesh_analysis`

### `MeshAnalysis` (frozen dataclass)

| Field | Type | Description |
|---|---|---|
| `is_manifold` | `bool` | Overall manifold status |
| `is_watertight` | `bool` | Whether mesh is watertight |
| `hole_count` | `int` | Number of holes |
| `open_edge_count` | `int` | Number of open edges |
| `degenerate_face_count` | `int` | Number of zero-area faces |
| `non_manifold_edge_count` | `int` | Number of non-manifold edges |
| `open_edge_indices` | `NDArray[int64]` (N, 2) | Vertex index pairs for open edges |
| `non_manifold_edge_indices` | `NDArray[int64]` (N, 2) | Vertex index pairs for non-manifold edges |
| `degenerate_face_indices` | `NDArray[int64]` (N,) | Face indices of degenerate faces |

### Functions

```python
def analyze_mesh(mesh: MeshData) -> MeshAnalysis
```
Analyze mesh topology and return detailed diagnostics.

---

## Module: `meshscope.core.mesh_repair`

### `RepairPlan` (frozen dataclass)

| Field | Type | Description |
|---|---|---|
| `flipped_normal_count` | `int` | Normals to fix |
| `holes_to_fill` | `int` | Holes to fill |
| `degenerate_faces_to_remove` | `int` | Degenerate faces to remove |
| `estimated_face_delta` | `int` | Expected face count change |
| `high_impact_warning` | `bool` | True if face delta exceeds 5% |

### `RepairResult` (frozen dataclass)

| Field | Type | Description |
|---|---|---|
| `mesh` | `MeshData` | Repaired mesh |
| `normals_fixed` | `int` | Count of fixed normals |
| `holes_filled` | `int` | Count of filled holes |
| `degenerate_faces_removed` | `int` | Count of removed faces |
| `fully_repaired` | `bool` | True if all issues resolved |
| `remaining_issues` | `str \| None` | Description of remaining issues |

### Functions

```python
def plan_repair(analysis: MeshAnalysis, mesh: MeshData) -> RepairPlan
```
Dry-run repair planning on a copy. Returns what would be changed.

```python
def apply_repair(mesh: MeshData, plan: RepairPlan) -> RepairResult
```
Apply repairs: (1) remove degenerate faces, (2) fix normals, (3) fill holes. Raises `MeshRepairError`.

---

## Module: `meshscope.core.mesh_transform`

### `TransformResult` (frozen dataclass)

| Field | Type | Description |
|---|---|---|
| `mesh` | `MeshData` | Transformed mesh |
| `description` | `str` | Human-readable summary (e.g., "Scaled by 2.0x") |
| `warning` | `str \| None` | Warning if extreme transform |

### Functions

```python
def scale_mesh(mesh: MeshData, factor: float) -> TransformResult
```
Scale all vertices by uniform factor. Raises `MeshTransformError` if factor <= 0.

```python
def rotate_mesh(mesh: MeshData, axis: str, degrees: float) -> TransformResult
```
Rotate around center of mass by given degrees around x/y/z axis. Raises `MeshTransformError`.

```python
def mirror_mesh(mesh: MeshData, axis: str) -> TransformResult
```
Mirror across axis plane through model center. Reverses face winding. Raises `MeshTransformError`.

---

## Module: `meshscope.core.exceptions`

All exceptions carry a `user_message: str` attribute suitable for dialog display.

| Exception | Parent | Description |
|---|---|---|
| `MeshLoadError` | `Exception` | Base for all loading failures |
| `FileValidationError` | `MeshLoadError` | Pre-parse validation failure |
| `UnsupportedFormatError` | `FileValidationError` | Unknown extension |
| `FileTooLargeError` | `FileValidationError` | Exceeds 500MB limit |
| `FileNotFoundError_` | `FileValidationError` | File does not exist |
| `FileNotReadableError` | `FileValidationError` | Permission denied |
| `MeshParseError` | `MeshLoadError` | Parse failure |
| `CorruptFileError` | `MeshParseError` | Invalid file data |
| `EmptyMeshError` | `MeshParseError` | No geometry in file |
| `MeshExportError` | `Exception` | Base for export failures |
| `MeshRepairError` | `Exception` | Base for repair failures |
| `MeshTransformError` | `Exception` | Base for transform failures |

---

## Module: `meshscope.core.mesh_document`

### `MeshDocument`

Session container holding current mesh, original copy, undo stack, and analysis state.

```python
def __init__(
    self,
    mesh: MeshData,
    source_path: str,
    source_format: str,
    source_size_bytes: int,
    warnings: list[str] | None = None,
) -> None
```

| Attribute | Type | Description |
|---|---|---|
| `mesh` | `MeshData` | Current mesh state (mutable reference) |
| `original_mesh` | `MeshData` | Immutable copy of loaded mesh |
| `source_path` | `str` | File path of loaded file |
| `source_format` | `str` | Detected file format |
| `source_size_bytes` | `int` | File size in bytes |
| `undo_stack` | `UndoStack` | Ring buffer (max 10 entries) |
| `warnings` | `list[str]` | User-visible warnings |
| `analysis` | `MeshAnalysis \| None` | Invalidated on any mesh mutation |

---

## Module: `meshscope.core.config`

### Constants

- `CURRENT_SCHEMA_VERSION: int = 1`
- `DEFAULT_CONFIG: dict` — Default settings including print bed preset

### `AppConfig`

```python
def get(self, section: str, key: str) -> Any
def set(self, section: str, key: str, value: Any) -> None
def to_dict(self) -> dict[str, Any]
```
Property: `version -> int`

### Functions

```python
def load_config(path: Path | None = None) -> AppConfig
```
Load from file. Returns defaults on any error.

```python
def save_config(config: AppConfig, path: Path | None = None) -> None
```
Save with atomic write.
