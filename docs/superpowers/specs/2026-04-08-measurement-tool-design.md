# Feature 9: Measurement Tool — Design Spec

**Date:** 2026-04-08
**Status:** Approved
**Feature:** MVP Cutline #9 — Measurement Tool
**FRD Reference:** FRD Section 9

---

## Summary

Point-to-point distance measurement on mesh surfaces. Users toggle a dedicated measurement mode, click two points on the mesh, and see the Euclidean distance in mm. Hard cap at 3 simultaneous measurements with FIFO replacement. Session-only (not persisted, no undo).

---

## Interaction Model

### Activation
- **Toggle:** `M` key or toolbar button (checkable, like Print Bed toggle)
- **Menu:** Edit > Measure (checkable)
- **Status bar:** Shows "Measure mode — click two points on mesh surface" while active
- **Cursor:** Crosshair (`Qt.CrossCursor`) while in measurement mode

### Point Placement
1. First click on mesh surface → place point A (numbered dot marker, shown immediately)
2. Second click on mesh surface → place point B, draw line, calculate distance, add to info panel
3. Mode remains active for next measurement (stays in measure mode)
4. Click on empty space (no mesh hit) → no-op, status bar shows "No surface at click point"

### Orbit/Pan/Zoom
- **Left-click-drag** still orbits (VTK trackball default) — only a left-click **without drag** (press + release with <5px movement) is intercepted for point placement
- Right-click drag (zoom), middle-click drag (pan), and scroll wheel all work normally in measure mode
- This means the user can orbit freely to find the right angle, then single-click to place points

### Exiting Measure Mode
- Press `M` again (toggle off)
- Press `Escape`
- If a pending point A exists when exiting, discard it (no partial measurement)

### Measurement Cap (3 max, FIFO)
- When 3 measurements exist and user completes a 4th, the oldest measurement (by creation order) is automatically removed
- No confirmation dialog — FIFO is silent

### Clearing Measurements
- **Edit > Clear Measurements** (no keyboard shortcut)
- Removes all measurements and their viewport actors
- Disabled when no measurements exist

---

## Display

### Viewport
- Solid colored line between endpoints (not dashed — solid distinguishes from analysis highlight edges which use dashes/tubes)
- Numbered dot markers at each endpoint (circle with number inside)
- Up to 3 distinct colors, one per measurement:
  - Measurement 1: amber/gold (`#f0c040`)
  - Measurement 2: sky blue (`#40b0f0`)
  - Measurement 3: light green (`#60d060`)
- Colors are supplementary — measurements are also distinguished by number (colorblind-safe per Manifesto hard constraint)
- Line width: 2px
- Endpoint marker: filled circle (radius 5) with number label

### Info Panel
- New **"Measurements"** collapsible section in `InfoPanel`, below the Analysis section
- Section only visible when at least one measurement exists
- Each measurement entry shows:
  - Number and color indicator (small colored square)
  - Distance in mm with 1 decimal place (e.g., "42.7 mm")
  - Point A and Point B coordinates in mm (compact format: "A: (12.3, 45.6, 7.8)")
- Section collapses/expands like existing sections (CollapsibleSection widget)

### Status Bar Messages
| State | Message |
|---|---|
| Enter measure mode | "Measure mode — click two points on mesh surface" |
| Point A placed | "Point A placed — click second point" |
| Measurement complete | "Measurement #N: XX.X mm" |
| Click miss (no surface) | "No surface at click point" |
| Cap reached (FIFO) | "Measurement #N: XX.X mm (oldest measurement replaced)" |
| Clear all | "Measurements cleared" |

---

## Data Model

### `Measurement` (frozen dataclass, `core/mesh_data.py`)

```python
@dataclass(frozen=True)
class Measurement:
    point_a: tuple[float, float, float]  # model-space coordinates in mm
    point_b: tuple[float, float, float]  # model-space coordinates in mm
    distance_mm: float                    # Euclidean distance
    index: int                            # 1, 2, or 3
```

### MeshDocument Extension

Add to `MeshDocument.__init__`:
```python
self.measurements: list[Measurement] = []  # max 3, FIFO on overflow
```

### Invalidation

Measurements are **invalidated (cleared) when the mesh geometry changes**:
- Transform (scale, rotate, mirror)
- Repair
- Undo / Redo

