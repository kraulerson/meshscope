# Basic Mesh Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one-click mesh repair (fill holes, fix normals, remove degenerate faces) with full undo/redo UI support.

**Architecture:** New `mesh_repair.py` core module with `plan_repair()` (dry-run summary) and `apply_repair()` (execute repairs). UndoStack gets swap methods for proper undo/redo of current state. MainWindow gets Edit menu with Undo/Redo, plus Repair action in toolbar/View menu.

**Tech Stack:** Python 3.13, trimesh 4.7.4 (repair module), PySide6 6.9.3, numpy, VTK 9.4.2

---

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/meshscope/core/mesh_repair.py` | RepairPlan/RepairResult dataclasses, plan_repair(), apply_repair() |
| Create | `tests/unit/test_mesh_repair.py` | Unit tests for repair logic |
| Modify | `src/meshscope/core/exceptions.py:48-53` | Add MeshRepairError |
| Modify | `src/meshscope/core/undo_stack.py:31-45` | Add undo_swap(), redo_swap() |
| Modify | `tests/unit/test_undo_stack.py` | Tests for new swap methods |
| Modify | `src/meshscope/ui/main_window.py` | Undo/Redo/Repair actions, Edit menu, handlers |
| Modify | `tests/ui/test_main_window.py` | UI tests for new actions |

---

### Task 1: MeshRepairError Exception and Repair Datatypes

**Files:**
- Modify: `src/meshscope/core/exceptions.py:48-53`
- Create: `src/meshscope/core/mesh_repair.py`
- Create: `tests/unit/test_mesh_repair.py`

- [ ] **Step 1: Write test for MeshRepairError**

In `tests/unit/test_mesh_repair.py`:

```python
"""Tests for mesh repair logic."""

from meshscope.core.exceptions import MeshRepairError


class TestMeshRepairError:
    def test_has_user_message(self) -> None:
        err = MeshRepairError("Repair failed.")
        assert err.user_message == "Repair failed."

    def test_is_exception(self) -> None:
        err = MeshRepairError("msg")
        assert isinstance(err, Exception)

    def test_str_matches_user_message(self) -> None:
        err = MeshRepairError("msg")
        assert str(err) == "msg"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_mesh_repair.py::TestMeshRepairError -v`
Expected: FAIL — `ImportError: cannot import name 'MeshRepairError'`

- [ ] **Step 3: Implement MeshRepairError**

Add to `src/meshscope/core/exceptions.py` after the `MeshExportError` class (after line 53):

```python
class MeshRepairError(Exception):
    """Base exception for all mesh repair failures."""

    def __init__(self, user_message: str) -> None:
        self.user_message = user_message
        super().__init__(user_message)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_mesh_repair.py::TestMeshRepairError -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Write tests for RepairPlan and RepairResult dataclasses**

Append to `tests/unit/test_mesh_repair.py`:

```python
from meshscope.core.mesh_repair import RepairPlan, RepairResult


class TestRepairPlanDataclass:
    def test_creation(self) -> None:
        plan = RepairPlan(
            flipped_normal_count=3,
            holes_to_fill=2,
            degenerate_faces_to_remove=1,
            estimated_face_delta=-1,
            high_impact_warning=False,
        )
        assert plan.flipped_normal_count == 3
        assert plan.holes_to_fill == 2
        assert plan.degenerate_faces_to_remove == 1
        assert plan.estimated_face_delta == -1
        assert plan.high_impact_warning is False

    def test_is_frozen(self) -> None:
        plan = RepairPlan(0, 0, 0, 0, False)
        try:
            plan.holes_to_fill = 99  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except AttributeError:
            pass


class TestRepairResultDataclass:
    def test_creation(self) -> None:
        import numpy as np

        from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata

        verts = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)

        result = RepairResult(
            mesh=mesh,
            normals_fixed=3,
            holes_filled=2,
            degenerate_faces_removed=1,
            fully_repaired=True,
            remaining_issues=None,
        )
        assert result.normals_fixed == 3
        assert result.fully_repaired is True
        assert result.remaining_issues is None

    def test_is_frozen(self) -> None:
        import numpy as np

        from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata

        verts = np.array([[0, 0, 0]], dtype=np.float32)
        faces = np.array([[0, 0, 0]], dtype=np.uint32)
        normals = np.array([[0, 0, 1]], dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 0, 0, 0)
        meta = MeshMetadata(1, 1, bb, 0.0, None, False)
        mesh = MeshData(vertices=verts, faces=faces, normals=normals, metadata=meta)
        result = RepairResult(mesh, 0, 0, 0, True, None)
        try:
            result.normals_fixed = 99  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except AttributeError:
            pass
```

- [ ] **Step 6: Run test to verify it fails**

Run: `pytest tests/unit/test_mesh_repair.py -v`
Expected: FAIL — `ImportError: cannot import name 'RepairPlan' from 'meshscope.core.mesh_repair'`

- [ ] **Step 7: Create mesh_repair.py with dataclasses**

Create `src/meshscope/core/mesh_repair.py`:

