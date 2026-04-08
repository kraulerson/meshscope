# Feature 7: Basic Mesh Repair — Design Spec

## Goal

Add one-click mesh repair that fixes common 3D printing issues (flipped normals, small holes, degenerate faces) with full undo/redo support. Non-destructive: the original mesh is always recoverable.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Repair trigger | One-click "Repair All" with summary dialog | Simple for 3D printing audience; avoids decision fatigue |
| Undo/Redo UI | Full: Edit menu + toolbar + Ctrl+Z/Ctrl+Shift+Z | Must be discoverable for geometry-modifying operations |
| Repair placement | Toolbar + View menu, shortcut R | Consistent with existing action pattern |
| Pre-repair dialog | Always shown, extra warning at >5% change | Transparency before geometry modification |
| Post-repair analysis | Auto re-analyze immediately | Closes feedback loop; user sees results instantly |

## Architecture

### New Files

- `src/meshscope/core/mesh_repair.py` — repair planning and execution
- `tests/unit/test_mesh_repair.py` — unit tests for repair logic

### Modified Files

- `src/meshscope/core/exceptions.py` — add `MeshRepairError`
- `src/meshscope/ui/main_window.py` — Repair action, Undo/Redo actions, Edit menu, handlers
- `tests/unit/test_main_window.py` or `tests/ui/test_main_window.py` — UI tests for new actions

## Data Types

```python
@dataclass(frozen=True)
class RepairPlan:
    flipped_normal_count: int
    holes_to_fill: int
    degenerate_faces_to_remove: int
    estimated_face_delta: int       # positive = added, negative = removed
    high_impact_warning: bool       # True if |delta| > 5% of original face count

@dataclass(frozen=True)
class RepairResult:
    mesh: MeshData
    normals_fixed: int
    holes_filled: int
    degenerate_faces_removed: int
    fully_repaired: bool            # False if some issues remain
    remaining_issues: str | None    # Description of unfixed issues
```

## Repair Logic (`mesh_repair.py`)

### `plan_repair(analysis: MeshAnalysis, mesh: MeshData) -> RepairPlan`

