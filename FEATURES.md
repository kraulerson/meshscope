# Feature Reference

<!--
  This document is a living index of all features built during Phase 2.
  Update at Step 2.5 of every Build Loop iteration alongside the CHANGELOG and Bible.
  Purpose: Give someone a quick orientation to what the app does without reading the Bible.
  For detailed analysis, follow the links to ADRs and interface docs.
-->

## Feature 1: File Loading

**Phase Built:** 2
**Build Date:** 2026-04-06
**Status:** Complete
**Summary:** Load STL, OBJ, 3MF, and PLY mesh files from disk into an in-memory MeshDocument with full validation, error handling, and computed metadata. Supports dialog, drag-drop, and CLI invocation. Target: <5s for 50MB files.
**Design Spec:** `docs/superpowers/specs/2026-04-06-file-loading-design.md`
**Key Interfaces:** [`docs/api and interfaces/mesh-operations.md`](docs/api%20and%20interfaces/mesh-operations.md)
**Related ADRs:** [`docs/ADR documentation/0004-stl-as-primary-format.md`](docs/ADR%20documentation/0004-stl-as-primary-format.md)
**Test Coverage:** Unit (mesh_loader, mesh_data), Integration (load pipeline)
**Known Limitations:** None

---

## Feature 2: 3D Viewport

**Phase Built:** 2
**Build Date:** 2026-04-06
**Status:** Complete
**Summary:** Interactive 3D viewport rendering loaded meshes via VTK with orbit, pan, zoom, fit-to-view, wireframe toggle, and flat/smooth shading. Includes the complete main window shell (menu bar, toolbar, status bar, drag-drop support) making the application end-to-end usable.
**Design Spec:** `docs/superpowers/specs/2026-04-06-3d-viewport-design.md`
**Key Interfaces:** [`docs/api and interfaces/viewport.md`](docs/api%20and%20interfaces/viewport.md)
**Related ADRs:** [`docs/ADR documentation/0001-architecture-selection.md`](docs/ADR%20documentation/0001-architecture-selection.md)
**Test Coverage:** Unit (viewport_widget), UI (main_window)
**Known Limitations:** None

---

## Feature 3: Mesh Info Panel

**Phase Built:** 2
**Build Date:** 2026-04-07
**Status:** Complete
**Summary:** Dockable info panel displaying mesh metadata in four collapsible sections: file info, geometry counts, bounding box dimensions, and manifold/volume status. Includes a warning banner for unit mismatches and updates whenever a file is loaded.
**Design Spec:** `docs/superpowers/specs/2026-04-07-mesh-info-panel-design.md`
**Key Interfaces:** [`docs/api and interfaces/viewport.md`](docs/api%20and%20interfaces/viewport.md)
**Related ADRs:** None
**Test Coverage:** Unit (info_panel), UI (main_window), Accessibility
**Known Limitations:** None

---

## Feature 4: Format Conversion

**Phase Built:** 2
**Build Date:** 2026-04-07
**Status:** Complete
**Summary:** Export the current mesh to STL (binary), OBJ, 3MF, or PLY via File > Export As dialog with data loss warnings. Uses atomic writes (temp file + rename) and symlink detection for safe file handling.
**Design Spec:** `docs/superpowers/specs/2026-04-07-format-conversion-design.md`
**Key Interfaces:** [`docs/api and interfaces/mesh-operations.md`](docs/api%20and%20interfaces/mesh-operations.md)
**Related ADRs:** [`docs/ADR documentation/0004-stl-as-primary-format.md`](docs/ADR%20documentation/0004-stl-as-primary-format.md)
**Test Coverage:** Unit (mesh_exporter), Integration (load-export-reload round-trip)
**Known Limitations:** None

---

## Feature 5: Print Bed Visualization

**Phase Built:** 2
**Build Date:** 2026-04-07
**Status:** Complete
**Summary:** Toggleable 3D print volume overlay with wireframe box, grid floor, and printer presets (Ender 3 220x220, Prusa MK4 250x210, Voron 2.4 350x350, custom). Detects mesh overflow with hatching on the floor and includes a schema-versioned user preferences system for persistent settings.
**Design Spec:** `docs/superpowers/specs/2026-04-07-print-bed-visualization-design.md`
**Key Interfaces:** [`docs/api and interfaces/viewport.md`](docs/api%20and%20interfaces/viewport.md)
**Related ADRs:** None
**Test Coverage:** Unit (print_bed, config), UI (main_window)
**Known Limitations:** None