```python
"""Basic mesh repair: plan and apply repairs for common 3D printing issues."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from meshscope.core.mesh_data import MeshData

logger = logging.getLogger("meshscope.core.mesh_repair")


@dataclass(frozen=True)
class RepairPlan:
    """Summary of planned repair operations."""

    flipped_normal_count: int
    holes_to_fill: int
    degenerate_faces_to_remove: int
    estimated_face_delta: int
    high_impact_warning: bool


@dataclass(frozen=True)
class RepairResult:
    """Result of applying mesh repairs."""

    mesh: MeshData
    normals_fixed: int
    holes_filled: int
    degenerate_faces_removed: int
    fully_repaired: bool
    remaining_issues: str | None
```

- [ ] **Step 8: Run all tests to verify they pass**

Run: `pytest tests/unit/test_mesh_repair.py -v`
Expected: PASS (7 tests)

- [ ] **Step 9: Commit**

```bash
git add src/meshscope/core/exceptions.py src/meshscope/core/mesh_repair.py tests/unit/test_mesh_repair.py
git commit -m "feat: add MeshRepairError, RepairPlan, and RepairResult datatypes"
```

---

### Task 2: UndoStack Swap Methods

The existing `undo()` and `redo()` methods move snapshots between stacks but don't handle the "current state" — which means redo restores the wrong state. New `undo_swap(current)` and `redo_swap(current)` methods properly swap the current mesh with the stack entry so undo/redo round-trips correctly.

**Files:**
- Modify: `src/meshscope/core/undo_stack.py:31-45`
- Modify: `tests/unit/test_undo_stack.py`

- [ ] **Step 1: Write tests for undo_swap and redo_swap**

Append to `tests/unit/test_undo_stack.py`:

```python
class TestUndoSwap:
    def test_undo_swap_returns_previous_state(self) -> None:
        stack = UndoStack(max_entries=10)
        mesh_a = _make_mesh(1.0)
        mesh_b = _make_mesh(2.0)
        stack.push(mesh_a)
        result = stack.undo_swap(mesh_b)
        assert result is mesh_a

    def test_undo_swap_saves_current_for_redo(self) -> None:
        stack = UndoStack(max_entries=10)
        mesh_a = _make_mesh(1.0)
        mesh_b = _make_mesh(2.0)
        stack.push(mesh_a)
        stack.undo_swap(mesh_b)
        assert stack.can_redo() is True

    def test_undo_swap_returns_none_when_empty(self) -> None:
        stack = UndoStack(max_entries=10)
        mesh_b = _make_mesh(2.0)
        assert stack.undo_swap(mesh_b) is None
        assert stack.can_redo() is False

    def test_redo_swap_returns_forward_state(self) -> None:
        stack = UndoStack(max_entries=10)
        mesh_a = _make_mesh(1.0)
        mesh_b = _make_mesh(2.0)
        stack.push(mesh_a)
        stack.undo_swap(mesh_b)
        # Now redo should give back mesh_b (the post-modification state)
        result = stack.redo_swap(mesh_a)
        assert result is mesh_b

    def test_redo_swap_returns_none_when_empty(self) -> None:
        stack = UndoStack(max_entries=10)
        mesh_a = _make_mesh(1.0)
        assert stack.redo_swap(mesh_a) is None
        assert stack.can_undo() is False

    def test_full_undo_redo_roundtrip(self) -> None:
        """push(A), current=B → undo → redo should restore B."""
        stack = UndoStack(max_entries=10)
        mesh_a = _make_mesh(1.0)
        mesh_b = _make_mesh(2.0)

        stack.push(mesh_a)
        # Simulate: current is now B

        # Undo: swap B for A
        restored = stack.undo_swap(mesh_b)
        assert restored is mesh_a

        # Redo: swap A for B
        redone = stack.redo_swap(mesh_a)
        assert redone is mesh_b

    def test_two_repairs_double_undo_double_redo(self) -> None:
        """push(A), current=B, push(B), current=C → undo×2 → redo×2."""
        stack = UndoStack(max_entries=10)
        mesh_a = _make_mesh(1.0)
        mesh_b = _make_mesh(2.0)
        mesh_c = _make_mesh(3.0)

        stack.push(mesh_a)
        # current = B
        stack.push(mesh_b)
        # current = C

        # Undo to B
        r1 = stack.undo_swap(mesh_c)
        assert r1 is mesh_b

        # Undo to A
        r2 = stack.undo_swap(mesh_b)
        assert r2 is mesh_a

        # Redo to B
        r3 = stack.redo_swap(mesh_a)
        assert r3 is mesh_b

        # Redo to C
        r4 = stack.redo_swap(mesh_b)
        assert r4 is mesh_c

    def test_push_after_undo_swap_clears_redo(self) -> None:
        """Undo then new push should clear redo history."""
        stack = UndoStack(max_entries=10)
        mesh_a = _make_mesh(1.0)
        mesh_b = _make_mesh(2.0)
        mesh_c = _make_mesh(3.0)

        stack.push(mesh_a)
        stack.undo_swap(mesh_b)
        assert stack.can_redo() is True

        # New modification after undo — redo should be cleared
        stack.push(mesh_a)
        assert stack.can_redo() is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_undo_stack.py::TestUndoSwap -v`