Rationale: measurement coordinates are in model space. After a transform, the surface points the user clicked no longer correspond to the same physical locations. Silently keeping stale measurements would be misleading.

Status bar message on invalidation: "Measurements cleared — mesh geometry changed"

---

## Architecture

### New Components

#### `vtk_adapter/measurement_manager.py` — `MeasurementManager`

Manages VTK actors for measurement visualization. Pattern follows `HighlightManager`.

```python
class MeasurementManager:
    def __init__(self) -> None: ...

    def create_measurement_actors(
        self,
        point_a: tuple[float, float, float],
        point_b: tuple[float, float, float],
        index: int,
    ) -> list[vtkActor]:
        """Create line + endpoint marker actors for one measurement."""

    def create_pending_point_actor(
        self,
        point: tuple[float, float, float],
    ) -> vtkActor:
        """Create a single endpoint marker for point A before point B is placed."""
```

#### Ray-Mesh Intersection (in `SceneManager`)

```python
def pick_surface_point(self, display_x: int, display_y: int) -> tuple[float, float, float] | None:
    """Cast a ray from screen coordinates into the scene.
    Returns the 3D intersection point on the mesh surface, or None if no hit.
    Uses vtkCellPicker with the mesh actor."""
```

This is added to `SceneManager` because it needs access to the renderer and mesh actor. Returns model-space coordinates.

### Modified Components

- **`SceneManager`**: Add `pick_surface_point()`, `show_measurements()`, `hide_measurements()`, `show_pending_point()`, `hide_pending_point()`
- **`MeshDocument`**: Add `measurements: list[Measurement]` field
- **`InfoPanel`**: Add Measurements collapsible section
- **`MainWindow`**: Add measure mode toggle, mouse event handling, Clear Measurements action

### Mouse Event Handling

When measure mode is active, `MainWindow` installs a custom event filter on the `QVTKRenderWindowInteractor` to intercept left-click events:
- Track mouse press position on left-button down
- On left-button release, check if movement was <5px (click vs drag threshold)
- If click (not drag) → call `scene_manager.pick_surface_point(x, y)`
  - If hit: place point or complete measurement
  - If miss: show status bar message
- If drag → pass through to VTK interactor for orbit rotation
- All other mouse events (right-click, middle-click, scroll, move) always pass through

This avoids subclassing the interactor and keeps the measurement logic in `MainWindow` where all other tool logic lives.

---

## VTK Dependencies

### New Imports Required
- `vtkmodules.vtkRenderingCore.vtkCellPicker` — ray-mesh intersection (already in `vtkRenderingCore` which is included in Nuitka config)

### Nuitka Config
No new `--include-module` entries needed. `vtkCellPicker` is part of `vtkRenderingCore` which is already included. Verify during implementation.

---

## Accessibility

- Measurements distinguished by number (not color alone) — Manifesto hard constraint
- Endpoint markers are numbered circles, not just colored dots
- Info panel shows distances as text (screen reader accessible)
- Status bar announces all measurement state changes
- Measurement mode indicated by cursor change + status bar text (not color alone)
- Keyboard: `M` to toggle, `Escape` to exit

---

## Edge Cases

| Case | Behavior |
|---|---|
| No mesh loaded | Measure action disabled (greyed out) |
| Measure mode active, user loads new file | Exit measure mode, clear measurements, load file |
| Measure mode active, user clicks toolbar action (e.g., Transform) | Exit measure mode (discard pending point if any) |
| Point A placed, user exits mode | Discard pending point A |
| Mesh at extreme scale (measurements in microns or meters) | Display as-is in mm — no unit conversion |
| Two clicks on same point | Show 0.0 mm distance (valid measurement) |
| FIFO replaces measurement that user was looking at | No special handling — oldest goes away |

---

## Testing Strategy

- **Unit tests:** `Measurement` dataclass, distance calculation, FIFO replacement logic
- **Unit tests:** `MeasurementManager` actor creation (line geometry, endpoint positions)
- **Integration tests:** `pick_surface_point` with known mesh geometry and screen coordinates
- **UI tests:** Measure mode toggle, mouse click → measurement creation, Clear Measurements action
- **Regression tests:** Measurement invalidation on transform/repair/undo
