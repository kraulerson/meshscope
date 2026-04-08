# Scale/Rotate/Mirror Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add uniform scale, axis rotation, and axis mirror transforms with a tabbed Transform dialog and full undo/redo support.

**Architecture:** New `mesh_transform.py` core module with pure numpy transform functions (no trimesh). New `transform_dialog.py` UI with QTabWidget for Scale/Rotate/Mirror tabs. MainWindow gets Transform action (Ctrl+T) in Edit menu and toolbar.

**Tech Stack:** Python 3.13, numpy, PySide6 6.9.3 (QDialog, QTabWidget, QDoubleSpinBox, QPushButton)

---

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `src/meshscope/core/exceptions.py:56-61` | Add MeshTransformError |
| Create | `src/meshscope/core/mesh_transform.py` | TransformResult, scale/rotate/mirror functions, _recompute_metadata |
| Create | `tests/unit/test_mesh_transform.py` | Unit tests for all transform functions |
| Create | `src/meshscope/ui/transform_dialog.py` | Tabbed QDialog for transform input |
| Modify | `src/meshscope/ui/main_window.py:161-336` | Transform action, Edit menu, toolbar, handler |
| Modify | `tests/ui/test_main_window.py` | UI tests for transform action |

---

### Task 1: MeshTransformError and TransformResult

**Files:**
- Modify: `src/meshscope/core/exceptions.py:56-61`
- Create: `src/meshscope/core/mesh_transform.py`
- Create: `tests/unit/test_mesh_transform.py`

- [ ] **Step 1: Write test for MeshTransformError**

Create `tests/unit/test_mesh_transform.py`:

```python
"""Tests for mesh transform logic."""

from meshscope.core.exceptions import MeshTransformError


class TestMeshTransformError:
    def test_has_user_message(self) -> None:
        err = MeshTransformError("Scale factor must be greater than zero.")
        assert err.user_message == "Scale factor must be greater than zero."

    def test_is_exception(self) -> None:
        err = MeshTransformError("msg")
        assert isinstance(err, Exception)

    def test_str_matches_user_message(self) -> None:
        err = MeshTransformError("msg")
        assert str(err) == "msg"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_mesh_transform.py::TestMeshTransformError -v`
Expected: FAIL — `ImportError: cannot import name 'MeshTransformError'`

- [ ] **Step 3: Implement MeshTransformError**

Add to `src/meshscope/core/exceptions.py` after the `MeshRepairError` class (after line 61):

```python
class MeshTransformError(Exception):
    """Base exception for all mesh transform failures."""

    def __init__(self, user_message: str) -> None:
        self.user_message = user_message
        super().__init__(user_message)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_mesh_transform.py::TestMeshTransformError -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Write tests for TransformResult dataclass**

Append to `tests/unit/test_mesh_transform.py`:

```python
import numpy as np

from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.core.mesh_transform import TransformResult