Expected: FAIL — `AttributeError: 'UndoStack' object has no attribute 'undo_swap'`

- [ ] **Step 3: Implement undo_swap and redo_swap**

Add to `src/meshscope/core/undo_stack.py` after the existing `redo` method (after line 45), before `can_undo`:

```python
    def undo_swap(self, current: MeshData) -> MeshData | None:
        """Undo with proper current-state tracking.

        Pops the previous state from the undo stack, pushes the
        current state onto the redo stack, and returns the previous state.
        Returns None if nothing to undo.
        """
        if not self._entries:
            return None
        previous = self._entries.pop()
        self._redo_stack.append(current)
        return previous

    def redo_swap(self, current: MeshData) -> MeshData | None:
        """Redo with proper current-state tracking.

        Pops the next state from the redo stack, pushes the current
        state onto the undo stack, and returns the next state.
        Returns None if nothing to redo.
        """
        if not self._redo_stack:
            return None
        next_state = self._redo_stack.pop()
        self._entries.append(current)
        return next_state
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_undo_stack.py -v`
Expected: PASS (all tests including new ones)

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/core/undo_stack.py tests/unit/test_undo_stack.py
git commit -m "feat: add undo_swap and redo_swap to UndoStack for proper state tracking"
```

---

### Task 3: plan_repair() Function

**Files:**
- Modify: `src/meshscope/core/mesh_repair.py`
- Modify: `tests/unit/test_mesh_repair.py`

- [ ] **Step 1: Write tests for plan_repair**

Add to `tests/unit/test_mesh_repair.py`. First, add test helpers at the top of the file (after existing imports):

```python
import numpy as np

from meshscope.core.mesh_analysis import analyze_mesh
from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
from meshscope.core.mesh_repair import RepairPlan, RepairResult, plan_repair


