# Mesh Info Panel — Design Spec

**Feature:** 3 — Mesh Info Panel
**Date:** 2026-04-07
**Status:** Approved

---

## Summary

A dockable info panel (QDockWidget) that displays mesh metadata when a file is loaded. Four collapsible sections show file info, geometry counts, bounding box dimensions, and manifold/volume status. A warning banner alerts the user when dimensions suggest a unit mismatch.

---

## Requirements (from Product Manifesto)

- Vertex/face count
- Bounding box
- Surface area
- Volume (if manifold)
- Manifold status
- Unit mismatch detection

---

## Architecture

- **New file:** `src/meshscope/ui/info_panel.py` containing `InfoPanel(QDockWidget)`
- **Connection pattern:** Direct method call (Approach A). MainWindow calls `info_panel.update(document)` after successful load and `info_panel.clear()` on error or empty state.
- **Data source:** `MeshDocument.mesh.metadata` (MeshMetadata), `MeshDocument.warnings`, `MeshDocument.source_path`, `MeshDocument.source_format`, `MeshDocument.source_size_bytes`
- **No new dependencies.** Pure PySide6 widgets.
- **No signals or observer pattern.** Signals can be introduced later (Features 7-8) if mesh mutations need to auto-refresh the panel.

---

## Panel Layout

### Warning Banner (conditional)

Shown at the top of the panel only when `MeshDocument.warnings` contains a unit mismatch warning. Hidden otherwise.

- Styled with warning background, left border accent, warning triangle icon + text
- Text: the warning message from `_check_unit_mismatch()` (e.g., "Dimensions may indicate a unit mismatch. Consider scaling by 25.4 (inches to mm) or 0.0394 (mm to inches).")
- Accessibility: icon shape (triangle) + text. Not color-only.

### Section 1: File

| Field | Source | Example |
|---|---|---|
| Name | `Path(doc.source_path).name` | bracket_mount.stl |
| Format | `doc.source_format` (uppercased) | STL |
| Size | `doc.source_size_bytes` (human-readable) | 4.2 MB |

### Section 2: Geometry

| Field | Source | Example |
|---|---|---|
| Vertices | `metadata.vertex_count` | 24,576 |
| Faces | `metadata.face_count` | 49,148 |
| Surface area | `metadata.surface_area_mm2` | 18,432.5 mm² |

### Section 3: Dimensions

Primary display — bounding box size:

| Field | Source | Example |
|---|---|---|
| Size X | `metadata.bounding_box.size_x` | 120.0 mm |
| Size Y | `metadata.bounding_box.size_y` | 85.3 mm |
| Size Z | `metadata.bounding_box.size_z` | 42.1 mm |

Collapsible sub-section — min/max coordinates (collapsed by default):

| Field | Source | Example |
|---|---|---|
| X | `[min_x, max_x]` | [-60.0, 60.0] |
| Y | `[min_y, max_y]` | [-42.6, 42.6] |
| Z | `[min_z, max_z]` | [0.0, 42.1] |

Inline unit mismatch warning (shown when applicable):
- Smaller, less prominent than the top banner
- Displayed below the dimension values within this section

### Section 4: Status

| Field | Source | Example (manifold) | Example (non-manifold) |
|---|---|---|---|
| Manifold | `metadata.is_manifold` | Checkmark icon + "Yes" | Warning triangle icon + "No" |
| Volume | `metadata.volume_mm3` | 52,847.3 mm³ | "N/A (non-manifold)" in muted text |

---

## Collapsible Sections

- All four top-level sections are collapsible (expand/collapse on click)
- All sections start expanded by default
- Min/max coordinates sub-section within Dimensions starts collapsed
- Section headers: uppercase label, monospace font, #2a2a2a background, disclosure triangle indicator
- Collapse state is not persisted across sessions (always resets to default)

---

## Component States

| State | Behavior |
|---|---|
| **Empty** (no file loaded) | Panel visible, shows "No mesh loaded" placeholder, all sections empty |
| **Loading** | Panel stays on previous state (load is fast enough that no spinner is needed) |
| **Success** | All sections populated from MeshDocument |
| **Error** (load failed) | Panel cleared to empty state |

---

## Units

- All values displayed in mm, mm², mm³. Always. No unit selector.
- meshscope assumes millimeters throughout (standard for 3D printing).
- STL/OBJ/PLY files contain no unit metadata. 3MF specifies units but trimesh normalizes.
- Unit mismatch detection is heuristic: all dimensions < 1mm or any dimension > 10,000mm triggers a warning.
- A unit selector/conversion tool is not in the MVP. Users can scale manually via Feature 8.
- Feature 8 design note (stored in Qdrant): include contextual help about common unit conversion scaling factors.

---

## Accessibility

- **Keyboard:** Tab to focus section headers, Enter/Space to expand/collapse. Visible focus indicator (outline, not color change).
- **Screen reader:** `setAccessibleName()` on dock widget ("Mesh Info Panel"), each section header (e.g., "Geometry section, expanded"), and the warning banner.
- **Manifold status:** Checkmark icon shape + "Yes" text, or warning triangle icon shape + "No" text. Icon shape carries meaning; color supplements only.
- **Unit mismatch:** Warning triangle icon + text. Not color-only.
- **Contrast:** All text meets 4.5:1 minimum against #262626 background. Label text color must be verified (may need #999 or brighter instead of #888).
- **Numbers:** Thousands separators for readability. Right-aligned values.

---

## MainWindow Integration

```python
# __init__
self._info_panel = InfoPanel()
self.addDockWidget(Qt.LeftDockWidgetArea, self._info_panel)
self.view_menu.addAction(self._info_panel.toggleViewAction())

# After successful load
self._info_panel.update(doc)

# On load error or clear
self._info_panel.clear()
```

- Keyboard shortcut: **I** to toggle panel visibility
- View menu entry via `toggleViewAction()` (built-in QDockWidget feature)
- Status bar retains filename + face count (useful when panel is hidden)

---

## Scope Boundaries

**In scope (Feature 3):**
- Display all MeshMetadata fields
- Collapsible sections
- Unit mismatch warning (banner + inline)
- Empty/error states
- Accessibility compliance

**Out of scope (deferred):**
- Detailed manifold diagnostics (hole count, open edges, etc.) → Feature 6
- Unit selector/conversion → Post-MVP
- Info panel refresh on mesh mutation → Features 7-8 (add signals then)
- Collapse state persistence → Post-MVP

---

## Test Files

Existing test fixtures cover the needed scenarios:
- `fixtures/valid/cube.stl` — manifold mesh with known geometry
- `fixtures/valid/cube.obj` — OBJ format variant
- `fixtures/valid/cube.3mf` — 3MF format variant
- `fixtures/valid/cube.ply` — PLY format variant
- Non-manifold test mesh — may need to add a fixture

---

## Revision History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-04-07 | Initial design from brainstorming session. |