---

## Feature 6: Manifold/Watertight Check

**Phase Built:** 2
**Build Date:** 2026-04-07
**Status:** Complete
**Summary:** On-demand mesh topology analysis reporting manifold status, hole count, open edge count, degenerate face count, and non-manifold edge count. Problem edges and faces are highlighted in the viewport with distinct line styles (solid, tubes, dashed) for accessibility.
**Design Spec:** `docs/superpowers/specs/2026-04-07-manifold-check-design.md`
**Key Interfaces:** [`docs/api and interfaces/mesh-operations.md`](docs/api%20and%20interfaces/mesh-operations.md)
**Related ADRs:** None
**Test Coverage:** Unit (mesh_analysis), UI (main_window, highlight_manager)
**Known Limitations:** None

---

## Feature 7: Basic Mesh Repair

**Phase Built:** 2
**Build Date:** 2026-04-07
**Status:** Complete
**Summary:** One-click mesh repair fixing flipped normals, small holes, and degenerate faces with full undo/redo support. Non-destructive with pre-repair impact warnings and automatic re-analysis post-repair to close the feedback loop instantly.
**Design Spec:** `docs/superpowers/specs/2026-04-07-basic-mesh-repair-design.md`
**Key Interfaces:** [`docs/api and interfaces/mesh-operations.md`](docs/api%20and%20interfaces/mesh-operations.md)
**Related ADRs:** None
**Test Coverage:** Unit (mesh_repair, undo_stack), UI (main_window)
**Known Limitations:** None

---

## Feature 8: Scale/Rotate/Mirror

**Phase Built:** 2
**Build Date:** 2026-04-08
**Status:** Complete
**Summary:** Uniform scale, axis rotation, and axis mirror transforms accessed through a single tabbed Transform dialog (Ctrl+T). All transforms are undoable, update the viewport and info panel immediately, and center operations on the model's center of mass.
**Design Spec:** `docs/superpowers/specs/2026-04-07-scale-rotate-mirror-design.md`
**Key Interfaces:** [`docs/api and interfaces/mesh-operations.md`](docs/api%20and%20interfaces/mesh-operations.md)
**Related ADRs:** None
**Test Coverage:** Unit (mesh_transform), UI (main_window, transform_dialog)
**Known Limitations:** None

---

## Feature 9: Measurement Tool

**Phase Built:** 2
**Build Date:** 2026-04-08
**Status:** Complete
**Summary:** Point-to-point distance measurement on mesh surfaces. Dedicated measure mode (M key) with crosshair cursor. Click two points on the mesh to measure Euclidean distance in mm. Up to 3 simultaneous measurements with FIFO replacement. Distances displayed in info panel Measurements section with color-coded entries and coordinates.
**Design Spec:** `docs/superpowers/specs/2026-04-08-measurement-tool-design.md`
**Key Interfaces:** [`docs/api and interfaces/mesh-operations.md`](docs/api%20and%20interfaces/mesh-operations.md)
**Related ADRs:** None
**Test Coverage:** Unit (measurement dataclass, compute_distance, MeasurementManager, MeshDocument FIFO), UI (measure mode, event filter, info panel, invalidation)
**Known Limitations:** Left-click orbit disabled in measure mode (right-click/scroll still work)

---

## Feature 10: Cross-Section Slice Plane

**Phase Built:** 2
**Build Date:** 2026-04-08
**Status:** Complete
**Summary:** Interactive clipping plane that slices through the mesh to reveal interior cross-sections. Uses VTK's vtkImplicitPlaneWidget2 for direct manipulation — drag to move, rotate handles to tilt. X/Y/Z preset buttons and Reset in a floating overlay panel. Cross-section interior filled with terracotta color. Toggle with C key.
**Design Spec:** `docs/superpowers/specs/2026-04-08-cross-section-slice-plane-design.md`
**Key Interfaces:** [`docs/api and interfaces/viewport.md`](docs/api%20and%20interfaces/viewport.md)
**Related ADRs:** None
**Test Coverage:** Unit (SlicePlaneManager activation, presets, reset, clipping pipeline), UI (slice toggle, overlay, SceneManager delegation)
**Known Limitations:** vtkClipClosedSurface cap generation may fall back to open clip on non-manifold meshes