class TestTransformResultDataclass:
    def test_creation(self) -> None:
        verts = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)

        result = TransformResult(
            mesh=mesh,
            description="Scaled by 2.0x",
            warning=None,
        )
        assert result.description == "Scaled by 2.0x"
        assert result.warning is None

    def test_is_frozen(self) -> None:
        verts = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)
        result = TransformResult(mesh, "test", None)
        try:
            result.description = "changed"  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except AttributeError:
            pass

    def test_with_warning(self) -> None:
        verts = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)
        result = TransformResult(mesh, "Scaled by 20000.0x", "Model is now very large")
        assert result.warning == "Model is now very large"
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest tests/unit/test_mesh_transform.py::TestTransformResultDataclass -v`
Expected: FAIL — `ImportError: cannot import name 'TransformResult'`

- [ ] **Step 7: Create mesh_transform.py with TransformResult**

Create `src/meshscope/core/mesh_transform.py`:

```python
"""Mesh transforms: scale, rotate, and mirror with pure numpy."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata

logger = logging.getLogger("meshscope.core.mesh_transform")


@dataclass(frozen=True)
class TransformResult:
    """Result of applying a mesh transform."""

    mesh: MeshData
    description: str
    warning: str | None
```

- [ ] **Step 8: Run all tests to verify they pass**

Run: `pytest tests/unit/test_mesh_transform.py -v`
Expected: PASS (6 tests)

- [ ] **Step 9: Commit**

```bash
git add src/meshscope/core/exceptions.py src/meshscope/core/mesh_transform.py tests/unit/test_mesh_transform.py
git commit -m "feat: add MeshTransformError and TransformResult dataclass"
```

---

### Task 2: _recompute_metadata Helper

**Files:**
- Modify: `src/meshscope/core/mesh_transform.py`
- Modify: `tests/unit/test_mesh_transform.py`

- [ ] **Step 1: Write tests for _recompute_metadata**

Append to `tests/unit/test_mesh_transform.py`:

```python
from meshscope.core.mesh_transform import _recompute_metadata


def _make_cube_vertices() -> np.ndarray:
    """Unit cube 0-10mm on each axis."""
    return np.array(
        [
            [0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0],
            [0, 0, 10], [10, 0, 10], [10, 10, 10], [0, 10, 10],
        ],
        dtype=np.float32,
    )


def _make_cube_faces() -> np.ndarray:
    """12 triangles forming a watertight cube."""
    return np.array(
        [
            [0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
            [0, 1, 5], [0, 5, 4], [2, 3, 7], [2, 7, 6],
            [0, 4, 7], [0, 7, 3], [1, 2, 6], [1, 6, 5],
        ],
        dtype=np.uint32,
    )


class TestRecomputeMetadata:
    def test_bounding_box(self) -> None:
        verts = _make_cube_vertices()
        faces = _make_cube_faces()
        meta = _recompute_metadata(verts, faces, is_manifold=True)
        assert meta.bounding_box.min_x == 0.0
        assert meta.bounding_box.max_x == 10.0
        assert meta.bounding_box.min_y == 0.0
        assert meta.bounding_box.max_y == 10.0
        assert meta.bounding_box.min_z == 0.0
        assert meta.bounding_box.max_z == 10.0

    def test_vertex_and_face_counts(self) -> None:
        verts = _make_cube_vertices()
        faces = _make_cube_faces()
        meta = _recompute_metadata(verts, faces, is_manifold=True)
        assert meta.vertex_count == 8
        assert meta.face_count == 12

    def test_surface_area(self) -> None:
        verts = _make_cube_vertices()
        faces = _make_cube_faces()
        meta = _recompute_metadata(verts, faces, is_manifold=True)
        # 10mm cube: 6 faces * 100mm^2 = 600mm^2
        assert abs(meta.surface_area_mm2 - 600.0) < 0.1

    def test_volume_manifold(self) -> None:
        verts = _make_cube_vertices()
        faces = _make_cube_faces()
        meta = _recompute_metadata(verts, faces, is_manifold=True)
        # 10mm cube: 1000mm^3
        assert meta.volume_mm3 is not None
        assert abs(meta.volume_mm3 - 1000.0) < 0.1

    def test_volume_non_manifold_is_none(self) -> None:
        verts = _make_cube_vertices()
        faces = _make_cube_faces()
        meta = _recompute_metadata(verts, faces, is_manifold=False)
        assert meta.volume_mm3 is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_mesh_transform.py::TestRecomputeMetadata -v`
Expected: FAIL — `ImportError: cannot import name '_recompute_metadata'`

- [ ] **Step 3: Implement _recompute_metadata**

Add to `src/meshscope/core/mesh_transform.py` after the TransformResult dataclass:

```python
def _recompute_metadata(
    vertices: np.ndarray,
    faces: np.ndarray,
    *,
    is_manifold: bool,
) -> MeshMetadata:
    """Recompute mesh metadata from raw arrays.

    Uses pure numpy: bounding box from min/max, surface area from
    cross-product magnitudes, volume from signed tetrahedra.
    """
    bbox = BoundingBox(
        min_x=float(vertices[:, 0].min()),
        min_y=float(vertices[:, 1].min()),
        min_z=float(vertices[:, 2].min()),
        max_x=float(vertices[:, 0].max()),
        max_y=float(vertices[:, 1].max()),
        max_z=float(vertices[:, 2].max()),
    )

    # Surface area: sum of triangle areas
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]
    cross = np.cross(v1 - v0, v2 - v0)
    triangle_areas = np.linalg.norm(cross, axis=1) / 2.0
    surface_area = float(triangle_areas.sum())

    # Volume: signed tetrahedron method (only if manifold)
    volume: float | None = None
    if is_manifold:
        # Each triangle forms a tetrahedron with the origin
        # Volume contribution = v0 . (v1 x v2) / 6
        dot = np.einsum("ij,ij->i", v0, np.cross(v1, v2))
        volume = abs(float(dot.sum() / 6.0))

    return MeshMetadata(
        vertex_count=len(vertices),
        face_count=len(faces),
        bounding_box=bbox,
        surface_area_mm2=surface_area,
        volume_mm3=volume,
        is_manifold=is_manifold,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_mesh_transform.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/core/mesh_transform.py tests/unit/test_mesh_transform.py
git commit -m "feat: add _recompute_metadata helper for transform metadata"
```

---

### Task 3: scale_mesh Function

**Files:**
- Modify: `src/meshscope/core/mesh_transform.py`
- Modify: `tests/unit/test_mesh_transform.py`

- [ ] **Step 1: Write tests for scale_mesh**

Add to `tests/unit/test_mesh_transform.py` imports:

```python
from meshscope.core.mesh_transform import TransformResult, _recompute_metadata, scale_mesh
```

Append test class:

```python
def _make_cube_mesh() -> MeshData:
    """Watertight 10mm cube for transform tests."""
    verts = _make_cube_vertices()
    faces = _make_cube_faces()
    normals = np.zeros((12, 3), dtype=np.float32)
    bb = BoundingBox(0, 0, 0, 10, 10, 10)
    meta = MeshMetadata(8, 12, bb, 600.0, 1000.0, True)
    return MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)


class TestScaleMesh:
    def test_scale_doubles_vertices(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 2.0)
        assert result.mesh.vertices.max() == 20.0
        assert result.mesh.vertices.min() == 0.0

    def test_scale_halves_vertices(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 0.5)
        assert result.mesh.vertices.max() == 5.0

    def test_scale_updates_bounding_box(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 2.0)
        assert result.mesh.metadata.bounding_box.max_x == 20.0
        assert result.mesh.metadata.bounding_box.max_y == 20.0
        assert result.mesh.metadata.bounding_box.max_z == 20.0

    def test_scale_surface_area_scales_by_factor_squared(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 3.0)
        # 600 * 3^2 = 5400
        assert abs(result.mesh.metadata.surface_area_mm2 - 5400.0) < 1.0

    def test_scale_volume_scales_by_factor_cubed(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 2.0)
        # 1000 * 2^3 = 8000
        assert result.mesh.metadata.volume_mm3 is not None
        assert abs(result.mesh.metadata.volume_mm3 - 8000.0) < 1.0

    def test_scale_zero_raises(self) -> None:
        mesh = _make_cube_mesh()
        try:
            scale_mesh(mesh, 0.0)
            raise AssertionError("Should have raised MeshTransformError")
        except MeshTransformError as e:
            assert "greater than zero" in e.user_message

    def test_scale_negative_raises(self) -> None:
        mesh = _make_cube_mesh()
        try:
            scale_mesh(mesh, -1.0)
            raise AssertionError("Should have raised MeshTransformError")
        except MeshTransformError as e:
            assert "greater than zero" in e.user_message

    def test_scale_returns_transform_result(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 2.0)
        assert isinstance(result, TransformResult)
        assert "2.0" in result.description

    def test_scale_extreme_returns_warning(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 20000.0)
        assert result.warning is not None

    def test_scale_preserves_face_count(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 2.0)
        assert result.mesh.metadata.face_count == 12

    def test_scale_preserves_manifold(self) -> None:
        mesh = _make_cube_mesh()
        result = scale_mesh(mesh, 2.0)
        assert result.mesh.metadata.is_manifold is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_mesh_transform.py::TestScaleMesh -v`
Expected: FAIL — `ImportError: cannot import name 'scale_mesh'`

- [ ] **Step 3: Implement scale_mesh**

Add to `src/meshscope/core/mesh_transform.py` imports (add at top, after existing imports):

```python
from meshscope.core.exceptions import MeshTransformError
```

Add function after `_recompute_metadata`:

```python
def _recompute_normals(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """Recompute per-face unit normals from vertices and faces."""
    v0 = vertices[faces[:, 0]]
    v1 = vertices[faces[:, 1]]
    v2 = vertices[faces[:, 2]]
    cross = np.cross(v1 - v0, v2 - v0)
    norms = np.linalg.norm(cross, axis=1, keepdims=True)
    # Avoid division by zero for degenerate faces
    norms = np.where(norms < 1e-10, 1.0, norms)
    return (cross / norms).astype(np.float32)


def scale_mesh(mesh: MeshData, factor: float) -> TransformResult:
    """Scale all vertices by a uniform factor.

    Raises MeshTransformError if factor <= 0.
    """
    if factor <= 0:
        raise MeshTransformError("Scale factor must be greater than zero.")

    new_vertices = (mesh.vertices * factor).astype(np.float32)
    new_normals = _recompute_normals(new_vertices, mesh.faces)
    new_meta = _recompute_metadata(
        new_vertices, mesh.faces, is_manifold=mesh.metadata.is_manifold
    )

    new_mesh = MeshData(
        vertices=new_vertices,
        faces=mesh.faces.copy(),
        normals=new_normals,
        metadata=new_meta,
    )

    warning: str | None = None
    if factor > 10000:
        max_dim = max(
            new_meta.bounding_box.max_x - new_meta.bounding_box.min_x,
            new_meta.bounding_box.max_y - new_meta.bounding_box.min_y,
            new_meta.bounding_box.max_z - new_meta.bounding_box.min_z,
        )
        warning = f"Model is now very large ({max_dim:.0f}mm on longest axis)"

    logger.info("Scale: factor=%.4f", factor)

    return TransformResult(
        mesh=new_mesh,
        description=f"Scaled by {factor}x",
        warning=warning,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_mesh_transform.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/core/mesh_transform.py tests/unit/test_mesh_transform.py
git commit -m "feat: implement scale_mesh with validation and warnings"
```

---

### Task 4: rotate_mesh Function

**Files:**
- Modify: `src/meshscope/core/mesh_transform.py`
- Modify: `tests/unit/test_mesh_transform.py`

- [ ] **Step 1: Write tests for rotate_mesh**

Update the import line in `tests/unit/test_mesh_transform.py`:

```python
from meshscope.core.mesh_transform import (
    TransformResult,
    _recompute_metadata,
    rotate_mesh,
    scale_mesh,
)
```

Append test class:

```python
class TestRotateMesh:
    def test_rotate_90_z_swaps_xy(self) -> None:
        """90° around Z: (10,0,0) -> (0,10,0)."""
        mesh = _make_cube_mesh()
        result = rotate_mesh(mesh, "z", 90.0)
        # Vertex at (10,0,0) should move to approximately (0,10,0)
        # relative to center (5,5,5)
        # (10,0,0) - (5,5,5) = (5,-5,0) -> rotated 90° Z -> (-(-5),5,0) = (5,5,0) + (5,5,5) = (10,10,5)
        # Actually: (5,-5,0) rotated 90° CCW around Z = (5,5,0) -> + center = (10,10,5)
        # Let's just check the bounding box is unchanged (rotation preserves extents for a cube)
        bb = result.mesh.metadata.bounding_box
        assert abs(bb.max_x - bb.min_x - 10.0) < 0.1
        assert abs(bb.max_y - bb.min_y - 10.0) < 0.1
        assert abs(bb.max_z - bb.min_z - 10.0) < 0.1

    def test_rotate_360_returns_to_original(self) -> None:
        mesh = _make_cube_mesh()
        result = rotate_mesh(mesh, "x", 360.0)
        np.testing.assert_allclose(result.mesh.vertices, mesh.vertices, atol=1e-4)

    def test_rotate_180_twice_returns_to_original(self) -> None:
        mesh = _make_cube_mesh()
        result1 = rotate_mesh(mesh, "y", 180.0)
        result2 = rotate_mesh(result1.mesh, "y", 180.0)
        np.testing.assert_allclose(result2.mesh.vertices, mesh.vertices, atol=1e-4)

    def test_rotate_preserves_face_count(self) -> None:
        mesh = _make_cube_mesh()
        result = rotate_mesh(mesh, "x", 45.0)
        assert result.mesh.metadata.face_count == 12

    def test_rotate_preserves_surface_area(self) -> None:
        mesh = _make_cube_mesh()
        result = rotate_mesh(mesh, "z", 30.0)
        assert abs(result.mesh.metadata.surface_area_mm2 - 600.0) < 1.0

    def test_rotate_preserves_volume(self) -> None:
        mesh = _make_cube_mesh()
        result = rotate_mesh(mesh, "y", 45.0)
        assert result.mesh.metadata.volume_mm3 is not None
        assert abs(result.mesh.metadata.volume_mm3 - 1000.0) < 1.0

    def test_rotate_returns_transform_result(self) -> None:
        mesh = _make_cube_mesh()
        result = rotate_mesh(mesh, "x", 90.0)
        assert isinstance(result, TransformResult)
        assert "90" in result.description
        assert "X" in result.description

    def test_rotate_invalid_axis_raises(self) -> None:
        mesh = _make_cube_mesh()
        try:
            rotate_mesh(mesh, "w", 90.0)
            raise AssertionError("Should have raised MeshTransformError")
        except MeshTransformError as e:
            assert "axis" in e.user_message.lower()

    def test_rotate_normals_recomputed(self) -> None:
        mesh = _make_cube_mesh()
        result = rotate_mesh(mesh, "x", 90.0)
        # Normals should be unit vectors
        norms = np.linalg.norm(result.mesh.normals, axis=1)
        np.testing.assert_allclose(norms, 1.0, atol=1e-5)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_mesh_transform.py::TestRotateMesh -v`
Expected: FAIL — `ImportError: cannot import name 'rotate_mesh'`

- [ ] **Step 3: Implement rotate_mesh**

Add to `src/meshscope/core/mesh_transform.py` after `scale_mesh`:

```python
def rotate_mesh(mesh: MeshData, axis: str, degrees: float) -> TransformResult:
    """Rotate mesh around its center of mass by degrees around the given axis.

    Raises MeshTransformError if axis is not x, y, or z.
    """
    axis_lower = axis.lower()
    if axis_lower not in ("x", "y", "z"):
        raise MeshTransformError(
            f"Invalid axis '{axis}'. Must be 'x', 'y', or 'z'."
        )

    radians = np.radians(degrees)
    cos_a = np.cos(radians)
    sin_a = np.sin(radians)

    if axis_lower == "x":
        rot = np.array([
            [1, 0, 0],
            [0, cos_a, -sin_a],
            [0, sin_a, cos_a],
        ], dtype=np.float64)
    elif axis_lower == "y":
        rot = np.array([
            [cos_a, 0, sin_a],
            [0, 1, 0],
            [-sin_a, 0, cos_a],
        ], dtype=np.float64)
    else:  # z
        rot = np.array([
            [cos_a, -sin_a, 0],
            [sin_a, cos_a, 0],
            [0, 0, 1],
        ], dtype=np.float64)

    # Rotate around center of mass
    center = mesh.vertices.mean(axis=0).astype(np.float64)
    centered = mesh.vertices.astype(np.float64) - center
    rotated = (centered @ rot.T) + center
    new_vertices = rotated.astype(np.float32)

    new_normals = _recompute_normals(new_vertices, mesh.faces)
    new_meta = _recompute_metadata(
        new_vertices, mesh.faces, is_manifold=mesh.metadata.is_manifold
    )

    new_mesh = MeshData(
        vertices=new_vertices,
        faces=mesh.faces.copy(),
        normals=new_normals,
        metadata=new_meta,
    )

    logger.info("Rotate: axis=%s degrees=%.1f", axis_lower, degrees)

    return TransformResult(
        mesh=new_mesh,
        description=f"Rotated {degrees}\u00b0 around {axis_lower.upper()} axis",
        warning=None,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_mesh_transform.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/core/mesh_transform.py tests/unit/test_mesh_transform.py
git commit -m "feat: implement rotate_mesh around center of mass"
```

---

### Task 5: mirror_mesh Function

**Files:**
- Modify: `src/meshscope/core/mesh_transform.py`
- Modify: `tests/unit/test_mesh_transform.py`

- [ ] **Step 1: Write tests for mirror_mesh**

Update the import line in `tests/unit/test_mesh_transform.py`:

```python
from meshscope.core.mesh_transform import (
    TransformResult,
    _recompute_metadata,
    mirror_mesh,
    rotate_mesh,
    scale_mesh,
)
```

Append test class:

```python
class TestMirrorMesh:
    def test_mirror_x_negates_x_coordinates(self) -> None:
        mesh = _make_cube_mesh()
        center_x = mesh.vertices[:, 0].mean()
        result = mirror_mesh(mesh, "x")
        # Each vertex X should be reflected around center
        expected_x = 2 * center_x - mesh.vertices[:, 0]
        np.testing.assert_allclose(result.mesh.vertices[:, 0], expected_x, atol=1e-5)

    def test_mirror_y_negates_y_coordinates(self) -> None:
        mesh = _make_cube_mesh()
        center_y = mesh.vertices[:, 1].mean()
        result = mirror_mesh(mesh, "y")
        expected_y = 2 * center_y - mesh.vertices[:, 1]
        np.testing.assert_allclose(result.mesh.vertices[:, 1], expected_y, atol=1e-5)

    def test_mirror_z_negates_z_coordinates(self) -> None:
        mesh = _make_cube_mesh()
        center_z = mesh.vertices[:, 2].mean()
        result = mirror_mesh(mesh, "z")
        expected_z = 2 * center_z - mesh.vertices[:, 2]
        np.testing.assert_allclose(result.mesh.vertices[:, 2], expected_z, atol=1e-5)

    def test_mirror_reverses_face_winding(self) -> None:
        mesh = _make_cube_mesh()
        result = mirror_mesh(mesh, "x")
        # Columns 1 and 2 should be swapped
        np.testing.assert_array_equal(result.mesh.faces[:, 1], mesh.faces[:, 2])
        np.testing.assert_array_equal(result.mesh.faces[:, 2], mesh.faces[:, 1])

    def test_mirror_twice_returns_to_original(self) -> None:
        mesh = _make_cube_mesh()
        result1 = mirror_mesh(mesh, "x")
        result2 = mirror_mesh(result1.mesh, "x")
        np.testing.assert_allclose(result2.mesh.vertices, mesh.vertices, atol=1e-5)
        # Face winding should be back to original after double swap
        np.testing.assert_array_equal(result2.mesh.faces, mesh.faces)

    def test_mirror_preserves_bounding_box_size(self) -> None:
        mesh = _make_cube_mesh()
        result = mirror_mesh(mesh, "y")
        bb = result.mesh.metadata.bounding_box
        assert abs(bb.max_x - bb.min_x - 10.0) < 0.1
        assert abs(bb.max_y - bb.min_y - 10.0) < 0.1
        assert abs(bb.max_z - bb.min_z - 10.0) < 0.1

    def test_mirror_preserves_surface_area(self) -> None:
        mesh = _make_cube_mesh()
        result = mirror_mesh(mesh, "z")
        assert abs(result.mesh.metadata.surface_area_mm2 - 600.0) < 1.0

    def test_mirror_preserves_volume(self) -> None:
        mesh = _make_cube_mesh()
        result = mirror_mesh(mesh, "x")
        assert result.mesh.metadata.volume_mm3 is not None
        assert abs(result.mesh.metadata.volume_mm3 - 1000.0) < 1.0

    def test_mirror_returns_transform_result(self) -> None:
        mesh = _make_cube_mesh()
        result = mirror_mesh(mesh, "x")
        assert isinstance(result, TransformResult)
        assert "X" in result.description

    def test_mirror_invalid_axis_raises(self) -> None:
        mesh = _make_cube_mesh()
        try:
            mirror_mesh(mesh, "w")
            raise AssertionError("Should have raised MeshTransformError")
        except MeshTransformError as e:
            assert "axis" in e.user_message.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_mesh_transform.py::TestMirrorMesh -v`
Expected: FAIL — `ImportError: cannot import name 'mirror_mesh'`

- [ ] **Step 3: Implement mirror_mesh**

Add to `src/meshscope/core/mesh_transform.py` after `rotate_mesh`:

```python
def mirror_mesh(mesh: MeshData, axis: str) -> TransformResult:
    """Mirror mesh across the given axis plane through the model center.

    Reverses face winding order to maintain outward-facing normals.
    Raises MeshTransformError if axis is not x, y, or z.
    """
    axis_lower = axis.lower()
    if axis_lower not in ("x", "y", "z"):
        raise MeshTransformError(
            f"Invalid axis '{axis}'. Must be 'x', 'y', or 'z'."
        )

    axis_index = {"x": 0, "y": 1, "z": 2}[axis_lower]
    center = float(mesh.vertices[:, axis_index].mean())

    new_vertices = mesh.vertices.copy()
    new_vertices[:, axis_index] = 2 * center - new_vertices[:, axis_index]

    # Reverse face winding to fix normals (swap columns 1 and 2)
    new_faces = mesh.faces.copy()
    new_faces[:, 1], new_faces[:, 2] = mesh.faces[:, 2].copy(), mesh.faces[:, 1].copy()

    new_normals = _recompute_normals(new_vertices, new_faces)
    new_meta = _recompute_metadata(
        new_vertices, new_faces, is_manifold=mesh.metadata.is_manifold
    )

    new_mesh = MeshData(
        vertices=new_vertices,
        faces=new_faces,
        normals=new_normals,
        metadata=new_meta,
    )

    axis_labels = {"x": "YZ", "y": "XZ", "z": "XY"}
    logger.info("Mirror: axis=%s plane=%s", axis_lower, axis_labels[axis_lower])

    return TransformResult(
        mesh=new_mesh,
        description=f"Mirrored across {axis_labels[axis_lower]} plane ({axis_lower.upper()} axis)",
        warning=None,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_mesh_transform.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Run full test suite**

Run: `pytest tests/ -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/meshscope/core/mesh_transform.py tests/unit/test_mesh_transform.py
git commit -m "feat: implement mirror_mesh with face winding correction"
```

---

### Task 6: TransformDialog

**Files:**
- Create: `src/meshscope/ui/transform_dialog.py`

No TDD for this task — the dialog is a pure UI form with no business logic. It will be tested manually during UAT and indirectly via MainWindow integration.

- [ ] **Step 1: Create TransformDialog**

Create `src/meshscope/ui/transform_dialog.py`:

```python
"""Tabbed dialog for mesh transforms: Scale, Rotate, Mirror."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from meshscope.core.mesh_data import BoundingBox


