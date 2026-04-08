# Print Bed Visualization — Design Spec

**Feature:** 5 — Print Bed Visualization
**Date:** 2026-04-07
**Status:** Approved

---

## Summary

Toggle a 3D print volume overlay in the viewport showing a wireframe box + grid floor for a selected printer preset. Detects when the loaded mesh exceeds the print volume and indicates overflow with hatching on the floor + status bar text. Includes a full schema-versioned user preferences system for persisting the selected preset.

---

## Requirements (from Product Manifesto)

- Scaled grid overlay with printer presets
- Ender 3 220x220, Prusa MK4 250x210, Voron 2.4 350x350, custom
- Overflow detection with hatching + text
- Extended to full print volume (X/Y/Z) per Orchestrator decision

---

## Architecture

Two new modules:

- **`src/meshscope/core/config.py`** — Schema-versioned JSON config with load/save/atomic write/corrupt-file recovery. Stores print bed preset selection and custom dimensions. Reusable by future features.
- **`src/meshscope/vtk_adapter/print_bed.py`** — `PrintBedManager` class creating VTK actors for grid floor, wireframe volume box, and overflow hatching. Pure rendering logic, no UI dependencies.

MainWindow owns toggle state and preset selection. SceneManager delegates to PrintBedManager.

---

## Config Module

New `src/meshscope/core/config.py`:

- `AppConfig` class wrapping a dict with schema version
- `load_config() -> AppConfig` — loads from OS-standard config path, validates schema version, recovers from corrupt file by resetting to defaults
- `save_config(config: AppConfig) -> None` — atomic write (temp file + os.replace)
- Config path: `_get_config_dir() / "config.json"` (reuses path helper from logging.py)
- Schema version 1 with forward migration support

Default config:
```json
{
  "version": 1,
  "print_bed": {
    "preset": "ender_3",
    "custom_x": 220,
    "custom_y": 220,
    "custom_z": 250
  }
}
```

### Schema Recovery

- Missing file → create with defaults
- Invalid JSON → log warning, reset to defaults
- Unknown schema version → log warning, reset to defaults
- Missing keys → merge with defaults (preserve valid keys)

---

## Printer Presets

Defined as constant in `print_bed.py`:

```python
PRINTER_PRESETS = {
    "ender_3":    {"name": "Ender 3",        "x": 220, "y": 220, "z": 250},
    "prusa_mk4":  {"name": "Prusa MK4",      "x": 250, "y": 210, "z": 210},
    "voron_2_4":  {"name": "Voron 2.4",       "x": 350, "y": 350, "z": 350},
    "bambu_x1c":  {"name": "Bambu X1 Carbon", "x": 256, "y": 256, "z": 256},
    "bambu_p1s":  {"name": "Bambu P1S",       "x": 256, "y": 256, "z": 256},
}
```

- Preset keys match config storage
- "Custom" is not a preset — reads X/Y/Z from config's custom fields
- Custom dialog validates: dimensions > 0, warns if > 1000mm

---

## PrintBedManager (VTK Rendering)

`src/meshscope/vtk_adapter/print_bed.py`:

