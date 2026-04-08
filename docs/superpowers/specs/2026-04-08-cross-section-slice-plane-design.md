# Feature 10: Cross-Section Slice Plane — Design Spec

**Date:** 2026-04-08
**Status:** Approved
**Feature:** MVP Cutline #10 — Cross-Section Slice Plane
**FRD Reference:** FRD Section 10

---

## Summary

Interactive clipping plane that slices through the mesh to reveal interior cross-sections. Users drag and rotate the plane directly in the 3D viewport using VTK's implicit plane widget. X/Y/Z preset buttons and a Reset button are available in a floating overlay panel. The cross-section interior is filled with a distinct color. Session-only (not persisted, no undo).

---

## Interaction Model

### Activation
- **Toggle:** `C` key or toolbar button (checkable, like Print Bed toggle)
- **Menu:** View > Slice Plane (checkable)
- **Status bar:** Shows "Slice plane active — drag to move, rotate handles to tilt" while active
- On activation, plane appears at model center, oriented along Z axis (default preset)

### Direct Manipulation (VTK Widget)
- `vtkImplicitPlaneWidget2` renders a translucent plane in the viewport
- **Move:** grab the center handle and drag to slide the plane along its normal axis
- **Rotate:** grab edge/rotation handles to tilt the plane to arbitrary orientations
- **Normal arrow:** shows the clipping direction (visible side vs clipped side)
- Standard orbit/pan/zoom interaction works simultaneously — the widget only captures events when the user interacts with its handles
- **Real-time update:** clipping recalculates as the user drags (VTK widget fires `InteractionEvent` continuously during drag). This provides immediate visual feedback of the cross-section.

### Preset Buttons
Available in the floating overlay panel:
- **X** — snap plane to YZ plane through model center (normal along X axis)
- **Y** — snap plane to XZ plane through model center (normal along Y axis)
- **Z** — snap plane to XY plane through model center (normal along Z axis, default)
- **Reset** — return plane to model center at its current orientation (does not change axis)

### Deactivation
- Press `C` again (toggle off)
- Press `Escape`
- Clipping is removed, full mesh restored

---

## Display

### Viewport — Clipping
- Mesh is clipped by the plane: geometry on one side of the plane is hidden
- The remaining visible portion renders normally (same material/shading as unclipped mesh)
- Cross-section interior (the "cut face") is filled with a distinct terracotta color (`#c06040`) so the slice surface is clearly distinguishable from the exterior mesh

### Viewport — Plane Widget
- Translucent plane rectangle with dashed outline (VTK widget default styling, color: `#89b4fa` blue to match UI theme)
- Normal arrow pointing in the clip direction
- Draggable center handle (sphere)
- Rotation handles at edges

### Floating Overlay Panel
- **Position:** top-right corner of viewport
- **Visibility:** only shown while slice mode is active
- **Background:** semi-transparent dark (`#262626ee`) with border, rounded corners
- **Contents:**
  - "Slice Plane" title
  - X / Y / Z preset buttons in a row (current preset highlighted)
  - Reset button below
- **Size:** compact (~110px wide), does not resize with viewport

### Status Bar Messages
| State | Message |
|---|---|
| Slice activated | "Slice plane active — drag to move, rotate handles to tilt" |
| Preset applied | "Slice plane: X axis" / "Y axis" / "Z axis" |
| Reset | "Slice plane reset to model center" |
| Plane outside bounds | (no special message — full model shown, plane widget still visible) |
| Slice deactivated | "Slice plane removed" |

---

## Interior Fill (Cross-Section Capping)

### Approach
Use `vtkClipClosedSurface` to clip the mesh and generate a filled cap on the cut surface. This produces a watertight result where the interior is visible as a solid surface.