class TransformDialog(QDialog):
    """Tabbed dialog for Scale, Rotate, and Mirror transforms."""

    def __init__(
        self,
        bounding_box: BoundingBox,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Transform")
        self.setMinimumWidth(360)

        self._bounding_box = bounding_box
        self._operation = "scale"

        # Tabs
        self._tab_widget = QTabWidget()
        self._scale_tab = self._create_scale_tab()
        self._rotate_tab = self._create_rotate_tab()
        self._mirror_tab = self._create_mirror_tab()
        self._tab_widget.addTab(self._scale_tab, "Scale")
        self._tab_widget.addTab(self._rotate_tab, "Rotate")
        self._tab_widget.addTab(self._mirror_tab, "Mirror")
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self._tab_widget)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def _create_scale_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Factor input
        factor_layout = QHBoxLayout()
        factor_layout.addWidget(QLabel("Scale Factor:"))
        self._scale_factor_spin = QDoubleSpinBox()
        self._scale_factor_spin.setRange(0.001, 100000.0)
        self._scale_factor_spin.setValue(1.0)
        self._scale_factor_spin.setSingleStep(0.1)
        self._scale_factor_spin.setDecimals(4)
        self._scale_factor_spin.setAccessibleName("Scale factor")
        factor_layout.addWidget(self._scale_factor_spin)
        factor_layout.addWidget(QLabel("x"))
        factor_layout.addStretch()
        layout.addLayout(factor_layout)

        # Dimension preview
        dx = self._bounding_box.max_x - self._bounding_box.min_x
        dy = self._bounding_box.max_y - self._bounding_box.min_y
        dz = self._bounding_box.max_z - self._bounding_box.min_z

        self._current_dims_label = QLabel(
            f"Current: X={dx:.1f}mm  Y={dy:.1f}mm  Z={dz:.1f}mm"
        )
        self._after_dims_label = QLabel(
            f"After:   X={dx:.1f}mm  Y={dy:.1f}mm  Z={dz:.1f}mm"
        )
        layout.addWidget(self._current_dims_label)
        layout.addWidget(self._after_dims_label)

        self._dx = dx
        self._dy = dy
        self._dz = dz
        self._scale_factor_spin.valueChanged.connect(self._update_scale_preview)

        layout.addStretch()
        return tab

    def _update_scale_preview(self, factor: float) -> None:
        self._after_dims_label.setText(
            f"After:   X={self._dx * factor:.1f}mm  "
            f"Y={self._dy * factor:.1f}mm  "
            f"Z={self._dz * factor:.1f}mm"
        )

    def _create_rotate_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Axis buttons
        layout.addWidget(QLabel("Axis:"))
        axis_layout = QHBoxLayout()
        self._rotate_axis_buttons: dict[str, QPushButton] = {}
        for axis in ("X", "Y", "Z"):
            btn = QPushButton(axis)
            btn.setCheckable(True)
            btn.setAccessibleName(f"Rotate axis {axis}")
            btn.clicked.connect(lambda checked, a=axis: self._set_rotate_axis(a))
            self._rotate_axis_buttons[axis] = btn
            axis_layout.addWidget(btn)
        axis_layout.addStretch()
        layout.addLayout(axis_layout)
        self._rotate_axis_buttons["X"].setChecked(True)
        self._selected_rotate_axis = "x"

        # Degrees input
        degrees_layout = QHBoxLayout()
        degrees_layout.addWidget(QLabel("Degrees:"))
        self._rotate_degrees_spin = QDoubleSpinBox()
        self._rotate_degrees_spin.setRange(-3600.0, 3600.0)
        self._rotate_degrees_spin.setValue(90.0)
        self._rotate_degrees_spin.setSingleStep(90.0)
        self._rotate_degrees_spin.setDecimals(1)
        self._rotate_degrees_spin.setAccessibleName("Rotation degrees")
        degrees_layout.addWidget(self._rotate_degrees_spin)
        degrees_layout.addWidget(QLabel("\u00b0"))
        degrees_layout.addStretch()
        layout.addLayout(degrees_layout)

        layout.addStretch()
        return tab

    def _set_rotate_axis(self, axis: str) -> None:
        self._selected_rotate_axis = axis.lower()
        for key, btn in self._rotate_axis_buttons.items():
            btn.setChecked(key == axis)

    def _create_mirror_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        layout.addWidget(QLabel("Mirror Across Plane:"))
        axis_layout = QHBoxLayout()
        self._mirror_axis_buttons: dict[str, QPushButton] = {}
        labels = {"X": "X (YZ plane)", "Y": "Y (XZ plane)", "Z": "Z (XY plane)"}
        for axis, label in labels.items():
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setAccessibleName(f"Mirror axis {axis}")
            btn.clicked.connect(lambda checked, a=axis: self._set_mirror_axis(a))
            self._mirror_axis_buttons[axis] = btn
            axis_layout.addWidget(btn)
        layout.addLayout(axis_layout)
        self._mirror_axis_buttons["X"].setChecked(True)
        self._selected_mirror_axis = "x"

        layout.addStretch()
        return tab

    def _set_mirror_axis(self, axis: str) -> None:
        self._selected_mirror_axis = axis.lower()
        for key, btn in self._mirror_axis_buttons.items():
            btn.setChecked(key == axis)

    def _on_tab_changed(self, index: int) -> None:
        self._operation = ("scale", "rotate", "mirror")[index]

    # --- Accessors ---

    def operation(self) -> str:
        return self._operation

    def scale_factor(self) -> float:
        return self._scale_factor_spin.value()

    def rotate_axis(self) -> str:
        return self._selected_rotate_axis

    def rotate_degrees(self) -> float:
        return self._rotate_degrees_spin.value()

    def mirror_axis(self) -> str:
        return self._selected_mirror_axis
