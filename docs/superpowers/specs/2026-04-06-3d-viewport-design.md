# 3D Viewport — Implementation Design

**Feature:** #2 3D Viewport (FRD Section 2)
**Date:** 2026-04-06
**Status:** Approved
**Scope:** Main window shell + VTK viewport + scene management. Includes file open dialog, drag-drop, toolbar, menu bar, status bar, and interactive 3D rendering.

---

## Goal

Render a loaded mesh in an interactive 3D viewport embedded in the application's main window. Provide orbit, pan, zoom, fit-to-view, wireframe overlay toggle, and flat/smooth shading toggle. Include the full main window chrome (menu bar, toolbar, status bar, drag-drop) so the application is end-to-end usable.

## Architecture

### Approach: B-lite (SceneManager)

A `SceneManager` class owns the scene contents (mesh actor, lights, camera setup) and provides a clean interface for display and render mode changes. The `ViewportWidget` owns the VTK render window and renderer. `VtkMeshAdapter` is a stateless converter from `MeshData` to `vtkPolyData`. `MainWindow` orchestrates user actions.

This establishes the right seam for Features 5, 9, 10 (print bed, measurements, clipping plane) to add actors to the scene without the viewport widget becoming a god object. The SceneManager starts minimal — no speculative infrastructure for those features yet.

### Components

**`MainWindow`** (`src/meshscope/ui/main_window.py`)
QMainWindow subclass. Owns menu bar, toolbar, status bar, and signal wiring. Handles file open (dialog, drag-drop, CLI arg). Calls `load_mesh()`, converts via adapter, hands to SceneManager. Stores the current `MeshDocument` for later features.

**`ViewportWidget`** (`src/meshscope/ui/viewport_widget.py`)
Subclass of `QVTKRenderWindowInteractor`. Owns the `vtkRenderWindow` and `vtkRenderer`. Handles resize events, empty state display, and error state fallback. Delegates all scene content management to SceneManager.

**`SceneManager`** (`src/meshscope/vtk_adapter/scene_manager.py`)
Owns the mesh actor, wireframe overlay actor, lights, and camera configuration. Operates on a `vtkRenderer` that it receives (does not create). API:

```python
class SceneManager:
    def __init__(self, renderer: vtkRenderer) -> None: ...
    def display_mesh(self, polydata: vtkPolyData) -> None: ...
    def clear(self) -> None: ...
    def set_wireframe_overlay(self, enabled: bool) -> None: ...
    def set_smooth_shading(self, enabled: bool) -> None: ...
    def fit_to_view(self) -> None: ...
    @property
    def has_mesh(self) -> bool: ...
```

**`mesh_data_to_polydata()`** (`src/meshscope/vtk_adapter/mesh_adapter.py`)
Stateless function converting `MeshData` to `vtkPolyData`:

```python
def mesh_data_to_polydata(mesh: MeshData) -> vtkPolyData:
    """Convert MeshData (numpy arrays) to VTK polydata."""
```

### Data Flow

```
User action (open dialog / drag-drop / CLI arg)
  → MainWindow receives file path
  → load_mesh(path) → MeshDocument (or MeshLoadError → error dialog)
  → mesh_data_to_polydata(doc.mesh) → vtkPolyData
  → scene_manager.display_mesh(polydata)
      → creates vtkPolyDataMapper + vtkActor
      → sets up headlight + ambient light
      → auto-frames camera (fit to view)
  → status bar updated: "{filename} — {face_count:,} faces"
  → MainWindow stores MeshDocument for later features
```

---

## Main Window Layout

### Menu Bar
- **File**: Open (Ctrl+O), separator, Exit (Ctrl+Q)
- **View**: Wireframe Overlay (W), Shading Toggle (S), Fit to View (F)
- **Help**: About

### Toolbar (Left, Vertical)
All buttons have icon + text label (never icon-only, per accessibility rules):
- **Open** — opens file dialog
- **Wireframe** — toggles wireframe overlay (checkable)
- **Shading** — toggles flat/smooth shading (checkable)
- **Fit** — fits camera to model bounding box

### Status Bar
- Empty state: "Ready"
- Loading: "Loading {filename}..."
- Success: "{filename} — {face_count:,} faces"
- Error: exception's `user_message` text

### Drag-Drop
Entire main window accepts file drops. `dragEnterEvent` accepts files with `.stl`, `.obj`, `.3mf`, `.ply` extensions (case-insensitive). `dropEvent` loads the first accepted file.

### CLI Argument
If `sys.argv[1]` is a file path, load it on startup. Enables "open with" workflows.

---

## Window States

Every interactive component has 4 states per Project Bible:

| State | Viewport | Status Bar | Toolbar |
|---|---|---|---|
| **Empty** | Centered text: "Open a file or drag one here" + supported formats | "Ready" | Open enabled, others disabled |
| **Loading** | Previous content stays visible | "Loading {filename}..." | All disabled |
| **Success** | Rendered mesh | "{filename} — {face_count:,} faces" | All enabled |
| **Error** | Previous content stays visible | Error `user_message` | Open enabled, others disabled |

Loading is synchronous for MVP. `QApplication.processEvents()` called before load to ensure status bar updates. Threading deferred unless load times exceed the 5s target.

Re-loading a new file replaces the current mesh. No confirmation prompt for MVP.

---

## VTK Rendering