- Reads hole_count and degenerate_face_count from analysis
- For flipped normals: creates trimesh with `process=False`, calls `trimesh.repair.broken_faces()` or compares `fix_normals()` result to detect count (MeshAnalysis doesn't track flipped normals directly — this is a repair-specific check)
- Estimates face delta: degenerate removals decrease count, hole fills increase count
- Computes `high_impact_warning`: `|estimated_face_delta| / face_count > 0.05`
- Pure function (reads mesh data but doesn't modify it)

### `apply_repair(mesh: MeshData, plan: RepairPlan) -> RepairResult`

- Creates `trimesh.Trimesh` with `process=False`
- Applies operations in order:
  1. Remove degenerate faces (zero-area)
  2. Fix normals (consistent outward orientation)
  3. Fill holes (threshold: shortest bbox dimension / 10)
- Extracts new vertices, faces, normals arrays
- Recomputes MeshMetadata (bbox, surface area, volume, manifold)
- Creates new frozen MeshData
- Counts actual changes by comparing before/after state
- Returns RepairResult

**Failure handling:**
- All operations fail → raise `MeshRepairError` with user message
- Partial success → return `RepairResult(fully_repaired=False, remaining_issues="...")`
- Individual trimesh errors → catch, log, continue with remaining operations

## Undo/Redo UI

### Actions

- `undo_action`: Ctrl+Z, in Edit menu and toolbar
- `redo_action`: Ctrl+Shift+Z, in Edit menu and toolbar
- Both disabled by default; enabled/disabled via `_update_undo_state()` after each mesh-modifying operation

### Edit Menu

New menu inserted between File and View:
- Undo (Ctrl+Z)
- Redo (Ctrl+Shift+Z)

### Toolbar Placement

Undo and Redo after Open/Export group, separator before view actions.

### Handler Logic (`_on_undo`, `_on_redo`)

1. Pop mesh from undo/redo stack
2. Assign to `doc.mesh`
3. Rebuild VTK polydata, update viewport
4. Clear analysis (stale after mesh change)
5. Update info panel metadata
6. Update undo/redo and repair action enabled states
7. Status bar feedback

### State Reset

On file load: undo/redo disabled (fresh document, empty stack).

## Repair Action & MainWindow Integration

### Action Configuration

- Shortcut: R
- In View menu after Analyze
- In toolbar after Analyze
- Disabled by default
- Enabled when analysis exists AND has fixable issues: `hole_count > 0 or degenerate_face_count > 0 or open_edge_count > 0`

### `_on_repair()` Flow

1. Guard: return if no document or no analysis
2. `plan_repair(doc.analysis, doc.mesh)` → RepairPlan
3. Show confirmation dialog:
   - Title: "Repair Mesh"
   - Body: bullet list of planned actions
   - If `high_impact_warning`: "Warning: face count will change by X%. Review results carefully."
   - OK / Cancel
4. If cancelled → return
5. Push `doc.mesh` to undo stack
6. `apply_repair(doc.mesh, plan)` → RepairResult
7. Assign `result.mesh` to `doc.mesh`
8. Rebuild VTK polydata, update viewport
9. Auto re-analyze: `analyze_mesh(doc.mesh)`, update info panel
10. Update undo/redo state, update repair action state
11. Status bar:
    - Success: "Repair complete — N normals fixed, N holes filled, N degenerate faces removed"
    - Partial: "Repair partially complete — some issues remain. See analysis panel."
    - Re-show highlights if remaining issues
12. Exception: "Repair failed: {reason}. Original mesh unchanged." — no undo stack push

### No-Op Guard

If `apply_repair` returns zero changes across all counts, don't push to undo stack. Status bar: "No repairs needed — mesh is already clean."

## Error Handling

### New Exception

`MeshRepairError(Exception)` in `exceptions.py` with `user_message` attribute, following existing `MeshLoadError` / `MeshExportError` pattern.

### Edge Cases

| Case | Behavior |
|------|----------|
| Repair with no issues | Button disabled; guard clause returns early |
| Large mesh undo | Full snapshot stored; 10-entry ring buffer auto-evicts oldest |
| Repair changes nothing | No undo push; "No repairs needed" status message |
| File load after repair | Fresh MeshDocument; undo stack empty; all actions reset |
| Multiple repairs | Each is a separate undo entry; stack holds up to 10 |
| Repair after undo | Valid; user can undo, modify approach, re-repair |

## Accessibility

- Confirmation dialog: all text, no color-only indicators
- Warning uses "Warning:" text prefix, not just color
- Undo/Redo: standard Ctrl+Z / Ctrl+Shift+Z shortcuts
- Repair: R shortcut, consistent with single-key pattern (W, S, F, P, A)
- Dialog: standard OK/Cancel with keyboard focus on OK
- Status bar: full text descriptions of all outcomes

## Testing Strategy

### Unit Tests (`test_mesh_repair.py`)

- `plan_repair` with various analysis states (all issues, single issue, no issues)
- `plan_repair` high impact warning threshold
- `apply_repair` on mesh with known defects (open box, flipped normals, degenerate faces)
- `apply_repair` partial failure (holes too large)
- `apply_repair` no-op (clean mesh)
- Repair preserves vertex data integrity (no NaN, valid indices)

### UI Tests

- Repair action disabled with no mesh
- Repair action disabled with no analysis
- Repair action disabled when analysis shows no issues
- Repair action enabled when analysis shows issues
- Undo/redo action states after repair
- Undo/redo action states after file load
- Undo restores pre-repair mesh
- Redo re-applies repair

## Dependencies

- Feature 6 (Manifold Check): provides MeshAnalysis that drives repair
- UndoStack (`src/meshscope/core/undo_stack.py`): already implemented, first real usage
- trimesh 4.7.4: `fill_holes()`, `fix_normals()`, `remove_degenerate_faces()`