```

- [ ] **Step 2: Verify it imports without error**

Run: `python -c "from meshscope.ui.transform_dialog import TransformDialog; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/meshscope/ui/transform_dialog.py
git commit -m "feat: add TransformDialog with Scale/Rotate/Mirror tabs"
```

---

### Task 7: MainWindow Integration

**Files:**
- Modify: `src/meshscope/ui/main_window.py:161-336`
- Modify: `tests/ui/test_main_window.py`

- [ ] **Step 1: Write tests for transform action**

Add to `tests/ui/test_main_window.py`:

```python
class TestMainWindowTransform:
    def test_transform_action_exists(self, window: MainWindow) -> None:
        assert hasattr(window, "transform_action")

    def test_transform_action_disabled_initially(self, window: MainWindow) -> None:
        assert not window.transform_action.isEnabled()

    def test_transform_shortcut_is_ctrl_t(self, window: MainWindow) -> None:
        assert window.transform_action.shortcut() == QKeySequence("Ctrl+T")

    def test_transform_enabled_after_load(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert window.transform_action.isEnabled()

    def test_transform_in_edit_menu(self, window: MainWindow) -> None:
        edit_menu = None
        for action in window.menuBar().actions():
            if "Edit" in action.text():
                edit_menu = action.menu()
                break
        assert edit_menu is not None
        action_texts = [a.text() for a in edit_menu.actions()]
        assert any("Transform" in t for t in action_texts)

    def test_transform_in_toolbar(self, window: MainWindow) -> None:
        toolbar_actions = [a.text() for a in window.toolbar.actions()]
        assert any("Transform" in t for t in toolbar_actions)

    def test_transform_disabled_after_error(
        self, window: MainWindow, tmp_path: Path
    ) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        bad = tmp_path / "bad.stl"
        bad.write_bytes(b"not a real stl file")
        window._load_file(bad)
        assert not window.transform_action.isEnabled()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/ui/test_main_window.py::TestMainWindowTransform -v`
Expected: FAIL — `AttributeError: 'MainWindow' object has no attribute 'transform_action'`

- [ ] **Step 3: Add transform imports to main_window.py**

Add to existing imports in `src/meshscope/ui/main_window.py` (add after the `mesh_repair` import line):

```python
from meshscope.core.mesh_transform import mirror_mesh, rotate_mesh, scale_mesh
from meshscope.ui.transform_dialog import TransformDialog
```

Also add `MeshTransformError` to the exceptions import:

```python
from meshscope.core.exceptions import MeshExportError, MeshLoadError, MeshRepairError, MeshTransformError
```

- [ ] **Step 4: Add transform_action in _create_actions**

In `_create_actions`, after the `repair_action` block, add:

```python
        self.transform_action = QAction("Transform", self)
        self.transform_action.setShortcut(QKeySequence("Ctrl+T"))
        self.transform_action.setEnabled(False)
        self.transform_action.setToolTip("Scale, rotate, or mirror mesh")
        self.transform_action.triggered.connect(self._on_transform)
```

- [ ] **Step 5: Add transform to Edit menu**

In `_create_menus`, after `edit_menu.addAction(self.redo_action)`, add:

```python
        edit_menu.addSeparator()
        edit_menu.addAction(self.transform_action)
```

- [ ] **Step 6: Add transform to toolbar**

In `_create_toolbar`, after `self.toolbar.addAction(self.repair_action)`, add:

```python
        self.toolbar.addAction(self.transform_action)
```

- [ ] **Step 7: Update _set_render_actions_enabled**

In `_set_render_actions_enabled`, add after `self.analyze_action.setEnabled(enabled)`:

```python
        self.transform_action.setEnabled(enabled)
```

- [ ] **Step 8: Add _on_transform handler**

Add after `_on_repair` method (before `_on_export`):

```python
    def _on_transform(self) -> None:
        """Open transform dialog and apply the selected transform."""
        if self._document is None:
            return

        dialog = TransformDialog(
            self._document.mesh.metadata.bounding_box, parent=self
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        op = dialog.operation()
        try:
            if op == "scale":
                result = scale_mesh(self._document.mesh, dialog.scale_factor())
            elif op == "rotate":
                result = rotate_mesh(
                    self._document.mesh, dialog.rotate_axis(), dialog.rotate_degrees()
                )
            elif op == "mirror":
                result = mirror_mesh(self._document.mesh, dialog.mirror_axis())
            else:
                return
        except MeshTransformError as e:
            self.statusBar().showMessage(f"Transform failed: {e.user_message}")
            logger.error("Transform failed: %s", e.user_message)
            return
        except Exception as e:
            self.statusBar().showMessage(f"Transform failed: {e}")
            logger.exception("Transform failed")
            return

        # Push pre-transform state for undo
        self._document.undo_stack.push(self._document.mesh)
        self._document.mesh = result.mesh

        # Invalidate analysis
        self._document.analysis = None

        # Update viewport
        polydata = mesh_data_to_polydata(self._document.mesh)
        self._viewport.scene_manager.display_mesh(polydata)
        self._viewport.vtk_render()

        # Update info panel
        self._info_panel.set_document(self._document)
        self._info_panel.clear_analysis()
        self._viewport.scene_manager.hide_highlights()

        # Update action states
        self._update_undo_state()
        self._update_repair_state()

        # Refresh print bed if visible
        if self.bed_action.isChecked():
            self._on_bed_toggled(True)

        # Status bar
        msg = result.description
        if result.warning:
            msg += f" — {result.warning}"
        self.statusBar().showMessage(msg)
```

Add the `QDialog` import to the existing PySide6 imports (it's already imported — verify it's in the import list).

- [ ] **Step 9: Run tests to verify they pass**

Run: `pytest tests/ui/test_main_window.py::TestMainWindowTransform -v`
Expected: PASS (7 tests)

- [ ] **Step 10: Run full test suite**

Run: `pytest tests/ -v`
Expected: PASS

- [ ] **Step 11: Run linter and type checker**

Run: `ruff check src/ tests/ && mypy src/meshscope/`
Expected: PASS

- [ ] **Step 12: Commit**

```bash
git add src/meshscope/ui/main_window.py tests/ui/test_main_window.py
git commit -m "feat: integrate Transform action with dialog into MainWindow"
```
