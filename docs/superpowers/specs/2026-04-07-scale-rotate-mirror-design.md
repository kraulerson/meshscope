# Feature 8: Scale/Rotate/Mirror — Design Spec

**Date:** 2026-04-07
**Feature:** Scale/Rotate/Mirror transforms
**Status:** Approved

---

## Summary

Add uniform scale, axis rotation, and axis mirror transforms to meshscope. All transforms are undoable, update the viewport and info panel immediately, and are accessed through a single tabbed Transform dialog.

## Scope (MVP)

**In scope:**
- Uniform scale by factor (single numeric input)
- Rotate by degrees around one axis (X, Y, or Z), centered on model center of mass
- Mirror across one axis plane (YZ, XZ, or XY) through model center, with automatic face winding correction

**Out of scope (deferred):**
- Scale to target dimension ("set X = 100mm")
- Non-uniform scale per axis
- Combined/chained transforms in a single operation
- Real-time preview in viewport while dialog is open

## Architecture

### Core Module: `src/meshscope/core/mesh_transform.py`

Pure numpy transform functions. No trimesh dependency.

#### Functions

**`scale_mesh(mesh: MeshData, factor: float) -> TransformResult`**
- Multiply all vertex coordinates by `factor`
- Recompute metadata (bounding box, surface area, volume)
- Validation: factor <= 0 raises `MeshTransformError("Scale factor must be greater than zero.")`
- Warning: factor > 10000 sets `TransformResult.warning` with size advisory
- Surface area scales by factor², volume scales by factor³

**`rotate_mesh(mesh: MeshData, axis: str, degrees: float) -> TransformResult`**
- Build 3x3 rotation matrix for the given axis
- Compute model center of mass (mean of vertices)
- Translate vertices to origin, apply rotation, translate back
- Recompute face normals via cross products
- Recompute metadata
- Validation: axis must be "x", "y", or "z" (case-insensitive)

**`mirror_mesh(mesh: MeshData, axis: str) -> TransformResult`**
- Negate the selected coordinate axis on all vertices (centered on model center)
- Reverse face winding order (swap face columns 1 and 2) to maintain outward-facing normals
- Recompute face normals via cross products
- Recompute metadata
- Validation: axis must be "x", "y", or "z" (case-insensitive)

#### Helper

**`_recompute_metadata(vertices: ndarray, faces: ndarray) -> MeshMetadata`**
- Bounding box: min/max per axis
- Surface area: sum of cross-product magnitudes / 2 over all faces
- Volume: signed tetrahedron sum (only if manifold, else None)
- Manifold status: preserve `mesh.metadata.is_manifold` from input (transforms don't change topology). Volume computed only when `is_manifold` is True
- Vertex/face counts from array shapes

#### Data Types

**`TransformResult`** (frozen dataclass):
- `mesh: MeshData` — the transformed mesh
- `description: str` — human-readable summary (e.g., "Scaled by 2.5x")
- `warning: str | None` — optional advisory (e.g., extreme scale)

**`MeshTransformError`** in `exceptions.py`:
- Same pattern as `MeshRepairError`: `user_message` attribute, subclass of `Exception`

### UI: Transform Dialog — `src/meshscope/ui/transform_dialog.py`

A `QDialog` with three tabs (QTabWidget):

**Scale tab:**
- `QDoubleSpinBox` for scale factor (range: 0.001 to 100000, default 1.0, step 0.1)
- Read-only info panel showing current dimensions and after-scale dimensions (live update as factor changes)
- Current dimensions passed in from `MeshData.metadata.bounding_box`

**Rotate tab:**
- Three toggle-style `QPushButton` for axis (X, Y, Z) — exclusive selection
- `QDoubleSpinBox` for degrees (range: -3600 to 3600, default 90, step 90)

**Mirror tab:**
- Three toggle-style `QPushButton` for axis: "X (YZ plane)", "Y (XZ plane)", "Z (XY plane)" — exclusive selection

**Dialog return:**
- `exec()` returns `Accepted` or `Rejected`
- Accessor methods: `operation() -> str` (one of "scale", "rotate", "mirror"), `scale_factor() -> float`, `rotate_axis() -> str`, `rotate_degrees() -> float`, `mirror_axis() -> str`

### UI: MainWindow Integration

**Action:** `self.transform_action` — shortcut `Ctrl+T`, tooltip "Scale, rotate, or mirror mesh", disabled until mesh loaded.

**Menu:** Edit menu, after Undo/Redo with separator.

**Toolbar:** After Repair button.

**Handler `_on_transform()`:**
1. Open `TransformDialog` with current mesh bounding box
2. If rejected, return
3. Read operation type and parameters from dialog
4. Call the appropriate transform function
5. Push current mesh to undo stack: `self._document.undo_stack.push(self._document.mesh)`
6. Replace mesh: `self._document.mesh = result.mesh`
7. Update viewport: `mesh_data_to_polydata()` → `display_mesh()` → `vtk_render()`
8. Update info panel: `set_document()`
9. Invalidate analysis: `self._document.analysis = None`
10. Clear analysis UI: `self._info_panel.clear_analysis()`, hide highlights
11. Update action states: `_update_undo_state()`, `_update_repair_state()`
12. Refresh print bed if visible
13. Status bar: show `result.description`, append warning if present

**State management:**
- `_set_render_actions_enabled(True)` enables `transform_action`
- `_set_render_actions_enabled(False)` disables it

### Design Note (from Qdrant)

During Feature 3 brainstorming, the Orchestrator requested that Feature 8 include contextual help for unit conversion when scaling. This is **deferred** since the MVP only supports scale-by-factor (not scale-to-dimension). The unit conversion help will be added when scale-to-target-dimension is implemented in a future enhancement.

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/meshscope/core/mesh_transform.py` | TransformResult, scale/rotate/mirror functions |
| Create | `src/meshscope/ui/transform_dialog.py` | Tabbed QDialog for transform input |
| Create | `tests/unit/test_mesh_transform.py` | Unit tests for transform logic |
| Modify | `src/meshscope/core/exceptions.py` | Add MeshTransformError |
| Modify | `src/meshscope/ui/main_window.py` | Transform action, menu, toolbar, handler |
| Modify | `tests/ui/test_main_window.py` | UI tests for transform action |

## Testing

### Unit Tests (`tests/unit/test_mesh_transform.py`)

**Scale:**
- Factor 2x doubles vertex coordinates and bounding box
- Factor 0.5 halves them
- Factor <= 0 raises MeshTransformError
- Factor > 10000 returns warning
- Surface area scales by factor², volume by factor³

**Rotate:**
- 90° around Z swaps X/Y coordinates correctly
- 360° returns to original (within float tolerance)
- Normals recomputed correctly after rotation

**Mirror:**
- Mirror X negates X vertex coordinates
- Face winding reversed (columns 1 and 2 swapped)
- Mirror twice returns to original geometry
- Volume preserved (winding fix maintains sign)

**Metadata:**
- `_recompute_metadata` computes correct bounding box, surface area, counts
- Volume is None for non-manifold meshes

**TransformResult:**
- Frozen dataclass creation and access

### UI Tests (`tests/ui/test_main_window.py`)

- `transform_action` exists, disabled initially, enabled after load
- Shortcut is Ctrl+T
- Action in Edit menu and toolbar
- Disabled after load error