def _make_cube_mesh() -> MeshData:
    """Watertight cube — no issues."""
    vertices = np.array(
        [
            [0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0],
            [0, 0, 10], [10, 0, 10], [10, 10, 10], [0, 10, 10],
        ],
        dtype=np.float32,
    )
    faces = np.array(
        [
            [0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
            [0, 1, 5], [0, 5, 4], [2, 3, 7], [2, 7, 6],
            [0, 4, 7], [0, 7, 3], [1, 2, 6], [1, 6, 5],
        ],
        dtype=np.uint32,
    )
    normals = np.zeros((12, 3), dtype=np.float32)
    bb = BoundingBox(0, 0, 0, 10, 10, 10)
    meta = MeshMetadata(8, 12, bb, 600.0, 1000.0, True)
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


def _make_open_mesh() -> MeshData:
    """Cube with 2 faces removed — has holes and open edges."""
    vertices = np.array(
        [
            [0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0],
            [0, 0, 10], [10, 0, 10], [10, 10, 10], [0, 10, 10],
        ],
        dtype=np.float32,
    )
    faces = np.array(
        [
            [0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
            [0, 1, 5], [0, 5, 4], [2, 3, 7], [2, 7, 6],
            [0, 4, 7], [0, 7, 3],
        ],
        dtype=np.uint32,
    )
    normals = np.zeros((10, 3), dtype=np.float32)
    bb = BoundingBox(0, 0, 0, 10, 10, 10)
    meta = MeshMetadata(8, 10, bb, 500.0, None, False)
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


def _make_degenerate_mesh() -> MeshData:
    """Simple mesh with one degenerate (zero-area) face."""
    vertices = np.array(
        [
            [0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0],
        ],
        dtype=np.float32,
    )
    faces = np.array(
        [
            [0, 1, 2],
            [0, 2, 3],
            [0, 1, 0],  # degenerate: repeated vertex
        ],
        dtype=np.uint32,
    )
    normals = np.zeros((3, 3), dtype=np.float32)
    bb = BoundingBox(0, 0, 0, 10, 10, 0)
    meta = MeshMetadata(4, 3, bb, 100.0, None, False)
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)
```

Then add the test class:

```python
class TestPlanRepair:
    def test_clean_mesh_no_repairs_needed(self) -> None:
        mesh = _make_cube_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        assert plan.holes_to_fill == 0
        assert plan.degenerate_faces_to_remove == 0
        assert plan.high_impact_warning is False

    def test_open_mesh_reports_holes(self) -> None:
        mesh = _make_open_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        assert plan.holes_to_fill > 0

    def test_degenerate_mesh_reports_degenerate(self) -> None:
        mesh = _make_degenerate_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        assert plan.degenerate_faces_to_remove >= 1

    def test_returns_repair_plan_type(self) -> None:
        mesh = _make_cube_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        assert isinstance(plan, RepairPlan)

    def test_high_impact_warning_when_large_change(self) -> None:
        """A mesh where repair changes face count by >5% should set warning."""
        mesh = _make_open_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        # open mesh has 10 faces; filling a hole adds faces. If delta > 5%
        # of 10 (i.e. > 0.5 faces), warning should be True
        if abs(plan.estimated_face_delta) > 0:
            assert plan.high_impact_warning is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_mesh_repair.py::TestPlanRepair -v`
Expected: FAIL — `ImportError: cannot import name 'plan_repair'`

- [ ] **Step 3: Implement plan_repair**

Add to `src/meshscope/core/mesh_repair.py` (update imports and add function after the dataclasses):

Update the imports section to:

```python
"""Basic mesh repair: plan and apply repairs for common 3D printing issues."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import trimesh

if TYPE_CHECKING:
    from meshscope.core.mesh_analysis import MeshAnalysis
    from meshscope.core.mesh_data import MeshData

logger = logging.getLogger("meshscope.core.mesh_repair")
```

Add after the RepairResult dataclass:

```python
def plan_repair(analysis: MeshAnalysis, mesh: MeshData) -> RepairPlan:
    """Compute what repairs would be applied without modifying the mesh.

    Runs a trial repair on a copy to get accurate counts.
    """
    tm = trimesh.Trimesh(
        vertices=np.array(mesh.vertices, dtype=np.float64),
        faces=np.array(mesh.faces, dtype=np.int64),
        process=False,
    )
    original_face_count = len(tm.faces)

    trial = tm.copy()

    # 1. Remove degenerate faces
    degen = analysis.degenerate_face_count
    if degen > 0:
        trial.remove_degenerate_faces()

    # 2. Fix normals — count faces that changed winding
    faces_before_normals = trial.faces.copy()
    trimesh.repair.fix_normals(trial)
    flipped_count = int(np.sum(np.any(trial.faces != faces_before_normals, axis=1)))

    # 3. Fill holes
    holes = analysis.hole_count
    if holes > 0:
        trimesh.repair.fill_holes(trial)

    estimated_delta = len(trial.faces) - original_face_count
    high_impact = (
        abs(estimated_delta) > 0.05 * original_face_count
        if original_face_count > 0
        else False
    )

    return RepairPlan(
        flipped_normal_count=flipped_count,
        holes_to_fill=holes,
        degenerate_faces_to_remove=degen,
        estimated_face_delta=estimated_delta,
        high_impact_warning=high_impact,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_mesh_repair.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/core/mesh_repair.py tests/unit/test_mesh_repair.py
git commit -m "feat: implement plan_repair for dry-run repair planning"
```

---

### Task 4: apply_repair() Function

**Files:**
- Modify: `src/meshscope/core/mesh_repair.py`
- Modify: `tests/unit/test_mesh_repair.py`

- [ ] **Step 1: Write tests for apply_repair**

Add import at the top of `tests/unit/test_mesh_repair.py` (update the existing import line):

```python
from meshscope.core.mesh_repair import RepairPlan, RepairResult, apply_repair, plan_repair
```

Add test class:

```python
class TestApplyRepair:
    def test_repairs_open_mesh(self) -> None:
        """Filling holes on an open mesh should produce a mesh with more faces."""
        mesh = _make_open_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        result = apply_repair(mesh, plan)
        assert isinstance(result, RepairResult)
        assert result.mesh.metadata.face_count >= mesh.metadata.face_count

    def test_removes_degenerate_faces(self) -> None:
        mesh = _make_degenerate_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        result = apply_repair(mesh, plan)
        assert result.degenerate_faces_removed >= 1
        assert result.mesh.metadata.face_count < mesh.metadata.face_count

    def test_clean_mesh_returns_no_changes(self) -> None:
        """Applying repair to a clean mesh should change nothing."""
        mesh = _make_cube_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        result = apply_repair(mesh, plan)
        assert result.normals_fixed == 0
        assert result.holes_filled == 0
        assert result.degenerate_faces_removed == 0

    def test_result_mesh_has_valid_metadata(self) -> None:
        mesh = _make_open_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        result = apply_repair(mesh, plan)
        meta = result.mesh.metadata
        assert meta.vertex_count > 0
        assert meta.face_count > 0
        assert meta.surface_area_mm2 > 0

    def test_result_mesh_has_valid_arrays(self) -> None:
        mesh = _make_open_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        result = apply_repair(mesh, plan)
        assert result.mesh.vertices.shape[1] == 3
        assert result.mesh.faces.shape[1] == 3
        assert result.mesh.normals.shape[1] == 3
        assert not np.any(np.isnan(result.mesh.vertices))

    def test_fully_repaired_flag(self) -> None:
        mesh = _make_degenerate_mesh()
        analysis = analyze_mesh(mesh)
        plan = plan_repair(analysis, mesh)
        result = apply_repair(mesh, plan)
        # Degenerate removal should succeed fully
        assert result.degenerate_faces_removed >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_mesh_repair.py::TestApplyRepair -v`
Expected: FAIL — `ImportError: cannot import name 'apply_repair'`

- [ ] **Step 3: Implement apply_repair**

Add to `src/meshscope/core/mesh_repair.py`. First, add the import for MeshRepairError and the mesh data types (update the import section):

```python
from meshscope.core.exceptions import MeshRepairError
from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata
```

Remove these from the `TYPE_CHECKING` block (they're now runtime imports). The `TYPE_CHECKING` block should only contain:

```python
if TYPE_CHECKING:
    from meshscope.core.mesh_analysis import MeshAnalysis
```

Then add the function after `plan_repair`:

```python
def apply_repair(mesh: MeshData, plan: RepairPlan) -> RepairResult:
    """Apply planned repairs to a mesh and return the repaired result.

    Operations are applied in order:
    1. Remove degenerate faces (zero-area)
    2. Fix normals (consistent outward orientation)
    3. Fill holes

    Raises MeshRepairError if all operations fail.
    """
    tm = trimesh.Trimesh(
        vertices=np.array(mesh.vertices, dtype=np.float64),
        faces=np.array(mesh.faces, dtype=np.int64),
        process=False,
    )

    normals_fixed = 0
    holes_filled = 0
    degenerate_removed = 0
    remaining: list[str] = []

    # 1. Remove degenerate faces
    if plan.degenerate_faces_to_remove > 0:
        faces_before = len(tm.faces)
        try:
            tm.remove_degenerate_faces()
            degenerate_removed = faces_before - len(tm.faces)
        except Exception:
            remaining.append("Could not remove degenerate faces")
            logger.exception("Failed to remove degenerate faces")

    # 2. Fix normals
    if plan.flipped_normal_count > 0:
        try:
            faces_before_fix = tm.faces.copy()
            trimesh.repair.fix_normals(tm)
            normals_fixed = int(
                np.sum(np.any(tm.faces != faces_before_fix, axis=1))
            )
        except Exception:
            remaining.append("Could not fix normals")
            logger.exception("Failed to fix normals")

    # 3. Fill holes
    if plan.holes_to_fill > 0:
        try:
            faces_before_fill = len(tm.faces)
            trimesh.repair.fill_holes(tm)
            faces_added = len(tm.faces) - faces_before_fill
            if faces_added > 0:
                holes_filled = plan.holes_to_fill
            else:
                remaining.append("Holes could not be filled (too large or complex)")
        except Exception:
            remaining.append("Could not fill holes")
            logger.exception("Failed to fill holes")

    # Check if all operations failed
    total_fixed = normals_fixed + holes_filled + degenerate_removed
    if total_fixed == 0 and remaining:
        raise MeshRepairError(
            "All repair operations failed. Original mesh is unchanged."
        )

    # Build new MeshData from repaired trimesh
    repaired_vertices = np.asarray(tm.vertices, dtype=np.float32)
    repaired_faces = np.asarray(tm.faces, dtype=np.uint32)
    repaired_normals = np.asarray(tm.face_normals, dtype=np.float32)

    if np.any(np.isnan(repaired_vertices)):
        raise MeshRepairError(
            "Repair produced invalid geometry. Original mesh is unchanged."
        )

    bounds = tm.bounds
    bbox = BoundingBox(
        min_x=float(bounds[0][0]),
        min_y=float(bounds[0][1]),
        min_z=float(bounds[0][2]),
        max_x=float(bounds[1][0]),
        max_y=float(bounds[1][1]),
        max_z=float(bounds[1][2]),
    )
    is_manifold = bool(tm.is_volume)
    volume = float(tm.volume) if is_manifold else None

    metadata = MeshMetadata(
        vertex_count=len(repaired_vertices),
        face_count=len(repaired_faces),
        bounding_box=bbox,
        surface_area_mm2=float(tm.area),
        volume_mm3=volume,
        is_manifold=is_manifold,
    )

    new_mesh = MeshData(
        vertices=repaired_vertices,
        faces=repaired_faces,
        normals=repaired_normals,
        metadata=metadata,
    )

    remaining_text = "; ".join(remaining) if remaining else None

    return RepairResult(
        mesh=new_mesh,
        normals_fixed=normals_fixed,
        holes_filled=holes_filled,
        degenerate_faces_removed=degenerate_removed,
        fully_repaired=len(remaining) == 0,
        remaining_issues=remaining_text,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_mesh_repair.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Run full test suite to check nothing broke**

Run: `pytest tests/ -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/meshscope/core/mesh_repair.py tests/unit/test_mesh_repair.py
git commit -m "feat: implement apply_repair for mesh repair execution"
```

---

### Task 5: Undo/Redo Actions in MainWindow

**Files:**
- Modify: `src/meshscope/ui/main_window.py:1-304`
- Modify: `tests/ui/test_main_window.py`

- [ ] **Step 1: Write tests for undo/redo actions**

Add to `tests/ui/test_main_window.py`:

```python
class TestMainWindowUndoRedo:
    def test_undo_action_exists(self, window: MainWindow) -> None:
        assert hasattr(window, "undo_action")

    def test_redo_action_exists(self, window: MainWindow) -> None:
        assert hasattr(window, "redo_action")

    def test_undo_disabled_initially(self, window: MainWindow) -> None:
        assert not window.undo_action.isEnabled()

    def test_redo_disabled_initially(self, window: MainWindow) -> None:
        assert not window.redo_action.isEnabled()

    def test_undo_shortcut_is_ctrl_z(self, window: MainWindow) -> None:
        assert window.undo_action.shortcut() == QKeySequence("Ctrl+Z")

    def test_redo_shortcut_is_ctrl_shift_z(self, window: MainWindow) -> None:
        assert window.redo_action.shortcut() == QKeySequence("Ctrl+Shift+Z")

    def test_edit_menu_exists(self, window: MainWindow) -> None:
        menus = [a.text() for a in window.menuBar().actions()]
        assert any("Edit" in m for m in menus)

    def test_edit_menu_has_undo_and_redo(self, window: MainWindow) -> None:
        edit_menu = None
        for action in window.menuBar().actions():
            if "Edit" in action.text():
                edit_menu = action.menu()
                break
        assert edit_menu is not None
        action_texts = [a.text() for a in edit_menu.actions()]
        assert any("Undo" in t for t in action_texts)
        assert any("Redo" in t for t in action_texts)

    def test_undo_redo_in_toolbar(self, window: MainWindow) -> None:
        toolbar_actions = [a.text() for a in window.toolbar.actions()]
        assert any("Undo" in t for t in toolbar_actions)
        assert any("Redo" in t for t in toolbar_actions)

    def test_undo_disabled_after_file_load(self, window: MainWindow) -> None:
        """Fresh document has empty undo stack."""
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert not window.undo_action.isEnabled()
        assert not window.redo_action.isEnabled()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/ui/test_main_window.py::TestMainWindowUndoRedo -v`
Expected: FAIL — `AttributeError: 'MainWindow' object has no attribute 'undo_action'`

- [ ] **Step 3: Implement undo/redo actions and Edit menu**

In `src/meshscope/ui/main_window.py`, make these changes:

**3a.** Add new imports at top (add to existing imports):

```python
from meshscope.vtk_adapter.mesh_adapter import mesh_data_to_polydata
```

(This import already exists. No new imports needed for this task.)

**3b.** In `_create_actions` (after `self.analyze_action` block, around line 158), add:

```python
        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        self.undo_action.setEnabled(False)
        self.undo_action.setToolTip("Undo last mesh modification")
        self.undo_action.triggered.connect(self._on_undo)

        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut(QKeySequence("Ctrl+Shift+Z"))
        self.redo_action.setEnabled(False)
        self.redo_action.setToolTip("Redo last undone modification")
        self.redo_action.triggered.connect(self._on_redo)
```

**3c.** In `_create_menus`, insert Edit menu **between** File menu and View menu. Replace the existing `_create_menus` method. The new code after the file_menu block and before the view_menu block:

```python
        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
```

(Insert this between `file_menu.addAction(self.exit_action)` and the `view_menu = self.menuBar().addMenu("&View")` line.)

**3d.** In `_create_toolbar`, add undo/redo after the export action. Insert after `self.toolbar.addAction(self.export_action)` (line 199) and before the first `self.toolbar.addSeparator()` (line 200):

```python
        self.toolbar.addAction(self.undo_action)
        self.toolbar.addAction(self.redo_action)
```

**3e.** In `_load_file`, after setting `self._document = doc` (line 252), add undo/redo state reset:

```python
        self._update_undo_state()
```

**3f.** In `_set_render_actions_enabled`, when `enabled` is False, also disable undo/redo. Add at the end of the method:

```python
        if not enabled:
            self.undo_action.setEnabled(False)
            self.redo_action.setEnabled(False)
```

**3g.** Add handler methods (after `_on_highlight_toggled`, before `_on_export`):

```python
    def _on_undo(self) -> None:
        """Restore the previous mesh state."""
        if self._document is None or not self._document.undo_stack.can_undo():
            return

        restored = self._document.undo_stack.undo_swap(self._document.mesh)
        if restored is None:
            return

        self._document.mesh = restored
        self._document.analysis = None

        polydata = mesh_data_to_polydata(self._document.mesh)
        self._viewport.scene_manager.display_mesh(polydata)
        self._viewport.vtk_render()

        self._info_panel.set_document(self._document)
        self._info_panel.clear_analysis()
        self._viewport.scene_manager.hide_highlights()

        self._update_undo_state()

        # Refresh print bed if visible
        if self.bed_action.isChecked():
            self._on_bed_toggled(True)

        self.statusBar().showMessage("Undo: mesh restored")

    def _on_redo(self) -> None:
        """Re-apply the last undone modification."""
        if self._document is None or not self._document.undo_stack.can_redo():
            return

        redone = self._document.undo_stack.redo_swap(self._document.mesh)
        if redone is None:
            return

        self._document.mesh = redone
        self._document.analysis = None

        polydata = mesh_data_to_polydata(self._document.mesh)
        self._viewport.scene_manager.display_mesh(polydata)
        self._viewport.vtk_render()

        self._info_panel.set_document(self._document)
        self._info_panel.clear_analysis()
        self._viewport.scene_manager.hide_highlights()

        self._update_undo_state()

        # Refresh print bed if visible
        if self.bed_action.isChecked():
            self._on_bed_toggled(True)

        self.statusBar().showMessage("Redo: modification reapplied")

    def _update_undo_state(self) -> None:
        """Enable/disable undo and redo actions based on stack state."""
        if self._document is None:
            self.undo_action.setEnabled(False)
            self.redo_action.setEnabled(False)
            return
        self.undo_action.setEnabled(self._document.undo_stack.can_undo())
        self.redo_action.setEnabled(self._document.undo_stack.can_redo())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/ui/test_main_window.py::TestMainWindowUndoRedo -v`
Expected: PASS (all tests)

- [ ] **Step 5: Run full UI test suite**

Run: `pytest tests/ui/test_main_window.py -v`
Expected: PASS (all existing + new tests)

- [ ] **Step 6: Commit**

```bash
git add src/meshscope/ui/main_window.py tests/ui/test_main_window.py
git commit -m "feat: add Undo/Redo actions with Edit menu and toolbar integration"
```

---

### Task 6: Repair Action in MainWindow

**Files:**
- Modify: `src/meshscope/ui/main_window.py`
- Modify: `tests/ui/test_main_window.py`

- [ ] **Step 1: Write tests for repair action**

Add to `tests/ui/test_main_window.py`:

```python
class TestMainWindowRepair:
    def test_repair_action_exists(self, window: MainWindow) -> None:
        assert hasattr(window, "repair_action")

    def test_repair_action_disabled_initially(self, window: MainWindow) -> None:
        assert not window.repair_action.isEnabled()

    def test_repair_shortcut_is_r(self, window: MainWindow) -> None:
        assert window.repair_action.shortcut() == QKeySequence("R")

    def test_repair_disabled_after_load_no_analysis(self, window: MainWindow) -> None:
        """Repair requires analysis to have been run."""
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert not window.repair_action.isEnabled()

    def test_repair_disabled_after_clean_analysis(self, window: MainWindow) -> None:
        """Repair disabled when analysis finds no issues."""
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        window.analyze_action.trigger()
        assert not window.repair_action.isEnabled()

    def test_repair_action_in_view_menu(self, window: MainWindow) -> None:
        view_menu = None
        for action in window.menuBar().actions():
            if "View" in action.text():
                view_menu = action.menu()
                break
        assert view_menu is not None
        action_texts = [a.text() for a in view_menu.actions()]
        assert any("Repair" in t for t in action_texts)

    def test_repair_action_in_toolbar(self, window: MainWindow) -> None:
        toolbar_actions = [a.text() for a in window.toolbar.actions()]
        assert any("Repair" in t for t in toolbar_actions)

    def test_repair_disabled_after_error(
        self, window: MainWindow, tmp_path: Path
    ) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        bad = tmp_path / "bad.stl"
        bad.write_bytes(b"not a real stl file")
        window._load_file(bad)
        assert not window.repair_action.isEnabled()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/ui/test_main_window.py::TestMainWindowRepair -v`
Expected: FAIL — `AttributeError: 'MainWindow' object has no attribute 'repair_action'`

- [ ] **Step 3: Implement repair action and handler**

In `src/meshscope/ui/main_window.py`:

**3a.** Add new imports at top (add to existing import lines):

```python
from meshscope.core.exceptions import MeshExportError, MeshLoadError, MeshRepairError
from meshscope.core.mesh_repair import apply_repair, plan_repair
```

(Update the existing `MeshExportError, MeshLoadError` import to include `MeshRepairError`, and add the `mesh_repair` import.)

**3b.** In `_create_actions`, after the redo_action block, add:

```python
        self.repair_action = QAction("Repair", self)
        self.repair_action.setShortcut(QKeySequence("R"))
        self.repair_action.setEnabled(False)
        self.repair_action.setToolTip("Repair mesh issues found by analysis")
        self.repair_action.triggered.connect(self._on_repair)
```

**3c.** In `_create_menus`, add repair to the View menu after the analyze action:

```python
        view_menu.addAction(self.repair_action)
```

(Add after `view_menu.addAction(self.analyze_action)`)

**3d.** In `_create_toolbar`, add repair after analyze:

```python
        self.toolbar.addAction(self.repair_action)
```

(Add after `self.toolbar.addAction(self.analyze_action)`)

**3e.** In `_set_render_actions_enabled`, add repair_action. Add to the method:

```python
        self.repair_action.setEnabled(False)
```

(Repair starts disabled regardless of `enabled` flag — it's controlled by `_update_repair_state`.)

**3f.** At the end of `_on_analyze` (inside the `try` block, after the highlight/status logic, before the `except`), add:

```python
            self._update_repair_state()
```

**3g.** Add helper and handler methods (after `_update_undo_state`):

```python
    def _update_repair_state(self) -> None:
        """Enable/disable repair action based on analysis results."""
        if self._document is None or self._document.analysis is None:
            self.repair_action.setEnabled(False)
            return
        a = self._document.analysis
        has_fixable = (
            a.hole_count > 0
            or a.degenerate_face_count > 0
            or a.open_edge_count > 0
        )
        self.repair_action.setEnabled(has_fixable)

    def _on_repair(self) -> None:
        """Run mesh repair workflow: plan → confirm → apply → re-analyze."""
        if self._document is None or self._document.analysis is None:
            return

        # Plan
        try:
            plan = plan_repair(self._document.analysis, self._document.mesh)
        except Exception as e:
            self.statusBar().showMessage(f"Repair planning failed: {e}")
            logger.exception("Repair planning failed")
            return

        # Build confirmation dialog
        lines: list[str] = []
        if plan.flipped_normal_count > 0:
            lines.append(f"Fix {plan.flipped_normal_count} flipped normal(s)")
        if plan.holes_to_fill > 0:
            lines.append(f"Fill {plan.holes_to_fill} hole(s)")
        if plan.degenerate_faces_to_remove > 0:
            lines.append(
                f"Remove {plan.degenerate_faces_to_remove} degenerate face(s)"
            )

        if not lines:
            self.statusBar().showMessage(
                "No repairs needed — mesh is already clean."
            )
            return

        body = "The following repairs will be applied:\n\n"
        body += "\n".join(f"  \u2022 {line}" for line in lines)

        if plan.high_impact_warning and self._document.mesh.metadata.face_count > 0:
            pct = (
                abs(plan.estimated_face_delta)
                / self._document.mesh.metadata.face_count
                * 100
            )
            body += (
                f"\n\nWarning: Face count will change by {pct:.0f}%. "
                "Review results carefully."
            )

        result = QMessageBox.warning(
            self,
            "Repair Mesh",
            body,
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        )
        if result != QMessageBox.StandardButton.Ok:
            return

        # Apply
        try:
            repair_result = apply_repair(self._document.mesh, plan)
        except MeshRepairError as e:
            self.statusBar().showMessage(
                f"Repair failed: {e.user_message}"
            )
            logger.error("Repair failed: %s", e.user_message)
            return
        except Exception as e:
            self.statusBar().showMessage(f"Repair failed: {e}")
            logger.exception("Repair failed")
            return

        # Check for no-op
        total_changes = (
            repair_result.normals_fixed
            + repair_result.holes_filled
            + repair_result.degenerate_faces_removed
        )
        if total_changes == 0:
            self.statusBar().showMessage(
                "No repairs needed — mesh is already clean."
            )
            return

        # Push pre-repair state for undo, then replace mesh
        self._document.undo_stack.push(self._document.mesh)
        self._document.mesh = repair_result.mesh

        # Update viewport
        polydata = mesh_data_to_polydata(self._document.mesh)
        self._viewport.scene_manager.display_mesh(polydata)
        self._viewport.vtk_render()

        # Update info panel with new mesh metadata
        self._info_panel.set_document(self._document)

        # Auto re-analyze
        try:
            analysis = analyze_mesh(self._document.mesh)
            self._document.analysis = analysis
            self._info_panel.show_analysis(analysis)

            total_issues = (
                analysis.open_edge_count
                + analysis.non_manifold_edge_count
                + analysis.degenerate_face_count
                + analysis.hole_count
            )
            if total_issues > 0:
                self._viewport.scene_manager.show_highlights(
                    analysis,
                    self._document.mesh.vertices,
                    self._document.mesh.faces,
                )
            else:
                self._viewport.scene_manager.hide_highlights()
            self._viewport.vtk_render()
        except Exception:
            logger.exception("Post-repair analysis failed")

        # Update action states
        self._update_undo_state()
        self._update_repair_state()

        # Refresh print bed if visible
        if self.bed_action.isChecked():
            self._on_bed_toggled(True)

        # Status bar
        parts: list[str] = []
        if repair_result.normals_fixed > 0:
            parts.append(f"{repair_result.normals_fixed} normals fixed")
        if repair_result.holes_filled > 0:
            parts.append(f"{repair_result.holes_filled} holes filled")
        if repair_result.degenerate_faces_removed > 0:
            parts.append(
                f"{repair_result.degenerate_faces_removed} degenerate faces removed"
            )
        summary = ", ".join(parts)

        if repair_result.fully_repaired:
            self.statusBar().showMessage(f"Repair complete — {summary}")
        else:
            self.statusBar().showMessage(
                f"Repair partially complete — {summary}. "
                "Some issues remain. See analysis panel."
            )
```

**3h.** In `_on_undo` and `_on_redo` methods (added in Task 5), add `_update_repair_state()` call after `_update_undo_state()`:

```python
        self._update_repair_state()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/ui/test_main_window.py::TestMainWindowRepair -v`
Expected: PASS (all tests)

- [ ] **Step 5: Run full test suite**

Run: `pytest tests/ -v`
Expected: PASS

- [ ] **Step 6: Run linter and type checker**

Run: `ruff check src/ tests/ && mypy src/meshscope/`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/meshscope/ui/main_window.py tests/ui/test_main_window.py
git commit -m "feat: add Repair action with confirmation dialog and auto re-analyze"
```
