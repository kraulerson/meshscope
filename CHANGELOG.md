# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/) with extended categories
for handoff clarity. Categories are ordered by impact severity.

<!--
  Category definitions:
  - Security: Vulnerability fixes, dependency patches for CVEs, auth changes
  - Data Model: Schema migrations, data format changes, rollback notes
  - Added: New features, new endpoints, new commands
  - Changed: Modifications to existing behavior
  - Fixed: Bug fixes (reference BUGS.md entry if applicable)
  - Removed: Removed features, deprecated endpoints
  - Infrastructure: CI/CD changes, dependency updates, configuration changes, tooling
  - Documentation: Significant doc updates (new ADRs, updated threat model, revised user guide)
-->

## [Unreleased]

### Security
### Data Model

### Added

- **Feature 9 — Measurement Tool** (2026-04-08): Point-to-point distance measurement with dedicated mode (M key), vtkCellPicker ray-cast, 3-measurement FIFO cap, info panel display
- **Feature 10 — Cross-Section Slice Plane** (2026-04-08): Interactive clipping plane (C key) with vtkImplicitPlaneWidget2, X/Y/Z presets, floating overlay, terracotta interior fill via vtkClipClosedSurface
- Measurement dataclass with compute_distance, MeasurementManager for VTK line/endpoint actors
- SlicePlaneManager with full VTK clipping pipeline and vtkClipPolyData fallback
- SliceOverlayWidget floating Qt panel with preset buttons and Reset
- Window-level Escape shortcut exits active modes (slice, measure)

### Changed
### Fixed

- UAT5: Measurement left-click consumed in measure mode to prevent VTK orbit rotation
- UAT5: Slice overlay panel enlarged for visibility (was compressed to invisible)
- UAT5: Interactor passthrough fixed — pass QVTKRenderWindowInteractor directly
- UAT5: InsideOut enabled on fallback vtkClipPolyData clipper
- UAT5: Measurement invalidation triggers render to clear visuals on undo

### Removed

### Infrastructure

- Added `--include-module=vtkmodules.vtkInteractionWidgets` to Nuitka config

### Documentation

- Design specs for Features 9 and 10 in `docs/superpowers/specs/`
- Implementation plans for Features 9 and 10 in `docs/superpowers/plans/`
- UAT Session 5 interactive HTML test form (28 scenarios, 28/28 passing)

## [0.1.0-alpha] — Phase 2 Construction (2026-04-06 – 2026-04-08)

### Security

- File loading uses format-specific loaders only — never trimesh generic `load()` (threat model mitigation)
- Export uses atomic writes (temp file + rename) to prevent partial file corruption
- Symlink detection on export paths with user warning if target differs from selected path

### Data Model

- Schema-versioned JSON config (`~/Library/Application Support/meshscope/config.json`) with atomic persistence and corrupt-file recovery

### Added

- **Feature 1 — File Loading** (2026-04-06): Load STL, OBJ, 3MF, PLY via dialog, drag-drop, or CLI with full validation and computed metadata
- **Feature 2 — 3D Viewport** (2026-04-06): Interactive VTK viewport with orbit, pan, zoom, fit-to-view, wireframe, flat/smooth shading, and complete main window shell
- **Feature 3 — Mesh Info Panel** (2026-04-07): Dockable panel with file info, geometry counts, bounding box, manifold/volume status, and unit mismatch warning
- **Feature 4 — Format Conversion** (2026-04-07): Export As to STL (binary), OBJ, 3MF, PLY with data loss warnings and atomic writes
- **Feature 5 — Print Bed Visualization** (2026-04-07): Print volume overlay with presets (Ender 3, Prusa MK4, Voron 2.4, custom), overflow detection with hatching
- **Feature 6 — Manifold/Watertight Check** (2026-04-07): Topology analysis with hole, open edge, degenerate face, and non-manifold edge counts; viewport highlighting with distinct line styles
- **Feature 7 — Basic Mesh Repair** (2026-04-07): One-click repair for flipped normals, holes, degenerate faces with undo/redo and pre-repair impact warnings
- **Feature 8 — Scale/Rotate/Mirror** (2026-04-08): Tabbed Transform dialog with uniform scale, axis rotation, and axis mirror — all undoable
- Undo/redo stack with ring buffer (max 10 entries, scaled down for large meshes)
- Keyboard shortcuts: Open (Ctrl+O), Analyze (A), Repair (R), Transform (Ctrl+T), Undo (Ctrl+Z), Redo (Ctrl+Shift+Z), Print Bed (P)
- Dark theme default with 4.5:1 contrast ratio and colorblind-accessible indicators

### Changed
### Fixed

- UAT4-001: Camera position preserved during transforms, undo, redo, and repair (was resetting to default view)
- UAT4-002: Rotate axis buttons use QButtonGroup for proper exclusive selection (was allowing deselection)
- UAT4-003: Mirror axis buttons use QButtonGroup for proper exclusive selection (same fix as UAT4-002)
- UAT4-004: Rotation axis labels now show direction indicators using right-hand rule arrows (Y→Z, Z→X, X→Y)
- UAT4-005: Print bed positioned under model (centered in X/Y, floor at model base) instead of at world origin
- UAT4-006: Axis button checked state uses explicit stylesheet for visibility on macOS
- UAT4-007: X/Y/Z axis arrows with labels added at print bed origin corner for orientation
- UAT1: Trackball camera interaction style (was joystick default)
- UAT2: Keyboard focus and visible focus indicator for info panel section headers
- UAT3: Custom dialog, bed persistence, and highlight checkbox fixes

### Removed
### Infrastructure

- Nuitka build configuration validated — uses targeted `--include-module` for VTK (not `--include-package`, which causes infinite dependency analysis)
- Pre-commit hooks: trim whitespace, ruff, gitleaks, semgrep
- Test gate script for UAT session enforcement every 2 features
- Schema-versioned config system with atomic persistence

### Documentation

- Product Manifesto, Project Bible, Approval Log created during Phase 0-1
- Design specs for all 8 features in `docs/superpowers/specs/`
- Implementation plans for all 8 features in `docs/superpowers/plans/`
- UAT test sessions 1-4 with interactive HTML forms
