# Viewport & UI Component Interface

This document describes the public API surface for the UI layer: main window, viewport, info panel, transform dialog, and VTK adapter components.

## Module: `meshscope.main`

### Entry Point

```python
def main() -> None
```
Initializes QApplication, creates MainWindow, and runs the event loop. Accepts optional file path as first CLI argument.

---

## Module: `meshscope.ui.main_window`

### `MainWindow` (QMainWindow)

Main application window. Hosts the VTK viewport, toolbar, menu bar, info panel, and status bar. Handles file loading via dialog, drag-drop, and CLI argument.

```python
def __init__(self, file_path: str | None = None) -> None
```

#### Constants

- `SUPPORTED_EXTENSIONS: set[str]` — `{".stl", ".obj", ".3mf", ".ply"}`
- `FILE_FILTER: str` — Dialog filter for open operations
- `EXPORT_FILTER: str` — Dialog filter for export operations

#### Key Actions (QAction)

| Action | Shortcut | Description |
|---|---|---|
| Open | Ctrl+O | Open file dialog |
| Export As | Ctrl+Shift+S | Export to different format |
| Analyze | A | Run manifold/watertight analysis |
| Repair | R | Open repair dialog |
| Transform | Ctrl+T | Open transform dialog |
| Undo | Ctrl+Z | Undo last operation |
| Redo | Ctrl+Shift+Z | Redo last undone operation |
| Print Bed | P | Toggle print bed overlay |
| Wireframe | W | Toggle wireframe overlay |
| Fit to View | F | Auto-frame camera |

---

## Module: `meshscope.ui.viewport_widget`

### `ViewportWidget` (QWidget)

Hosts the VTK render window with state-based overlays: empty (prompt text), loading, success (VTK viewport), error (error message).

```python
def __init__(self, parent: QWidget | None = None) -> None
```

#### Properties

| Property | Type | Description |
|---|---|---|
| `renderer` | `vtkRenderer` | VTK renderer instance |
| `scene_manager` | `SceneManager` | Scene content manager |
| `state` | `str` | Current state: `"empty"`, `"loading"`, `"success"`, `"error"` |
| `vtk_interactor` | `QVTKRenderWindowInteractor` | VTK-Qt bridge |

#### Methods

```python
def set_state(self, state: str) -> None
```
Set viewport state. Valid values: `"empty"`, `"loading"`, `"success"`, `"error"`.

```python
def show_error(self, message: str) -> None
```
Show an error message and switch to error state.

```python
def vtk_render(self) -> None
```
Trigger a VTK render update.

---

## Module: `meshscope.ui.info_panel`

### `CollapsibleSection` (QWidget)

A section with a clickable header that toggles content visibility.

```python
def __init__(self, title: str, parent: QWidget | None = None, *, expanded: bool = True) -> None
```

Properties: `is_expanded`, `header_button`, `content_area`, `content_layout`

### `InfoPanel` (QDockWidget)

Dockable panel with four collapsible sections: File Info, Geometry, Dimensions, Status. Plus an Analysis section that appears after `show_analysis()`.

```python
def __init__(self, parent: QWidget | None = None) -> None
```

#### Methods

```python
def set_document(self, doc: MeshDocument) -> None
```
Populate all sections from a MeshDocument.

```python
def clear(self) -> None
```
Reset to empty state.

```python
def show_analysis(self, analysis: MeshAnalysis) -> None
```
Show analysis results in the Analysis section.

```python
def clear_analysis(self) -> None
```
Hide the Analysis section.

Property: `highlight_checkbox -> QCheckBox` — The "Highlight in viewport" checkbox.

---

## Module: `meshscope.ui.transform_dialog`

### `TransformDialog` (QDialog)

Tabbed dialog with Scale, Rotate, and Mirror tabs.

```python
def __init__(self, bounding_box: BoundingBox, parent: QWidget | None = None) -> None
```

#### Accessors

| Method | Returns | Description |
|---|---|---|
| `operation()` | `str` | `"scale"`, `"rotate"`, or `"mirror"` |
| `scale_factor()` | `float` | Scale multiplier (min 0.001) |
| `rotate_axis()` | `str` | `"x"`, `"y"`, or `"z"` |
| `rotate_degrees()` | `float` | Rotation angle |
| `mirror_axis()` | `str` | `"x"`, `"y"`, or `"z"` |

---

## Module: `meshscope.vtk_adapter.scene_manager`

### `SceneManager`

Manages VTK scene contents: mesh actor, wireframe overlay, highlights, print bed, lights, and camera.

```python
def __init__(self, renderer: vtkRenderer) -> None
```

#### Methods

