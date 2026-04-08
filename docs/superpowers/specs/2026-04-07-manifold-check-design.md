# Manifold/Watertight Check — Design Spec

**Feature:** 6 — Manifold/Watertight Check
**Date:** 2026-04-07
**Status:** Approved

---

## Summary

On-demand mesh topology analysis triggered by an Analyze button. Reports manifold/watertight status, hole count, open edge count, degenerate face count, and non-manifold edge count in a new "Analysis" section of the info panel. Problem edges and faces are highlighted in the viewport with distinct line styles (solid thick, tubes, dashed) that are distinguishable without color.

---

## Requirements (from Product Manifesto)

- Manifold status, hole/open edge/degenerate face/non-manifold edge counts
- Optional viewport highlighting with distinct line styles

---

## Architecture

Two new modules:

- **`src/meshscope/core/mesh_analysis.py`** — `MeshAnalysis` dataclass + `analyze_mesh()` function. Reconstructs trimesh from MeshData, runs topology analysis, returns results with edge/face indices for highlighting.
- **`src/meshscope/vtk_adapter/highlight_manager.py`** — `HighlightManager` creates VTK actors for problem edges/faces with distinct line styles.

Analysis is on-demand (not computed during load). Results stored on MeshDocument as `analysis: MeshAnalysis | None`.

---

## MeshAnalysis Data Model

New `src/meshscope/core/mesh_analysis.py`:

```python
@dataclass(frozen=True)
class MeshAnalysis:
    is_manifold: bool
    is_watertight: bool
    hole_count: int
    open_edge_count: int
    degenerate_face_count: int
    non_manifold_edge_count: int
    open_edge_indices: np.ndarray        # shape (N, 2) vertex index pairs
    non_manifold_edge_indices: np.ndarray # shape (N, 2) vertex index pairs
    degenerate_face_indices: np.ndarray   # shape (N,) face indices
```

`analyze_mesh(mesh: MeshData) -> MeshAnalysis`:
- Reconstructs trimesh.Trimesh from mesh.vertices, mesh.faces (process=False)
- Computes `is_volume`, `is_watertight` from trimesh
- Computes open edges: edges bordering only one face
- Computes non-manifold edges: edges shared by >2 faces
- Computes degenerate faces: faces with zero area
- Computes hole count: connected components of boundary edges
- Returns MeshAnalysis with all counts + index arrays

No flipped normal count — not in the Manifesto, requires manifold mesh for reliable detection. YAGNI.

---

## HighlightManager (VTK Rendering)

New `src/meshscope/vtk_adapter/highlight_manager.py`:

### Line Style Differentiation (Accessibility)

| Problem Type | Line Style | Width | Color (supplement) |
|---|---|---|---|
| Open edges | Solid thick | 3px | #cc4444 muted red |
| Non-manifold edges | Tube-rendered (`RenderLinesAsTubes`) | 2px | #cc8844 orange |
| Degenerate faces | Dashed (`SetLineStipplePattern`) | 2px | #cccc44 yellow |

Line style carries meaning; color supplements only.

### Methods

- `create_actors(analysis: MeshAnalysis, vertices: np.ndarray) -> list[vtkActor]` — builds actors for all problem edges/faces from analysis results + vertex positions

---

## SceneManager Integration

Add to `src/meshscope/vtk_adapter/scene_manager.py`:

- `show_highlights(analysis: MeshAnalysis, vertices: np.ndarray) -> None` — creates actors via HighlightManager, adds to renderer
- `hide_highlights() -> None` — removes all highlight actors
- `highlights_visible: bool` property
- `_highlight_actors: list[vtkActor]` stored separately from mesh/bed actors
- `clear()` also hides highlights

---

## Info Panel Integration

Add to `src/meshscope/ui/info_panel.py`:

- New "Analysis" CollapsibleSection, **hidden by default** until analysis is run
- `show_analysis(analysis: MeshAnalysis) -> None`:
  - Watertight: Yes/No with checkmark/warning icon
  - Holes: count
  - Open edges: count
  - Non-manifold edges: count
  - Degenerate faces: count
  - "Highlight in viewport" QCheckBox
- `clear_analysis() -> None` — hides the section
- All rows: icon shape + text (not color alone)

---

## MainWindow Integration

- `analyze_action = QAction("Analyze")` with shortcut **A**, not checkable
- Added to toolbar (after Bed section), added to View menu
- Disabled when no mesh loaded, enabled alongside render actions
- On trigger:
  1. Call `analyze_mesh(doc.mesh)`
  2. Store result: `doc.analysis = analysis`
  3. Update info panel: `info_panel.show_analysis(analysis)`
  4. Show highlights in viewport
  5. Status bar: "Analysis complete — N issues found" or "Analysis complete — no issues"
- Highlight checkbox in info panel connects to SceneManager `show_highlights()` / `hide_highlights()`
- Running analysis again replaces previous results
- Loading a new mesh clears analysis results

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Empty mesh (0 faces) | Info panel shows "No geometry to analyze" |
| trimesh analysis exception | Log error, status bar: "Analysis failed: {message}" |
| No issues found | Status bar: "Analysis complete — no issues". All counts show 0 with checkmark icons. |

No worker thread for MVP — trimesh topology analysis is fast (<1s typical, <5s for 1M+ triangles).

---

## Accessibility

- Analyze button: accessible name "Analyze mesh for printability issues"
- Analysis section rows: icon shape (checkmark/warning) + text label + count
- Highlight checkbox: accessible name "Show problem edges in viewport"
- Viewport highlights: line style differentiation (solid/tube/dashed), not color alone
- Keyboard: A shortcut triggers analysis

---

## Component States

| State | Analyze Action |
|---|---|
| **Empty** (no mesh) | Disabled |
| **Loading** | Disabled |
| **Success** (mesh loaded) | Enabled |
| **Error** | Disabled |

---

## Scope Boundaries

**In scope (Feature 6):**
- On-demand topology analysis (5 metrics)
- Analysis section in info panel
- Viewport highlighting with distinct line styles
- Highlight toggle

**Out of scope (deferred):**
- Flipped normal count → complex, not in Manifesto
- Auto-analysis on load → user triggers manually
- Worker thread / progress indicator → add if UAT reveals performance issues
- Repair actions → Feature 7

---

## Revision History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-04-07 | Initial design from brainstorming session. |
