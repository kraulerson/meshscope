# Manifold/Watertight Check Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add on-demand mesh topology analysis reporting hole count, open edge count, degenerate face count, and non-manifold edge count, with viewport highlighting using distinct line styles.

**Architecture:** New `mesh_analysis.py` computes topology metrics from MeshData via trimesh. New `highlight_manager.py` creates VTK actors for problem edges/faces. SceneManager delegates highlighting. Info panel gets a new "Analysis" section. MainWindow adds Analyze button.

**Tech Stack:** trimesh (topology analysis), VTK (vtkLine, vtkActor for highlighting), PySide6 (QCheckBox, QAction), numpy, collections.Counter

---

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/meshscope/core/mesh_analysis.py` | MeshAnalysis dataclass + analyze_mesh() function |
| Create | `src/meshscope/vtk_adapter/highlight_manager.py` | HighlightManager: VTK actors for problem edges/faces |
| Modify | `src/meshscope/vtk_adapter/scene_manager.py` | show_highlights / hide_highlights |
| Modify | `src/meshscope/ui/info_panel.py` | Analysis CollapsibleSection with show_analysis / clear_analysis |
| Modify | `src/meshscope/ui/main_window.py` | Analyze action, toolbar, menu, wiring |
| Modify | `src/meshscope/core/mesh_document.py` | Add analysis: MeshAnalysis | None field |
| Create | `tests/unit/test_mesh_analysis.py` | Analysis function tests |
| Create | `tests/unit/test_highlight_manager.py` | Highlight actor creation tests |
| Modify | `tests/unit/test_scene_manager.py` | SceneManager highlight tests |
| Modify | `tests/ui/test_info_panel.py` | Analysis section tests |
| Modify | `tests/ui/test_main_window.py` | Analyze action tests |

---

### Task 1: MeshAnalysis dataclass and analyze_mesh function

**Files:**
- Create: `tests/unit/test_mesh_analysis.py`
- Create: `src/meshscope/core/mesh_analysis.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_mesh_analysis.py`:

```python
"""Tests for mesh topology analysis."""

import numpy as np

from meshscope.core.mesh_analysis import MeshAnalysis, analyze_mesh
from meshscope.core.mesh_data import BoundingBox, MeshData, MeshMetadata