**Pipeline:**
1. `vtkPlane` defines the implicit clipping function (position + normal from widget)
2. `vtkClipClosedSurface` clips the mesh polydata and generates cap polygons
3. Cap polygons rendered with a separate `vtkActor` using the terracotta color
4. Clipped mesh rendered with the original mesh actor's material

**Fallback:** If `vtkClipClosedSurface` is unavailable or fails (e.g., non-manifold mesh), fall back to `vtkClipPolyData` without capping. The cross-section shows as an open hole rather than a filled surface. This is acceptable degradation — the clipping still works, just without the fill.

### Color
- Cross-section fill: terracotta (`#c06040`) — warm, distinct from the cool gray/blue mesh default
- Not colorblind-sensitive — the fill is distinguished by being a different surface (interior vs exterior), not just by color

---

## Data Model

### No New Persistent Data Structure
The slice plane state lives entirely in the VTK widget (`vtkImplicitPlaneWidget2`). No new dataclass is needed because:
- The plane is session-only (not persisted across app restarts)
- The plane is not undoable (it's a visualization tool, not a mesh operation)
- The widget manages its own position/orientation state

### MeshDocument
No changes to `MeshDocument`. The `slice_plane: SlicePlane | None` field mentioned in the Project Bible is not needed — the VTK widget is the source of truth for plane state. Update the Bible to reflect this decision.

---

## Architecture

### New Components

#### `vtk_adapter/slice_plane_manager.py` — `SlicePlaneManager`

Manages the VTK clipping pipeline and plane widget lifecycle.

```python
class SlicePlaneManager:
    def __init__(self, renderer: vtkRenderer, interactor: vtkRenderWindowInteractor) -> None: ...

    def activate(self, polydata: vtkPolyData, bounds: tuple[float, ...]) -> None:
        """Show the plane widget and start clipping.
        Initializes plane at center of bounds, oriented along Z axis."""

    def deactivate(self) -> None:
        """Remove plane widget and restore full mesh."""

    def set_preset(self, axis: str, bounds: tuple[float, ...]) -> None:
        """Snap plane to X, Y, or Z axis through center of bounds."""

    def reset_to_center(self, bounds: tuple[float, ...]) -> None:
        """Move plane back to center of bounds, keeping current orientation."""

    def update_mesh(self, polydata: vtkPolyData, bounds: tuple[float, ...]) -> None:
        """Update the clipped mesh (called after transforms/repair/undo).
        Keeps current plane position, recalculates clip."""

    @property
    def is_active(self) -> bool: ...
```

#### `ui/slice_overlay.py` — `SliceOverlayWidget`

Floating Qt overlay widget with preset buttons and Reset.

```python
class SliceOverlayWidget(QWidget):
    """Floating overlay for slice plane controls. Parented to viewport widget."""

    preset_clicked = Signal(str)   # emits "x", "y", or "z"
    reset_clicked = Signal()

    def __init__(self, parent: QWidget) -> None: ...

    def set_active_preset(self, axis: str) -> None:
        """Highlight the active preset button."""

    def show_overlay(self) -> None: ...
    def hide_overlay(self) -> None: ...
```

### Modified Components

- **`SceneManager`**: Add `activate_slice_plane()`, `deactivate_slice_plane()`, `set_slice_preset()`, `reset_slice_plane()`, `update_slice_mesh()`. Delegates to `SlicePlaneManager`. Needs to hide the original mesh actor and show the clipped version while slice is active.
- **`ViewportWidget`**: Host the `SliceOverlayWidget` as a child widget (positioned top-right via `move()` in `resizeEvent`)
- **`MainWindow`**: Add slice plane toggle action, connect overlay signals, handle preset/reset, update clip on mesh changes

### Clipping Pipeline Detail

```
                    ┌─────────────────┐
                    │  vtkImplicit     │
                    │  PlaneWidget2    │──── user drags/rotates
                    └────────┬────────┘
                             │ vtkPlane (position + normal)
                             ▼
              ┌──────────────────────────┐
              │  vtkClipClosedSurface    │
              │  (input: mesh polydata)  │
              └──────┬───────────┬───────┘
                     │           │
              clipped mesh    cap polys
                     │           │
              ┌──────▼──────┐ ┌──▼───────────┐
              │ mesh actor  │ │ cap actor     │
              │ (original   │ │ (terracotta   │
              │  material)  │ │  #c06040)     │
              └─────────────┘ └──────────────┘
```

---

## VTK Dependencies

### New Imports Required
- `vtkmodules.vtkInteractionWidgets.vtkImplicitPlaneWidget2` — interactive plane widget
- `vtkmodules.vtkInteractionWidgets.vtkImplicitPlaneRepresentation` — widget representation
- `vtkmodules.vtkFiltersGeneral.vtkClipClosedSurface` — clipping with cap generation (check availability; may be in `vtkFiltersGeneral` which is already included)
- `vtkmodules.vtkCommonDataModel.vtkPlane` — implicit plane function (already in `vtkCommonDataModel` which is included)

### Nuitka Config Additions
```
--include-module=vtkmodules.vtkInteractionWidgets
```

Must be added to the Nuitka config in `PROJECT_BIBLE.md` Section 11. Verify `vtkClipClosedSurface` is in `vtkFiltersGeneral` (already included) during implementation.

---

## Interaction with Other Features

| Feature | Interaction |
|---|---|
| **Transforms (F8)** | Plane stays at world-space position. Clip recalculated on transformed mesh. |
| **Repair (F7)** | Same as transforms — clip recalculated. |
| **Undo/Redo** | Same as transforms — clip recalculated. |
| **Analysis (F6)** | Analysis highlights shown on the visible (clipped) portion only. |
| **Measurements (F9)** | Both can be active simultaneously. Measurements are placed on the visible (clipped) mesh surface. |
| **Print Bed (F5)** | Both can be active simultaneously. Independent overlay. |
| **File Load** | Exit slice mode, remove plane. |
| **Wireframe toggle** | Wireframe applies to the clipped mesh portion. |

---

## Accessibility

- Slice mode indicated by status bar text + floating overlay panel (not color alone)
- Preset buttons have text labels ("X", "Y", "Z", "Reset") — not icons
- Floating overlay has sufficient contrast against viewport background
- Keyboard: `C` to toggle, `Escape` to exit
- VTK widget handles are sized for easy mouse targeting (VTK default sizing)
- Cross-section fill distinguished by being a different surface, not only by color

---

## Edge Cases

| Case | Behavior |
|---|---|
| No mesh loaded | Slice action disabled (greyed out) |
| Plane fully outside model bounds | Show full unclipped model (Manifesto requirement). Plane widget still visible and draggable. |
| Non-manifold mesh (cap generation fails) | Fall back to `vtkClipPolyData` — clipping works but cross-section shows open hole instead of filled surface. Status bar: "Cross-section fill unavailable for non-manifold mesh" |
| User loads new file while slice active | Deactivate slice mode, remove plane, load file normally |
| Very thin mesh (plane barely intersects) | Small cross-section is fine — no minimum size requirement |
| User clicks preset while plane is at that preset | No-op (plane already at that position) |
| Viewport resize | Floating overlay repositions to top-right via `resizeEvent` |

---

## Testing Strategy

- **Unit tests:** `SlicePlaneManager` activation/deactivation, preset positioning, reset logic
- **Unit tests:** `SliceOverlayWidget` signal emission on button clicks, visibility toggling
- **Integration tests:** Clipping pipeline — verify clipped polydata has fewer cells than original
- **Integration tests:** Cap generation — verify cap actor exists with correct color
- **UI tests:** Toggle slice mode, preset buttons, overlay visibility
- **Regression tests:** Clip update after transform/repair/undo, slice removed on file load
- **Edge case tests:** Plane outside bounds (full mesh visible), non-manifold fallback