### Camera & Interaction
- Interactor style: `vtkInteractorStyleTrackballCamera` (provides orbit, pan, zoom)
- Orbit: left-click drag
- Pan: middle-click drag or Shift+left-click drag
- Zoom: scroll wheel
- Zoom clamp: min distance = 10% of bounding box diagonal, max = 10x diagonal
- Fit to view: `renderer.ResetCamera()` with 10% padding. Triggered on initial load, F key, double-click, toolbar button.

### Lighting
- **Headlight**: `vtkLight`, type `HeadLight`, white, intensity 0.8. Follows camera automatically.
- **Ambient fill**: `vtkLight`, fixed position above-right, intensity 0.3. Prevents fully black shadows.
- No user-configurable lighting for MVP.

### Render Modes
- **Solid** (default): `actor.GetProperty().SetRepresentationToSurface()`
- **Wireframe overlay** (W toggle): Second actor with `SetRepresentationToWireframe()`, dark edge color (#333333), slight polygon offset to avoid z-fighting. Overlays on solid — not a replacement.
- **Flat shading** (default): `actor.GetProperty().SetInterpolationToFlat()`
- **Smooth shading** (S toggle): `actor.GetProperty().SetInterpolationToGouraud()`

### Mesh Appearance
- Default mesh color: light gray (#C0C0C0)
- Wireframe overlay color: dark gray (#333333)
- Background: #262626 (matches dark theme)

### Keyboard Shortcuts
| Key | Action |
|---|---|
| W | Toggle wireframe overlay |
| S | Toggle flat/smooth shading |
| F | Fit to view |
| Ctrl+O | Open file dialog |
| Ctrl+Q | Exit |

---

## Error Handling

### OpenGL Context Failure
Catch during `ViewportWidget` initialization. Replace viewport with a `QLabel` showing the FRD error message: "3D rendering unavailable. OpenGL {required_version} not supported on this system. GPU: {gpu_name}, Driver: {driver_version}." Log full GL error details.

### GPU Memory Exhaustion
Catch VTK error callback after polydata upload to GPU. Show warning in status bar: "Mesh too complex for GPU ({face_count} faces). Try a smaller file." Do not crash. Mesh remains in memory but may not render.

### Frame Rate Drops
Log frame time at DEBUG level if >100ms. No user-facing action for MVP.

### Viewport Resize
VTK handles projection matrix recalculation internally. `QVTKRenderWindowInteractor` handles resize events. No blank frames — VTK uses retained buffer.

---

## File Structure

```
src/meshscope/
├── ui/
│   ├── __init__.py
│   ├── main_window.py      — MainWindow (QMainWindow): menus, toolbar, status bar, file loading
│   └── viewport_widget.py  — ViewportWidget: QVTKRenderWindowInteractor subclass, empty/error states
├── vtk_adapter/
│   ├── __init__.py
│   ├── mesh_adapter.py     — mesh_data_to_polydata() stateless converter
│   └── scene_manager.py    — SceneManager: mesh actor, lights, camera, render modes
└── core/
    └── (existing from Feature 1)

tests/
├── unit/
│   ├── test_mesh_adapter.py    — vtkPolyData conversion correctness
│   └── test_scene_manager.py   — actor creation, render mode toggles, lighting
├── ui/
│   ├── test_main_window.py     — toolbar, menus, status bar, state transitions, drag-drop
│   └── test_viewport.py        — widget creation, empty/error states
└── (existing from Feature 1)
```

---

## Test Strategy

### Tier 1 — Pure Python, no GUI (CI-safe everywhere)
- `mesh_data_to_polydata()`: correct vertex count, face count, data types in output `vtkPolyData`
- `SceneManager`: actor creation, wireframe/shading state toggles, light setup, fit-to-view calls. Uses `vtkRenderer` in off-screen mode.

### Tier 2 — Qt required (`QT_QPA_PLATFORM=offscreen` for CI)
- `MainWindow` construction: toolbar buttons exist, menu actions wired, status bar shows "Ready"
- State transitions: empty → loading → success, empty → loading → error
- Keyboard shortcuts: W/S/F trigger correct SceneManager methods (mocked)
- Drag-drop: `dropEvent` with mocked file path triggers load
- File dialog filter: correct extensions

### Tier 3 — Manual verification
- Visual rendering correctness (mesh appears, rotates, wireframe overlays)
- OpenGL error fallback display
- Drag-drop from Finder/Explorer
- Cross-platform (Phase 3)

### What We Don't Test
VTK rendering output (pixel comparison). Fragile and GPU-dependent. We test that the right VTK calls are made, not what pixels come out.

### Test Fixtures
Reuse cube fixtures from Feature 1. No new fixtures needed.

---

## Accessibility

Per Project Bible Section 14 (hard constraint):
- All toolbar buttons: icon + text label
- Keyboard shortcuts for all viewport actions (W, S, F, Ctrl+O)
- Status bar messages are text-only (no color-only indicators)
- Wireframe/shading active state: button border/outline change, not color fill
- All widgets get `setAccessibleName()` for screen readers
- 4.5:1 contrast ratio for all text on #262626 background

---

## Decisions

- **B-lite SceneManager**: Owns scene actors with minimal API. Seam exists for Features 5, 9, 10 to add actors later without refactoring ViewportWidget.
- **Synchronous loading**: No threading for MVP. `processEvents()` keeps UI responsive. Thread if <5s target missed.
- **No Info Panel**: Feature 3 scope. Dock area reserved but empty.
- **No export prompt on re-load**: No unsaved changes concept until Feature 4.
- **Shading shortcut**: S key (standard in Blender). 2-state toggle: flat ↔ smooth.
- **Wireframe is overlay, not replacement**: W toggles a second wireframe actor on top of solid shading.
