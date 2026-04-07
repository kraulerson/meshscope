# Format Conversion — Design Spec

**Feature:** 4 — Format Conversion
**Date:** 2026-04-07
**Status:** Approved

---

## Summary

Export the current mesh to STL (binary), OBJ, 3MF, or PLY via a File > Export As dialog. Uses trimesh for format-specific export. Atomic writes (temp file + rename) prevent data loss. Pre-export warning dialogs inform the user when a format may lose data.

---

## Requirements (from Product Manifesto)

- Export As to STL (binary default), OBJ, 3MF, PLY
- Current mesh state including transforms
- STL ASCII/binary toggle is Post-MVP (P2)

---

## Architecture

- **New file:** `src/meshscope/core/mesh_exporter.py` containing `export_mesh(mesh: MeshData, path: Path, file_type: str) -> None`
- **Conversion:** MeshData (vertices, faces, normals) → trimesh.Trimesh → trimesh format-specific export
- **Atomic write:** Write to temp file in same directory, verify > 0 bytes, os.replace() to final path
- **Symlink detection:** os.path.realpath() check before writing, warn user if target differs
- **No new dependencies.** trimesh already handles all 4 format exports.
- **No Nuitka changes needed.** trimesh export is pure Python + numpy.

---

## Export Pipeline

```
User clicks Export As (Ctrl+Shift+S)
  → QFileDialog with format filter (STL default, OBJ, 3MF, PLY)
  → Detect selected format from filter/extension
  → Check symlink: os.path.realpath() vs selected path
    → If differs: warning dialog "Target resolves to {real_path}. Continue?"
  → Check overwrite source: if export path == doc.source_path
    → Warning dialog "This will overwrite the currently loaded file. Continue?"
  → Check format data loss: if target format has limitations
    → Warning dialog (see Format-Specific Behavior)
  → export_mesh(doc.mesh, path, file_type)
    → MeshData → trimesh.Trimesh (vertices, faces, face_normals)
    → trimesh.export(temp_path, file_type=file_type)
    → Validate temp file > 0 bytes
    → os.replace(temp_path, final_path)  # atomic rename
  → Success: status bar "Exported to {filename}"
  → Failure: error dialog with message, temp file cleaned up
```

---

## Format-Specific Behavior

| Format | trimesh file_type | Default | Data loss warning | Notes |
|--------|---|---|---|---|
| STL (binary) | `stl` | Yes (default filter) | None | Binary only for MVP. ASCII is Post-MVP P2. |
| OBJ | `obj` | No | "OBJ format may recalculate face normals." | trimesh exports vertex normals, recalculates from faces |
| 3MF | `3mf` | No | None | trimesh handles ZIP packaging internally |
| PLY | `ply` | No | None | Binary PLY output |

QFileDialog filter string: `"STL Files (*.stl);;OBJ Files (*.obj);;3MF Files (*.3mf);;PLY Files (*.ply)"`

STL listed first so it's the default selection.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Write fails (permissions) | Error dialog: "Cannot write to {path}: Permission denied" |
| Write fails (disk space) | Error dialog: "Export failed: {OS error message}" |
| Export produces 0-byte temp file | Delete temp file, error dialog: "Export produced empty file — mesh data may be corrupt" |
| Temp file rename fails | Error dialog with OS error, temp file left for user recovery |
| trimesh export raises exception | Error dialog: "Export failed: {message}", temp file cleaned up |
| User cancels any warning dialog | Export aborted silently, no error |
| User cancels file dialog | No action |

All errors logged at ERROR level with correlation ID. Success logged at INFO level.

---

## MainWindow Integration

- New `export_action = QAction("Export As...", self)` with shortcut Ctrl+Shift+S
- Added to File menu between Open and Exit (with separators)
- Added to toolbar after Open
- Starts disabled, enabled/disabled via `_set_render_actions_enabled()` alongside wireframe/shading/fit
- Status bar shows "Exported to {filename}" on success
- All warning/error dialogs are modal (QMessageBox)
- Accessibility: action has tooltip "Export mesh to another format"

---

## Security

- **Atomic writes:** temp file + os.replace(). Never write directly to the target path.
- **Symlink detection:** Resolve with os.path.realpath(). If resolved path differs from selected path, show warning dialog with both paths. User must confirm to proceed.
- **Post-export validation:** Verify exported file > 0 bytes. Delete and report error if empty.
- **Temp file cleanup:** Always delete temp file on failure (wrapped in try/finally).
- **Overwrite source protection:** If export path matches doc.source_path, show confirmation dialog.

---

## Component States

| State | Export Action |
|---|---|
| **Empty** (no mesh loaded) | Disabled (grayed out) |
| **Loading** | Disabled |
| **Success** (mesh loaded) | Enabled |
| **Error** | Disabled |

---

## Scope Boundaries

**In scope (Feature 4):**
- Export As dialog with format picker
- STL (binary), OBJ, 3MF, PLY export via trimesh
- Atomic writes with post-export validation
- Symlink detection
- Pre-export warning dialogs (format data loss, overwrite source)
- Error handling with user-facing dialogs

**Out of scope (deferred):**
- STL ASCII/binary toggle → Post-MVP P2
- File size preview before export → Post-MVP P2
- Export with transforms applied → Feature 8 (transforms don't exist yet; current mesh state = original mesh for now)
- Batch export / export all formats → not in MVP

---

## Revision History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-04-07 | Initial design from brainstorming session. |