def _make_cube_mesh() -> MeshData:
    """Create a watertight cube mesh (8 verts, 12 faces)."""
    vertices = np.array([
        [0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0],
        [0, 0, 10], [10, 0, 10], [10, 10, 10], [0, 10, 10],
    ], dtype=np.float32)
    faces = np.array([
        [0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
        [0, 1, 5], [0, 5, 4], [2, 3, 7], [2, 7, 6],
        [0, 4, 7], [0, 7, 3], [1, 2, 6], [1, 6, 5],
    ], dtype=np.uint32)
    normals = np.zeros((12, 3), dtype=np.float32)
    bb = BoundingBox(0, 0, 0, 10, 10, 10)
    meta = MeshMetadata(8, 12, bb, 600.0, 1000.0, True)
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


def _make_open_mesh() -> MeshData:
    """Create a mesh with open edges (remove 2 faces from cube = hole)."""
    vertices = np.array([
        [0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0],
        [0, 0, 10], [10, 0, 10], [10, 10, 10], [0, 10, 10],
    ], dtype=np.float32)
    faces = np.array([
        [0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
        [0, 1, 5], [0, 5, 4], [2, 3, 7], [2, 7, 6],
        [0, 4, 7], [0, 7, 3],
    ], dtype=np.uint32)
    normals = np.zeros((10, 3), dtype=np.float32)
    bb = BoundingBox(0, 0, 0, 10, 10, 10)
    meta = MeshMetadata(8, 10, bb, 500.0, None, False)
    return MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)


class TestAnalyzeMeshWatertight:
    def test_cube_is_manifold(self) -> None:
        result = analyze_mesh(_make_cube_mesh())
        assert result.is_manifold is True

    def test_cube_is_watertight(self) -> None:
        result = analyze_mesh(_make_cube_mesh())
        assert result.is_watertight is True

    def test_cube_no_holes(self) -> None:
        result = analyze_mesh(_make_cube_mesh())
        assert result.hole_count == 0

    def test_cube_no_open_edges(self) -> None:
        result = analyze_mesh(_make_cube_mesh())
        assert result.open_edge_count == 0

    def test_cube_no_degenerate_faces(self) -> None:
        result = analyze_mesh(_make_cube_mesh())
        assert result.degenerate_face_count == 0

    def test_cube_no_non_manifold_edges(self) -> None:
        result = analyze_mesh(_make_cube_mesh())
        assert result.non_manifold_edge_count == 0

    def test_cube_empty_edge_indices(self) -> None:
        result = analyze_mesh(_make_cube_mesh())
        assert len(result.open_edge_indices) == 0
        assert len(result.non_manifold_edge_indices) == 0
        assert len(result.degenerate_face_indices) == 0


class TestAnalyzeMeshOpenMesh:
    def test_open_mesh_not_manifold(self) -> None:
        result = analyze_mesh(_make_open_mesh())
        assert result.is_manifold is False

    def test_open_mesh_not_watertight(self) -> None:
        result = analyze_mesh(_make_open_mesh())
        assert result.is_watertight is False

    def test_open_mesh_has_open_edges(self) -> None:
        result = analyze_mesh(_make_open_mesh())
        assert result.open_edge_count > 0

    def test_open_mesh_has_holes(self) -> None:
        result = analyze_mesh(_make_open_mesh())
        assert result.hole_count > 0

    def test_open_edge_indices_match_count(self) -> None:
        result = analyze_mesh(_make_open_mesh())
        assert len(result.open_edge_indices) == result.open_edge_count

    def test_open_edge_indices_are_vertex_pairs(self) -> None:
        result = analyze_mesh(_make_open_mesh())
        assert result.open_edge_indices.ndim == 2
        assert result.open_edge_indices.shape[1] == 2


class TestAnalyzeMeshDegenerate:
    def test_degenerate_face_detected(self) -> None:
        """A face with zero area should be counted as degenerate."""
        vertices = np.array([
            [0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0],
            [5, 5, 0],  # degenerate: colinear with edge
        ], dtype=np.float32)
        faces = np.array([
            [0, 1, 2], [0, 2, 3],
            [0, 1, 0],  # degenerate face (repeated vertex)
        ], dtype=np.uint32)
        normals = np.zeros((3, 3), dtype=np.float32)
        bb = BoundingBox(0, 0, 0, 10, 10, 0)
        meta = MeshMetadata(5, 3, bb, 100.0, None, False)
        mesh = MeshData(vertices=vertices, faces=faces, normals=normals, metadata=meta)
        result = analyze_mesh(mesh)
        assert result.degenerate_face_count >= 1
        assert len(result.degenerate_face_indices) >= 1


class TestMeshAnalysisDataclass:
    def test_is_frozen(self) -> None:
        result = analyze_mesh(_make_cube_mesh())
        try:
            result.hole_count = 99  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except AttributeError:
            pass

    def test_total_issues(self) -> None:
        result = analyze_mesh(_make_open_mesh())
        total = (
            result.open_edge_count
            + result.non_manifold_edge_count
            + result.degenerate_face_count
            + result.hole_count
        )
        assert total > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_mesh_analysis.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement mesh_analysis module**

Create `src/meshscope/core/mesh_analysis.py`:

```python
"""On-demand mesh topology analysis."""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import trimesh

if TYPE_CHECKING:
    from meshscope.core.mesh_data import MeshData

logger = logging.getLogger("meshscope.core.mesh_analysis")


@dataclass(frozen=True)
class MeshAnalysis:
    """Results of mesh topology analysis."""

    is_manifold: bool
    is_watertight: bool
    hole_count: int
    open_edge_count: int
    degenerate_face_count: int
    non_manifold_edge_count: int
    open_edge_indices: np.ndarray  # shape (N, 2) vertex index pairs
    non_manifold_edge_indices: np.ndarray  # shape (N, 2) vertex index pairs
    degenerate_face_indices: np.ndarray  # shape (N,) face indices


def analyze_mesh(mesh: MeshData) -> MeshAnalysis:
    """Analyze mesh topology and return detailed diagnostics."""
    tm = trimesh.Trimesh(
        vertices=np.array(mesh.vertices, dtype=np.float64),
        faces=np.array(mesh.faces, dtype=np.int64),
        process=False,
    )

    is_manifold = bool(tm.is_volume)
    is_watertight = bool(tm.is_watertight)

    # Edge analysis: count faces per edge
    all_edges = tm.edges.copy()
    all_edges.sort(axis=1)
    edge_tuples = [tuple(e) for e in all_edges]
    edge_counts = Counter(edge_tuples)

    # Open edges: shared by exactly 1 face
    open_edges = np.array(
        [list(e) for e, c in edge_counts.items() if c == 1],
        dtype=np.int64,
    ).reshape(-1, 2)

    # Non-manifold edges: shared by >2 faces
    nm_edges = np.array(
        [list(e) for e, c in edge_counts.items() if c > 2],
        dtype=np.int64,
    ).reshape(-1, 2)

    # Degenerate faces: zero area
    areas = tm.area_faces
    degen_indices = np.where(areas < 1e-10)[0]

    # Hole count: connected components of open/boundary edges
    hole_count = _count_holes(open_edges) if len(open_edges) > 0 else 0

    logger.info(
        "Analysis: manifold=%s watertight=%s holes=%d open=%d nm=%d degen=%d",
        is_manifold, is_watertight, hole_count,
        len(open_edges), len(nm_edges), len(degen_indices),
    )

    return MeshAnalysis(
        is_manifold=is_manifold,
        is_watertight=is_watertight,
        hole_count=hole_count,
        open_edge_count=len(open_edges),
        degenerate_face_count=len(degen_indices),
        non_manifold_edge_count=len(nm_edges),
        open_edge_indices=open_edges,
        non_manifold_edge_indices=nm_edges,
        degenerate_face_indices=degen_indices,
    )


def _count_holes(boundary_edges: np.ndarray) -> int:
    """Count boundary loops (holes) from boundary edge array."""
    if len(boundary_edges) == 0:
        return 0

    # Build adjacency from boundary edges
    adj: dict[int, set[int]] = {}
    for v0, v1 in boundary_edges:
        adj.setdefault(int(v0), set()).add(int(v1))
        adj.setdefault(int(v1), set()).add(int(v0))

    # Count connected components via BFS
    visited: set[int] = set()
    components = 0
    for start in adj:
        if start in visited:
            continue
        components += 1
        queue = [start]
        while queue:
            node = queue.pop()
            if node in visited:
                continue
            visited.add(node)
            queue.extend(adj.get(node, set()) - visited)
    return components
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_mesh_analysis.py -v`
Expected: All 15 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/core/mesh_analysis.py tests/unit/test_mesh_analysis.py
git commit -m "feat(analysis): add MeshAnalysis dataclass and analyze_mesh function"
```

---

### Task 2: HighlightManager VTK actors

**Files:**
- Create: `tests/unit/test_highlight_manager.py`
- Create: `src/meshscope/vtk_adapter/highlight_manager.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/test_highlight_manager.py`:

```python
"""Tests for mesh problem highlight VTK actors."""

import numpy as np

from meshscope.core.mesh_analysis import MeshAnalysis
from meshscope.vtk_adapter.highlight_manager import HighlightManager


def _make_clean_analysis() -> MeshAnalysis:
    return MeshAnalysis(
        is_manifold=True,
        is_watertight=True,
        hole_count=0,
        open_edge_count=0,
        degenerate_face_count=0,
        non_manifold_edge_count=0,
        open_edge_indices=np.zeros((0, 2), dtype=np.int64),
        non_manifold_edge_indices=np.zeros((0, 2), dtype=np.int64),
        degenerate_face_indices=np.zeros((0,), dtype=np.int64),
    )


def _make_problem_analysis() -> MeshAnalysis:
    return MeshAnalysis(
        is_manifold=False,
        is_watertight=False,
        hole_count=1,
        open_edge_count=2,
        degenerate_face_count=1,
        non_manifold_edge_count=1,
        open_edge_indices=np.array([[0, 1], [1, 2]], dtype=np.int64),
        non_manifold_edge_indices=np.array([[2, 3]], dtype=np.int64),
        degenerate_face_indices=np.array([0], dtype=np.int64),
    )


def _make_vertices() -> np.ndarray:
    return np.array([
        [0, 0, 0], [10, 0, 0], [10, 10, 0], [0, 10, 0],
    ], dtype=np.float32)


def _make_faces() -> np.ndarray:
    return np.array([[0, 1, 2], [0, 2, 3]], dtype=np.uint32)


class TestHighlightManagerClean:
    def test_no_actors_for_clean_mesh(self) -> None:
        mgr = HighlightManager()
        actors = mgr.create_actors(
            _make_clean_analysis(), _make_vertices(), _make_faces()
        )
        assert len(actors) == 0


class TestHighlightManagerProblems:
    def test_creates_actors_for_problems(self) -> None:
        mgr = HighlightManager()
        actors = mgr.create_actors(
            _make_problem_analysis(), _make_vertices(), _make_faces()
        )
        assert len(actors) > 0

    def test_creates_actor_per_problem_type(self) -> None:
        mgr = HighlightManager()
        # Has open edges + non-manifold + degenerate = 3 actor groups
        actors = mgr.create_actors(
            _make_problem_analysis(), _make_vertices(), _make_faces()
        )
        assert len(actors) == 3

    def test_open_edges_only(self) -> None:
        analysis = MeshAnalysis(
            is_manifold=False, is_watertight=False,
            hole_count=1, open_edge_count=2,
            degenerate_face_count=0, non_manifold_edge_count=0,
            open_edge_indices=np.array([[0, 1], [1, 2]], dtype=np.int64),
            non_manifold_edge_indices=np.zeros((0, 2), dtype=np.int64),
            degenerate_face_indices=np.zeros((0,), dtype=np.int64),
        )
        mgr = HighlightManager()
        actors = mgr.create_actors(analysis, _make_vertices(), _make_faces())
        assert len(actors) == 1  # only open edges actor
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_highlight_manager.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement HighlightManager**

Create `src/meshscope/vtk_adapter/highlight_manager.py`:

```python
"""VTK actors for highlighting mesh topology problems."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkLine, vtkPolyData
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper

if TYPE_CHECKING:
    from meshscope.core.mesh_analysis import MeshAnalysis

# Colors are supplementary — line style carries meaning
OPEN_EDGE_COLOR = (0.8, 0.267, 0.267)  # #cc4444 muted red
NON_MANIFOLD_COLOR = (0.8, 0.533, 0.267)  # #cc8844 orange
DEGENERATE_COLOR = (0.8, 0.8, 0.267)  # #cccc44 yellow


class HighlightManager:
    """Creates VTK actors for mesh problem visualization."""

    def create_actors(
        self,
        analysis: MeshAnalysis,
        vertices: np.ndarray,
        faces: np.ndarray,
    ) -> list[vtkActor]:
        """Create highlight actors for all problem types found in analysis."""
        actors: list[vtkActor] = []

        if analysis.open_edge_count > 0:
            actors.append(
                self._create_edge_actor(
                    analysis.open_edge_indices,
                    vertices,
                    color=OPEN_EDGE_COLOR,
                    line_width=3.0,
                    tubes=False,
                )
            )

        if analysis.non_manifold_edge_count > 0:
            actors.append(
                self._create_edge_actor(
                    analysis.non_manifold_edge_indices,
                    vertices,
                    color=NON_MANIFOLD_COLOR,
                    line_width=2.0,
                    tubes=True,
                )
            )

        if analysis.degenerate_face_count > 0:
            actors.append(
                self._create_face_outline_actor(
                    analysis.degenerate_face_indices,
                    vertices,
                    faces,
                    color=DEGENERATE_COLOR,
                    line_width=2.0,
                )
            )

        return actors

    def _create_edge_actor(
        self,
        edge_indices: np.ndarray,
        vertices: np.ndarray,
        *,
        color: tuple[float, float, float],
        line_width: float,
        tubes: bool,
    ) -> vtkActor:
        """Create a line actor for a set of edges."""
        points = vtkPoints()
        lines = vtkCellArray()

        for v0_idx, v1_idx in edge_indices:
            p0 = points.InsertNextPoint(*vertices[v0_idx].astype(float))
            p1 = points.InsertNextPoint(*vertices[v1_idx].astype(float))
            line = vtkLine()
            line.GetPointIds().SetId(0, p0)
            line.GetPointIds().SetId(1, p1)
            lines.InsertNextCell(line)

        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetLineWidth(line_width)
        if tubes:
            actor.GetProperty().SetRenderLinesAsTubes(True)
        return actor

    def _create_face_outline_actor(
        self,
        face_indices: np.ndarray,
        vertices: np.ndarray,
        faces: np.ndarray,
        *,
        color: tuple[float, float, float],
        line_width: float,
    ) -> vtkActor:
        """Create a dashed wireframe outline for degenerate faces."""
        points = vtkPoints()
        lines = vtkCellArray()

        for fi in face_indices:
            if fi >= len(faces):
                continue
            face = faces[fi]
            # Draw the 3 edges of the triangle
            for i in range(3):
                v0_idx = face[i]
                v1_idx = face[(i + 1) % 3]
                p0 = points.InsertNextPoint(*vertices[v0_idx].astype(float))
                p1 = points.InsertNextPoint(*vertices[v1_idx].astype(float))
                line = vtkLine()
                line.GetPointIds().SetId(0, p0)
                line.GetPointIds().SetId(1, p1)
                lines.InsertNextCell(line)

        polydata = vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetLineWidth(line_width)
        actor.GetProperty().SetLineStipplePattern(0xF0F0)
        actor.GetProperty().SetLineStippleRepeatFactor(1)
        return actor
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_highlight_manager.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/vtk_adapter/highlight_manager.py tests/unit/test_highlight_manager.py
git commit -m "feat(analysis): add HighlightManager for problem edge/face visualization"
```

---

### Task 3: SceneManager highlight integration

**Files:**
- Modify: `tests/unit/test_scene_manager.py`
- Modify: `src/meshscope/vtk_adapter/scene_manager.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/unit/test_scene_manager.py`:

```python
from meshscope.core.mesh_analysis import MeshAnalysis


class TestSceneManagerHighlights:
    def test_highlights_not_visible_initially(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        assert sm.highlights_visible is False

    def test_show_highlights(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        analysis = MeshAnalysis(
            is_manifold=False, is_watertight=False,
            hole_count=1, open_edge_count=2,
            degenerate_face_count=0, non_manifold_edge_count=0,
            open_edge_indices=np.array([[0, 1], [1, 2]], dtype=np.int64),
            non_manifold_edge_indices=np.zeros((0, 2), dtype=np.int64),
            degenerate_face_indices=np.zeros((0,), dtype=np.int64),
        )
        vertices = np.array([[0,0,0],[10,0,0],[10,10,0]], dtype=np.float32)
        faces = np.array([[0,1,2]], dtype=np.uint32)
        sm.show_highlights(analysis, vertices, faces)
        assert sm.highlights_visible is True

    def test_hide_highlights(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        analysis = MeshAnalysis(
            is_manifold=False, is_watertight=False,
            hole_count=1, open_edge_count=2,
            degenerate_face_count=0, non_manifold_edge_count=0,
            open_edge_indices=np.array([[0, 1], [1, 2]], dtype=np.int64),
            non_manifold_edge_indices=np.zeros((0, 2), dtype=np.int64),
            degenerate_face_indices=np.zeros((0,), dtype=np.int64),
        )
        vertices = np.array([[0,0,0],[10,0,0],[10,10,0]], dtype=np.float32)
        faces = np.array([[0,1,2]], dtype=np.uint32)
        sm.show_highlights(analysis, vertices, faces)
        sm.hide_highlights()
        assert sm.highlights_visible is False

    def test_clear_also_hides_highlights(self) -> None:
        renderer = vtkRenderer()
        sm = SceneManager(renderer)
        analysis = MeshAnalysis(
            is_manifold=False, is_watertight=False,
            hole_count=1, open_edge_count=2,
            degenerate_face_count=0, non_manifold_edge_count=0,
            open_edge_indices=np.array([[0, 1], [1, 2]], dtype=np.int64),
            non_manifold_edge_indices=np.zeros((0, 2), dtype=np.int64),
            degenerate_face_indices=np.zeros((0,), dtype=np.int64),
        )
        vertices = np.array([[0,0,0],[10,0,0],[10,10,0]], dtype=np.float32)
        faces = np.array([[0,1,2]], dtype=np.uint32)
        sm.show_highlights(analysis, vertices, faces)
        sm.clear()
        assert sm.highlights_visible is False
```

NOTE: Read the existing test file first to see how SceneManager is constructed (may use vtkRenderer directly or a fixture). Add `import numpy as np` and `from meshscope.core.mesh_analysis import MeshAnalysis` at the top. Adapt constructor pattern to match existing tests.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_scene_manager.py::TestSceneManagerHighlights -v`
Expected: FAIL — `AttributeError`

- [ ] **Step 3: Add highlight methods to SceneManager**

Add imports to `src/meshscope/vtk_adapter/scene_manager.py`:
```python
import numpy as np
from meshscope.core.mesh_analysis import MeshAnalysis
from meshscope.vtk_adapter.highlight_manager import HighlightManager
```

In `__init__`, add:
```python
        self._highlight_actors: list[vtkActor] = []
        self._highlight_manager = HighlightManager()
        self._highlights_visible = False
```

Add methods:
```python
    def show_highlights(
        self, analysis: MeshAnalysis, vertices: np.ndarray, faces: np.ndarray
    ) -> None:
        """Show highlight actors for mesh problems."""
        self.hide_highlights()
        self._highlight_actors = self._highlight_manager.create_actors(
            analysis, vertices, faces
        )
        for actor in self._highlight_actors:
            self._renderer.AddActor(actor)
        self._highlights_visible = True

    def hide_highlights(self) -> None:
        """Remove all highlight actors."""
        for actor in self._highlight_actors:
            self._renderer.RemoveActor(actor)
        self._highlight_actors.clear()
        self._highlights_visible = False

    @property
    def highlights_visible(self) -> bool:
        return self._highlights_visible
```

Update `clear()` to also call `self.hide_highlights()`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/unit/test_scene_manager.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/vtk_adapter/scene_manager.py tests/unit/test_scene_manager.py
git commit -m "feat(analysis): integrate HighlightManager into SceneManager"
```

---

### Task 4: MeshDocument analysis field + Info panel Analysis section

**Files:**
- Modify: `src/meshscope/core/mesh_document.py`
- Modify: `tests/ui/test_info_panel.py`
- Modify: `src/meshscope/ui/info_panel.py`

- [ ] **Step 1: Add analysis field to MeshDocument**

In `src/meshscope/core/mesh_document.py`, add import and field:

```python
if TYPE_CHECKING:
    from meshscope.core.mesh_analysis import MeshAnalysis
    from meshscope.core.mesh_data import MeshData
```

In `__init__`, add after `self.warnings`:
```python
        self.analysis: MeshAnalysis | None = None
```

- [ ] **Step 2: Write failing tests for info panel Analysis section**

Append to `tests/ui/test_info_panel.py`:

```python
from meshscope.core.mesh_analysis import MeshAnalysis


def _make_clean_analysis() -> MeshAnalysis:
    return MeshAnalysis(
        is_manifold=True, is_watertight=True,
        hole_count=0, open_edge_count=0,
        degenerate_face_count=0, non_manifold_edge_count=0,
        open_edge_indices=np.zeros((0, 2), dtype=np.int64),
        non_manifold_edge_indices=np.zeros((0, 2), dtype=np.int64),
        degenerate_face_indices=np.zeros((0,), dtype=np.int64),
    )


def _make_problem_analysis() -> MeshAnalysis:
    return MeshAnalysis(
        is_manifold=False, is_watertight=False,
        hole_count=2, open_edge_count=8,
        degenerate_face_count=3, non_manifold_edge_count=1,
        open_edge_indices=np.zeros((8, 2), dtype=np.int64),
        non_manifold_edge_indices=np.zeros((1, 2), dtype=np.int64),
        degenerate_face_indices=np.zeros((3,), dtype=np.int64),
    )


class TestInfoPanelAnalysisSection:
    def test_analysis_section_hidden_by_default(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        assert panel.analysis_section_visible() is False

    def test_show_analysis_makes_section_visible(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.show_analysis(_make_clean_analysis())
        assert panel.analysis_section_visible() is True

    def test_clean_analysis_shows_watertight_yes(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.show_analysis(_make_clean_analysis())
        text = panel.analysis_section_text()
        assert "Watertight" in text
        assert "Yes" in text

    def test_problem_analysis_shows_counts(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.show_analysis(_make_problem_analysis())
        text = panel.analysis_section_text()
        assert "8" in text  # open edges
        assert "3" in text  # degenerate faces
        assert "2" in text  # holes
        assert "1" in text  # non-manifold

    def test_problem_analysis_shows_watertight_no(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.show_analysis(_make_problem_analysis())
        text = panel.analysis_section_text()
        assert "No" in text

    def test_clear_analysis_hides_section(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.show_analysis(_make_clean_analysis())
        panel.clear_analysis()
        assert panel.analysis_section_visible() is False

    def test_clear_also_clears_analysis(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.set_document(_make_document())
        panel.show_analysis(_make_clean_analysis())
        panel.clear()
        assert panel.analysis_section_visible() is False

    def test_has_highlight_checkbox(self, qapp: QApplication) -> None:
        panel = InfoPanel()
        panel.show_analysis(_make_problem_analysis())
        assert panel.has_highlight_checkbox() is True
```

- [ ] **Step 3: Implement Analysis section in info_panel.py**

Add `QCheckBox` to imports. Add to `__init__` after the Status section (before `addStretch`):

```python
        # --- Analysis section (hidden until analysis is run) ---
        self._analysis_section = CollapsibleSection("Analysis")
        self._watertight_label = QLabel()
        self._holes_label = QLabel()
        self._open_edges_label = QLabel()
        self._non_manifold_label = QLabel()
        self._degenerate_label = QLabel()
        self._highlight_checkbox = QCheckBox("Highlight in viewport")
        self._highlight_checkbox.setAccessibleName("Show problem edges in viewport")
        self._analysis_section.content_layout.addWidget(self._watertight_label)
        self._analysis_section.content_layout.addWidget(self._holes_label)
        self._analysis_section.content_layout.addWidget(self._open_edges_label)
        self._analysis_section.content_layout.addWidget(self._non_manifold_label)
        self._analysis_section.content_layout.addWidget(self._degenerate_label)
        self._analysis_section.content_layout.addWidget(self._highlight_checkbox)
        self._analysis_section.setVisible(False)
        self._layout.addWidget(self._analysis_section)
```

Add methods:

```python
    def show_analysis(self, analysis: MeshAnalysis) -> None:
        """Show analysis results in the Analysis section."""
        from meshscope.core.mesh_analysis import MeshAnalysis as _MA  # noqa: F811

        if analysis.is_watertight:
            self._watertight_label.setText(f"{_CHECKMARK} Watertight: Yes")
            self._watertight_label.setAccessibleName("Watertight: Yes")
        else:
            self._watertight_label.setText(f"{_WARNING} Watertight: No")
            self._watertight_label.setAccessibleName("Watertight: No")

        self._holes_label.setText(
            f"{_CHECKMARK if analysis.hole_count == 0 else _WARNING} "
            f"Holes: {analysis.hole_count}"
        )
        self._open_edges_label.setText(
            f"{_CHECKMARK if analysis.open_edge_count == 0 else _WARNING} "
            f"Open edges: {analysis.open_edge_count}"
        )
        self._non_manifold_label.setText(
            f"{_CHECKMARK if analysis.non_manifold_edge_count == 0 else _WARNING} "
            f"Non-manifold edges: {analysis.non_manifold_edge_count}"
        )
        self._degenerate_label.setText(
            f"{_CHECKMARK if analysis.degenerate_face_count == 0 else _WARNING} "
            f"Degenerate faces: {analysis.degenerate_face_count}"
        )

        has_issues = (
            analysis.open_edge_count > 0
            or analysis.non_manifold_edge_count > 0
            or analysis.degenerate_face_count > 0
        )
        self._highlight_checkbox.setVisible(has_issues)
        self._highlight_checkbox.setChecked(has_issues)
        self._analysis_section.setVisible(True)

    def clear_analysis(self) -> None:
        """Hide the Analysis section."""
        self._analysis_section.setVisible(False)
        self._highlight_checkbox.setChecked(False)

    @property
    def highlight_checkbox(self) -> QCheckBox:
        return self._highlight_checkbox

    # Test accessors
    def analysis_section_visible(self) -> bool:
        return not self._analysis_section.isHidden()

    def analysis_section_text(self) -> str:
        return "\n".join([
            self._watertight_label.text(),
            self._holes_label.text(),
            self._open_edges_label.text(),
            self._non_manifold_label.text(),
            self._degenerate_label.text(),
        ])

    def has_highlight_checkbox(self) -> bool:
        return self._highlight_checkbox is not None
```

Update `clear()` to also call `self.clear_analysis()`.

Add TYPE_CHECKING import for MeshAnalysis at the top of info_panel.py:
```python
if TYPE_CHECKING:
    from meshscope.core.mesh_analysis import MeshAnalysis
    from meshscope.core.mesh_document import MeshDocument
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_info_panel.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/core/mesh_document.py src/meshscope/ui/info_panel.py tests/ui/test_info_panel.py
git commit -m "feat(analysis): add Analysis section to info panel with show/clear/highlight"
```

---

### Task 5: MainWindow Analyze action integration

**Files:**
- Modify: `tests/ui/test_main_window.py`
- Modify: `src/meshscope/ui/main_window.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/ui/test_main_window.py`:

```python
class TestMainWindowAnalyze:
    def test_analyze_action_exists(self, window: MainWindow) -> None:
        assert hasattr(window, "analyze_action")

    def test_analyze_action_disabled_initially(self, window: MainWindow) -> None:
        assert not window.analyze_action.isEnabled()

    def test_analyze_action_enabled_after_load(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        assert window.analyze_action.isEnabled()

    def test_analyze_shortcut_is_a(self, window: MainWindow) -> None:
        assert window.analyze_action.shortcut() == QKeySequence("A")

    def test_analyze_action_in_view_menu(self, window: MainWindow) -> None:
        view_menu = None
        for action in window.menuBar().actions():
            if "View" in action.text():
                view_menu = action.menu()
                break
        assert view_menu is not None
        action_texts = [a.text() for a in view_menu.actions()]
        assert any("Analyze" in t for t in action_texts)

    def test_analyze_runs_analysis(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        window.analyze_action.trigger()
        assert window._document is not None
        assert window._document.analysis is not None

    def test_analyze_shows_analysis_section(self, window: MainWindow) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        window.analyze_action.trigger()
        assert window._info_panel.analysis_section_visible() is True

    def test_analyze_disabled_after_error(
        self, window: MainWindow, tmp_path: Path
    ) -> None:
        fixtures = Path(__file__).parent.parent / "fixtures" / "valid"
        window._load_file(fixtures / "cube.stl")
        bad = tmp_path / "bad.stl"
        bad.write_bytes(b"not a real stl file")
        window._load_file(bad)
        assert not window.analyze_action.isEnabled()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ui/test_main_window.py::TestMainWindowAnalyze -v`
Expected: FAIL — `AttributeError`

- [ ] **Step 3: Add Analyze action to MainWindow**

Add import:
```python
from meshscope.core.mesh_analysis import analyze_mesh
```

In `_create_actions`, add after bed_action:
```python
        self.analyze_action = QAction("Analyze", self)
        self.analyze_action.setShortcut(QKeySequence("A"))
        self.analyze_action.setEnabled(False)
        self.analyze_action.setToolTip("Analyze mesh for printability issues")
        self.analyze_action.setAccessibleName("Analyze mesh for printability issues")
        self.analyze_action.triggered.connect(self._on_analyze)
```

In `_create_menus`, add to view_menu after bed_action:
```python
        view_menu.addAction(self.analyze_action)
```

In `_create_toolbar`, add after bed_preset_combo:
```python
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.analyze_action)
```

In `_set_render_actions_enabled`, add:
```python
        self.analyze_action.setEnabled(enabled)
```

Add handler:
```python
    def _on_analyze(self) -> None:
        """Run mesh topology analysis."""
        if self._document is None:
            return

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
                self.statusBar().showMessage(
                    f"Analysis complete — {total_issues} issue{'s' if total_issues != 1 else ''} found"
                )
                # Show highlights
                self._viewport.scene_manager.show_highlights(
                    analysis,
                    self._document.mesh.vertices,
                    self._document.mesh.faces,
                )
                self._viewport.vtk_render()
            else:
                self.statusBar().showMessage("Analysis complete — no issues")

            # Connect highlight checkbox
            self._info_panel.highlight_checkbox.toggled.connect(
                self._on_highlight_toggled
            )

        except Exception as e:
            self.statusBar().showMessage(f"Analysis failed: {e}")
            logger.exception("Analysis failed")

    def _on_highlight_toggled(self, checked: bool) -> None:
        """Toggle viewport highlights on/off."""
        if checked and self._document is not None and self._document.analysis is not None:
            self._viewport.scene_manager.show_highlights(
                self._document.analysis,
                self._document.mesh.vertices,
                self._document.mesh.faces,
            )
        else:
            self._viewport.scene_manager.hide_highlights()
        self._viewport.vtk_render()
```

Also update `_set_state_error` to clear analysis:
```python
        self._info_panel.clear_analysis()
```

And update `_load_file` to clear previous analysis when loading a new file. After `self._document = doc`:
```python
        self._info_panel.clear_analysis()
        self._viewport.scene_manager.hide_highlights()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/meshscope/ui/main_window.py tests/ui/test_main_window.py
git commit -m "feat(analysis): integrate Analyze action into MainWindow with highlighting"
```

---

### Task 6: Manual smoke test and final verification

**Files:** None (verification only)

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Run linting and type checking**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && ruff check src/meshscope/core/mesh_analysis.py src/meshscope/vtk_adapter/highlight_manager.py && mypy src/meshscope/core/mesh_analysis.py src/meshscope/vtk_adapter/highlight_manager.py`
Expected: No errors

- [ ] **Step 3: Visual verification**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && source .venv/bin/activate && python -m meshscope tests/fixtures/valid/cube.stl`

Verify:
- Analyze button in toolbar, shortcut A
- Cube analysis: all zeros, "no issues" in status bar, no highlights
- Load a non-manifold mesh if available — analysis shows counts, highlights appear
- Highlight checkbox toggles highlights on/off
- Analysis section hidden before running analysis
- New mesh load clears previous analysis

- [ ] **Step 4: Record the feature**

Run: `cd /Users/karl/Documents/Claude\ Projects/meshscope && bash scripts/test-gate.sh --record-feature "manifold-watertight-check"`

- [ ] **Step 5: Commit any final fixes if needed**