### Grid Floor
- vtkPolyData with line actors at 10mm intervals on the Z=0 plane
- Subtle color (#3a5a3a) to not compete with the mesh
- Covers the full X/Y bed dimensions

### Wireframe Box
- 12-edge wireframe showing the full X/Y/Z volume boundary
- Slightly brighter color (#5a8a5a)
- Thin lines (line width 1-2)

### Overflow Hatching
- When mesh bounding box exceeds bed dimensions on any axis, diagonal line actors are added to the floor beyond the bed boundary
- Hatching pattern (diagonal lines), not solid fill — accessible without color
- Only shown on axes that overflow

### Methods

- `create_actors(x: int, y: int, z: int) -> list[vtkActor]` — builds grid + box actors
- `create_overflow_actors(bed_x: int, bed_y: int, bed_z: int, mesh_bbox: BoundingBox) -> list[vtkActor]` — builds overflow hatching
- `get_overflow_text(bed_x: int, bed_y: int, bed_z: int, mesh_bbox: BoundingBox) -> str | None` — returns "Exceeds volume: X +80mm, Z +15mm" or None

### Overflow Calculation

- Compares mesh bounding box dimensions (size_x, size_y, size_z) to bed dimensions
- No model repositioning — dimension comparison only
- If mesh is 300mm wide and bed is 220mm, overflow = 80mm regardless of mesh position

---

## SceneManager Integration

Add to `src/meshscope/vtk_adapter/scene_manager.py`:

- `show_print_bed(x: int, y: int, z: int, mesh_bbox: BoundingBox) -> str | None` — creates actors via PrintBedManager, adds to renderer, returns overflow text
- `hide_print_bed() -> None` — removes all print bed actors
- `print_bed_visible: bool` property
- `_print_bed_actors: list[vtkActor]` — stored separately from mesh actors
- When `clear()` is called, also removes print bed actors

---

## MainWindow Integration

### Toolbar
- Toggle button: QAction("Bed", checkable=True, shortcut="P", disabled until mesh loaded)
- QComboBox dropdown: Ender 3 | Prusa MK4 | Voron 2.4 | Bambu X1 Carbon | Bambu P1S | Custom...
- Dropdown disabled until mesh loaded
- Selecting a preset from dropdown enables bed if off

### Menu
- View > Print Bed (toggle, mirrors toolbar button)
- View > Print Bed Preset > submenu: all presets + Custom...

### Custom Size Dialog
- QDialog with 3 QSpinBox fields (X, Y, Z) in mm
- Range: 1–2000mm
- OK / Cancel
- Validation: > 0 required, > 1000mm shows warning "Verify dimensions are in millimeters"

### Behavior
- P key or toolbar button toggles bed on/off
- Preset change saves to config immediately
- On app launch, restores last preset from config
- When a new mesh loads while bed is visible, overflow recalculates
- Overflow text shown in status bar (e.g., "Exceeds volume: X +80mm")
- No overflow → status bar shows normal message

### Disabled State
- Bed toggle and preset dropdown disabled when no mesh loaded
- Enabled/disabled alongside render actions (wireframe, shading, fit, export)

---

## Accessibility

- **Toggle state:** Checkable QAction with accessible name "Print bed, enabled" / "Print bed, disabled"
- **Overflow:** Hatching pattern (not color alone) + status bar text with exact mm values
- **Custom dialog:** All spinboxes have accessible names ("Bed width X in millimeters", etc.)
- **Keyboard:** P toggles bed. Dropdown navigable with arrow keys.
- **Contrast:** Grid #3a5a3a and box #5a8a5a visible against #262626 background

---

## Component States

| State | Bed Toggle | Dropdown |
|---|---|---|
| **Empty** (no mesh) | Disabled | Disabled |
| **Loading** | Disabled | Disabled |
| **Success** (mesh loaded) | Enabled | Enabled |
| **Error** | Disabled | Disabled |

---

## Scope Boundaries

**In scope (Feature 5):**
- Print volume wireframe box + grid floor
- 5 printer presets + custom
- Overflow detection (hatching + text)
- Full preferences system (config.py)
- Toolbar toggle + dropdown + menu
- Custom size dialog
- Preset persistence

**Out of scope (deferred):**
- Model auto-centering on bed → not needed (dimension comparison)
- Bed Z-axis label/ruler → Post-MVP
- Multiple model positioning on bed → Post-MVP
- Print bed in exported files → not applicable

---

## Nuitka Configuration

No new VTK modules needed. `vtkFiltersSources` (for vtkPlaneSource) and `vtkRenderingFreeType` (for text) are already included.

---

## Revision History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-04-07 | Initial design from brainstorming session. |