| Method | Signature | Description |
|---|---|---|
| `display_mesh` | `(polydata: vtkPolyData, *, auto_fit: bool = True) -> None` | Display mesh, replacing existing. `auto_fit=False` preserves camera position. |
| `clear` | `() -> None` | Remove all mesh actors |
| `show_highlights` | `(analysis, vertices, faces) -> None` | Add problem highlight actors |
| `hide_highlights` | `() -> None` | Remove highlight actors |
| `show_print_bed` | `(x: int, y: int, z: int, bbox: BoundingBox) -> str \| None` | Show bed overlay. Returns overflow text or None. Positions bed under model. |
| `hide_print_bed` | `() -> None` | Remove bed actors |
| `set_wireframe_overlay` | `(enabled: bool) -> None` | Toggle wireframe |
| `set_smooth_shading` | `(enabled: bool) -> None` | Toggle flat/smooth shading |
| `fit_to_view` | `() -> None` | Auto-frame camera |
| `pick_surface_point` | `(display_x: int, display_y: int) -> tuple[float, float, float] \| None` | Cast ray from screen coords, return 3D hit point or None |
| `show_measurements` | `(measurements: list[Measurement]) -> None` | Display measurement line + endpoint actors |
| `hide_measurements` | `() -> None` | Remove all measurement actors |
| `show_pending_point` | `(point: tuple[float, float, float], index: int) -> None` | Show point A marker before B is placed |
| `hide_pending_point` | `() -> None` | Remove pending point marker |
| `activate_slice_plane` | `(interactor: Any) -> None` | Show plane widget + start clipping |
| `deactivate_slice_plane` | `() -> None` | Remove plane widget, restore full mesh |
| `set_slice_preset` | `(axis: str) -> None` | Snap plane to X/Y/Z axis through center |
| `reset_slice_plane` | `() -> None` | Return plane to model center |
| `update_slice_mesh` | `(polydata: vtkPolyData) -> None` | Recalculate clip after mesh change |

#### Properties

| Property | Type |
|---|---|
| `highlights_visible` | `bool` |
| `print_bed_visible` | `bool` |
| `has_mesh` | `bool` |
| `wireframe_overlay_enabled` | `bool` |
| `smooth_shading_enabled` | `bool` |
| `measurements_visible` | `bool` |
| `slice_active` | `bool` |
| `slice_current_preset` | `str \| None` |

---

## Module: `meshscope.vtk_adapter.print_bed`

### Constants

- `PRINTER_PRESETS: dict[str, dict]` — Ender 3, Prusa MK4, Voron 2.4, Bambu X1C, Bambu P1S
- `GRID_SPACING_MM: int = 10`
- Color constants: `GRID_COLOR`, `BOX_COLOR`, `OVERFLOW_COLOR`, `AXIS_X_COLOR`, `AXIS_Y_COLOR`, `AXIS_Z_COLOR`

### `PrintBedManager`

```python
def create_actors(self, x: int, y: int, z: int) -> list[vtkActor]
```
Grid floor + wireframe box + axis labels.

```python
def create_overflow_actors(self, bed_x: int, bed_y: int, bed_z: int, bbox: BoundingBox) -> list[vtkActor]
```
Diagonal hatching for overflow regions.

### Functions

```python
def get_overflow_text(bed_x: int, bed_y: int, bed_z: int, bbox: BoundingBox) -> str | None
```
Returns overflow description text, or None if model fits.

---

## Module: `meshscope.vtk_adapter.measurement_manager`

### Constants

- `MEASUREMENT_COLORS: dict[int, tuple[float, float, float]]` — 1: amber, 2: sky blue, 3: light green
- `MEASUREMENT_LINE_WIDTH: float = 2.0`
- `ENDPOINT_MARKER_RADIUS: float = 0.8`

### `MeasurementManager`

```python
def create_measurement_actors(
    self, point_a: tuple, point_b: tuple, index: int
) -> list[vtkActor]
```
Returns [line_actor, endpoint_a_actor, endpoint_b_actor].

```python
def create_pending_point_actor(
    self, point: tuple, index: int
) -> vtkActor
```
Single endpoint marker for point A before B is placed.

---

## Module: `meshscope.vtk_adapter.slice_plane_manager`

### Constants

- `CAP_COLOR: tuple = (0.753, 0.376, 0.251)` — terracotta #c06040
- `PLANE_WIDGET_COLOR: tuple = (0.537, 0.706, 0.980)` — theme blue #89b4fa

### `SlicePlaneManager`

```python
def __init__(self, renderer: vtkRenderer, interactor: vtkRenderWindowInteractor) -> None
def activate(self, polydata: vtkPolyData, bounds: tuple[float, ...]) -> None
def deactivate(self) -> None
def set_preset(self, axis: str, bounds: tuple[float, ...]) -> None
def reset_to_center(self, bounds: tuple[float, ...]) -> None
def update_mesh(self, polydata: vtkPolyData, bounds: tuple[float, ...]) -> None
```

Properties: `is_active -> bool`, `current_preset -> str | None`

---

## Module: `meshscope.ui.slice_overlay`

### `SliceOverlayWidget` (QWidget)

Floating overlay for slice plane controls.

Signals:
- `preset_clicked(str)` — emits "x", "y", or "z"
- `reset_clicked()` — reset button clicked

```python
def set_active_preset(self, axis: str | None) -> None
def show_overlay(self) -> None
def hide_overlay(self) -> None
```
