# Functional Requirements Document — meshscope

**Phase:** 0, Step 0.1
**Source:** PROJECT_INTAKE.md Section 2 & 4
**Date:** 2026-04-05

---

## 1. File Loading

### Logic Trigger
If the user opens a file via File > Open dialog, drags a file onto the application window, drags a file onto the application dock/taskbar icon, or passes a file path as a command-line argument, AND the file extension is one of `.stl`, `.obj`, `.3mf`, or `.ply` (case-insensitive), the system must:

1. Validate the file is readable (filesystem permissions, file exists, not a directory).
2. Validate file size is <= 500MB (hard limit from Intake Section 5.1).
3. Parse the file according to its format:
   - **STL:** Detect binary vs. ASCII by inspecting the header. Parse triangle data (normal + 3 vertices per facet). Validate triangle count matches header (binary) or is self-consistent (ASCII).
   - **OBJ:** Parse vertex (`v`), face (`f`), and normal (`vn`) lines. Unsupported directives (materials, textures, groups, curves) are skipped, and a one-time user-visible warning is displayed per file listing the ignored directive types (e.g., "This OBJ file contains materials and texture data which are not supported. These will be ignored.").
   - **3MF:** Unzip the archive. Validate against 3MF core schema. Extract mesh data from the primary model. If multiple meshes exist in the archive, load the first and log a warning listing the others.
   - **PLY:** Parse header to determine ASCII vs. binary format and element definitions. Extract vertex and face data. Validate element counts match header declarations.
4. Construct an in-memory mesh representation (vertex array, face index array, optional normal array).
5. Display the mesh in the 3D viewport.
6. Populate the Mesh Info Panel (Feature 3).
7. Total time from user action to rendered viewport must be < 5 seconds for files up to 50MB.

### Failure States

| Condition | System Response |
|---|---|
| File extension not in supported set | Display error dialog: "Unsupported file format: .{ext}. Supported formats: STL, OBJ, 3MF, PLY." Do not attempt to parse. |
| File size > 500MB | Display error dialog: "File too large: {size}MB. Maximum supported size: 500MB." |
| File not readable (permissions) | Display error dialog: "Cannot read file: {path}. Permission denied." |
| File not found (stale drag reference) | Display error dialog: "File not found: {path}." |
| Corrupt/unparseable file | Display error dialog identifying the specific parse failure: e.g., "Invalid STL: unexpected EOF at byte 4096" or "Invalid OBJ: malformed face definition at line 234." Do not crash. Do not display partial geometry. |
| 3MF archive corrupt or unextractable | Display error dialog: "Invalid 3MF: unable to extract archive. File may be corrupt." |
| File loads but produces zero faces | Display error dialog: "File parsed successfully but contains no geometry (0 faces)." |
| Load exceeds 5 seconds | Display a progress indicator (indeterminate progress bar + "Loading {filename}..." text label). Do not freeze the UI. If loading exceeds 30 seconds, offer a cancel button. |

### Implicit Dependencies
- Requires a mesh parsing library (architecture decision: trimesh, Open3D, or custom parsing — deferred to Phase 1).
- Requires the 3D Viewport (Feature 2) to be operational for display.
- Requires the Mesh Info Panel (Feature 3) to exist for metadata display.

---

## 2. 3D Viewport

### Logic Trigger
If a mesh is loaded (Feature 1 completes successfully), the system must render it in an interactive 3D viewport with the following controls:

1. **Orbit:** Left-click drag rotates the camera around the model center. Rotation is constrained to avoid gimbal lock (use arcball or trackball rotation).
2. **Pan:** Middle-click drag OR Shift+Left-click drag translates the camera parallel to the view plane.
3. **Zoom:** Scroll wheel moves the camera along the view axis. Zoom must have a minimum distance (prevent camera inside model) and a maximum distance (prevent losing the model).
4. **Fit to view:** On initial load and on double-click or keyboard shortcut (F key), auto-frame the model so the entire bounding box is visible with padding.
5. **Default lighting:** At least one directional light that follows the camera (headlight) so the model is always illuminated regardless of rotation. A second fixed ambient light to prevent fully black shadowed faces.
6. **Render mode:** Solid shaded (default). Wireframe overlay toggle (W key). Flat vs. smooth shading toggle.
7. **Background:** Dark neutral background (matches dark theme). No gradient or skybox.

### Failure States

| Condition | System Response |
|---|---|
| OpenGL context creation fails | Display a fallback error panel in the viewport area: "3D rendering unavailable. OpenGL {required_version} not supported on this system. GPU: {gpu_name}, Driver: {driver_version}." Log full GL error. |
| Mesh too large for GPU memory | Detect via GL error after buffer upload. Display warning: "Mesh too complex for GPU ({face_count} faces). Try a smaller file or reduce mesh complexity." Do not crash. |
| Render loop drops below 10 FPS | No automatic action for MVP. Performance optimization is Phase 3. Log frame time if >100ms. |
| Viewport resize | Recalculate projection matrix on resize. No blank frames during resize (use retained buffer). |

### Implicit Dependencies
- Requires OpenGL context via QOpenGLWidget (PySide6). OpenGL version requirement must be determined in Phase 1 (minimum OpenGL 2.1 for broad compatibility, or 3.3 core profile for modern features).
- Requires numpy for efficient vertex/matrix operations.

---

## 3. Mesh Info Panel

### Logic Trigger
If a mesh is loaded, the system must display a persistent information panel (sidebar or bottom panel) showing:

1. **Filename:** Name of the loaded file (without path).
2. **Format:** Detected format and variant (e.g., "STL (binary)", "OBJ (ASCII)", "PLY (binary little-endian)").
3. **Vertex count:** Integer, formatted with thousands separator (e.g., "1,234,567").
4. **Face count:** Integer, formatted with thousands separator.
5. **Bounding box dimensions:** X, Y, Z extents in mm, displayed as "X: 120.50mm x Y: 85.30mm x Z: 45.00mm". Precision: 2 decimal places.
6. **Total surface area:** In mm^2 (< 1,000,000) or cm^2 (>= 1,000,000), formatted with units. Precision: 2 decimal places.
7. **Volume:** In mm^3 or cm^3 (unit auto-selected by magnitude). Only valid for manifold meshes. If non-manifold, display "N/A (non-manifold mesh)" with a text label and icon (not color alone — accessibility constraint).
8. **Manifold status:** "Yes" or "No" with an icon — checkmark for yes, warning triangle for no (not color alone).

All values must update immediately when transforms (Feature 8) are applied.

### Unit Mismatch Detection
If the bounding box of a loaded mesh is suspiciously small (all dimensions < 1mm) or suspiciously large (any dimension > 10,000mm), display a warning in the info panel with a warning icon + text: "Dimensions may indicate a unit mismatch. Consider scaling by 25.4 (inches to mm) or 0.0394 (mm to inches)." This is an informational warning only — no automatic action.

### Failure States

| Condition | System Response |
|---|---|
| Mesh is non-manifold | Display all available metrics. Volume shows "N/A (non-manifold mesh)" with warning icon + text. Do not show a computed volume for non-manifold meshes. |
| Calculation takes > 2 seconds | Display placeholder "Calculating..." text per field. Do not freeze the UI. |
| Mesh has zero faces | Display "0" for vertex/face count, "N/A" for dimensions/area/volume. |

### Implicit Dependencies
- Requires mesh analysis functions (vertex count, face count, bounding box, surface area, volume, manifold check). These may come from the mesh parsing library or need custom implementation.

---

## 4. Format Conversion

### Logic Trigger
If the user selects File > Export As (or Ctrl+Shift+S / Cmd+Shift+S), the system must:

1. Present a save dialog with format selection: STL, OBJ, 3MF, PLY.
2. For STL: export as binary by default (not ASCII). Binary STL is the universal interchange format for 3D printing.
3. Apply the current mesh state (including any transforms from Feature 8) to the export.
4. Write the file to the user-selected path.
5. Verify the written file is > 0 bytes and matches expected approximate size.

### Failure States

| Condition | System Response |
|---|---|
| Write fails (permissions) | Display error dialog: "Cannot write to {path}. Permission denied." |
| Write fails (disk space) | Display error dialog: "Cannot write to {path}. Insufficient disk space ({available} free, {needed} required)." |
| Target format cannot represent all source data | Display warning before export: e.g., "OBJ normals will be recalculated. Original normal data may differ." Proceed on user confirmation. |
| Export produces 0-byte file | Detect and delete the 0-byte file. Display error: "Export failed: output file is empty. The mesh data may be corrupt." |
| Export to same file as source while source is loaded | Warn: "Overwriting the currently loaded file. Continue?" with Yes/No. |

### Implicit Dependencies
- Requires mesh serialization for each format. Library support (trimesh/Open3D) or custom writers.
- Requires the current transform state from Feature 8.

---

## 5. Print Bed Visualization

### Logic Trigger
If the user activates print bed view (via toolbar toggle button or View menu), the system must:

1. Display a scaled grid in the viewport representing the selected printer bed.
2. Preset bed sizes:
   - Ender 3: 220mm x 220mm
   - Prusa MK4: 250mm x 210mm
   - Voron 2.4: 350mm x 350mm
   - Custom: user enters X and Y dimensions in mm
3. Position the model on the bed (centered, bottom face aligned to bed surface).
4. Grid lines at 10mm intervals with labeled axes.
5. Bed boundary displayed as a distinct border.

### Overflow Detection
If the model exceeds bed dimensions in any axis:
- Visually indicate overflow: the portion of the model extending beyond the bed boundary is marked with a distinct pattern (hatching or dashed outline — not color alone).
- Display a text warning in the info panel: "Model exceeds bed by X: +{n}mm, Y: +{n}mm" (only axes that overflow).

### Failure States

| Condition | System Response |
|---|---|
| Custom dimensions <= 0 | Reject input: "Bed dimensions must be positive values." |
| Custom dimensions > 1000mm | Accept but warn: "Bed size exceeds 1000mm. Verify dimensions are in millimeters." |
| Model is flat (no Z height) | Display on bed normally. No overflow warning for Z. |

### Implicit Dependencies
- Requires the 3D Viewport (Feature 2) to render the grid.
- Requires bounding box data from Feature 3 for overflow calculations.
- Requires user preferences persistence (Feature: Settings) for last-used bed preset.

### Design Decision (Orchestrator-confirmed)
- **Prusa MK4 bed size:** Use real manufacturer specs: 250mm x 210mm.

---

## 6. Manifold/Watertight Check

### Logic Trigger
If the user triggers a printability check (via toolbar button or Analyze menu), the system must analyze the mesh and report:

1. **Manifold status:** Yes/No with icon (checkmark / warning triangle — not color alone).
2. **Hole count:** Number of boundary loops (open edges forming holes). 0 = watertight.
3. **Open edge count:** Total number of edges that border only one face.
4. **Degenerate face count:** Faces with zero area (collapsed triangles).
5. **Non-manifold edge count:** Edges shared by more than 2 faces.
6. **Flipped normal count:** Faces whose normals are inconsistent with their neighbors (requires manifold mesh for reliable detection).

Results displayed in a dedicated panel or section of the info panel. Each metric has a label, numeric value, and status icon.

### Visual Feedback
- If the mesh has issues, offer to highlight problem areas in the viewport:
  - Open edges: highlighted with a distinct line style (thick dashed lines + text label "open edge").
  - Non-manifold edges: highlighted with a different line style.
  - Degenerate faces: highlighted with a pattern fill.
- All highlighting must be distinguishable without color (use line styles, patterns, labels — accessibility constraint).

### Failure States

| Condition | System Response |
|---|---|
| Analysis takes > 10 seconds | Show progress indicator with elapsed time. Do not freeze the UI. Allow cancel. |
| Mesh is empty (0 faces) | Display: "No geometry to analyze." |
| Analysis produces inconsistent results | Log warning. Display results with caveat: "Analysis may be incomplete for highly irregular meshes." |

### Implicit Dependencies
- Requires mesh topology analysis functions. These are computationally expensive for large meshes.
- Results feed into Feature 7 (Mesh Repair) to determine what repairs are possible.

---

## 7. Basic Mesh Repair

### Logic Trigger
If the mesh has issues detected by Feature 6 (holes, flipped normals), the system must offer repair through a toolbar button or Analyze > Repair menu:

1. **Fill small holes:** Automatically fill boundary loops where the hole diameter is below a threshold (default: shortest bounding box dimension / 10). Triangulate the fill.
2. **Fix normals:** Orient all face normals consistently (outward-facing for manifold meshes).
3. **Remove degenerate faces:** Delete zero-area faces.
4. **Non-destructive operation:** Repair operates on a copy of the mesh. The original remains accessible via Undo (Ctrl+Z / Cmd+Z).

### Pre-Repair Validation
Before applying repairs, calculate the impact:
- If repair would change vertex count by > 5%, display warning: "Repair will add/remove {n} vertices ({pct}% change). This may significantly alter geometry. Continue?"
- If repair would change face count by > 5%, display same warning with face counts.
- Display a summary of planned repairs before applying: "Fix {n} flipped normals, fill {n} holes, remove {n} degenerate faces."

### Failure States

| Condition | System Response |
|---|---|
| Repair fails completely | Display error: "Repair failed: {reason}. Original mesh is unchanged." |
| Repair is partial (some holes too large) | Display summary: "Repaired: {n} holes filled, {n} normals fixed. Remaining: {n} holes too large to fill automatically (diameter > {threshold}mm)." |
| Undo not available (at undo stack root) | Grey out Undo button/menu. Display "Nothing to undo" in status bar on attempt. |
| Multiple sequential repairs | Each repair operation is a separate undo entry. Undo reverses one repair at a time. |

### Implicit Dependencies
- Requires Feature 6 (Manifold Check) results to determine what needs repair.
- Requires an undo stack implementation (shared with Feature 8 transforms).

---

## 8. Scale / Rotate / Mirror

### Logic Trigger
If the user applies a transform via the toolbar or Edit menu:

1. **Scale:**
   - By factor: multiply all vertex positions by a uniform scalar. Factor must be > 0.
   - To target dimension: user specifies desired dimension for one axis (e.g., "X = 100mm"); system calculates and applies uniform scale factor.
   - Non-uniform scale: user specifies per-axis factors. Allow but warn: "Non-uniform scaling may distort the mesh."
2. **Rotate:**
   - By degrees around X, Y, or Z axis. Input accepts any numeric value (-360 to 360 typical, but allow arbitrary).
   - Apply rotation to all vertices around the model's center of mass (not world origin).
3. **Mirror:**
   - Across X, Y, or Z plane through the model's center.
   - Mirror reverses face winding order (normals must be flipped to maintain correct orientation).

All transforms must:
- Update the 3D Viewport immediately.
- Update the Mesh Info Panel (bounding box, surface area, volume) immediately.
- Be undoable (each transform is a separate undo entry).
- Be composable (multiple transforms accumulate).

### Failure States

| Condition | System Response |
|---|---|
| Scale factor of 0 | Reject: "Scale factor must be greater than zero." |
| Scale factor negative (not mirror) | Reject: "Use the Mirror tool for reflections. Scale factor must be positive." |
| Target dimension of 0 | Reject: "Target dimension must be greater than zero." |
| Rotation with no mesh loaded | Grey out controls. Status bar: "Load a mesh to use transform tools." |
| Extremely large scale (> 10,000x) | Accept but warn: "Scale factor {n}x will produce a mesh {size}mm in diameter. Continue?" |

### Implicit Dependencies
- Requires the undo stack (shared with Feature 7).
- Requires efficient vertex transformation (numpy matrix operations).

---

## 9. Measurement Tool

### Logic Trigger
If the user activates the measurement tool (toolbar toggle or Tools menu), and clicks two points on the mesh surface:

1. **Point placement:** Each click performs a ray-mesh intersection test. The point is placed at the exact intersection point on the mesh surface.
2. **Distance display:** After the second point, display the Euclidean distance between the two points in mm (precision: 2 decimal places). Display as a text label positioned at the midpoint of the measurement line.
3. **Visual line:** Draw a visible line connecting the two points in the viewport. Line must be visible regardless of mesh color/shading (use contrasting style — e.g., dashed line with text label).
4. **Multiple measurements:** Support at least 3 simultaneous measurements visible on screen. Each measurement has a numbered label (M1, M2, M3).
5. **Clear measurements:** Toolbar button or Escape key to clear all measurements. Individual measurement deletion via right-click context menu.

### Failure States

| Condition | System Response |
|---|---|
| Click misses the mesh (empty space) | Do not place a measurement point. Show a subtle crosshair snap indicator that the click did not hit geometry (e.g., a brief "no hit" icon at cursor position). |
| First point placed, second click misses | Keep the first point. Do not create a measurement. Allow re-clicking for the second point. |
| Mesh rotated/transformed after measurement | Measurements are in model space. They rotate/scale with the mesh. If the mesh is transformed, measurement values update to reflect the new distances. |
| More than 3 measurements attempted | Block placement. Display status bar message: "Maximum 3 measurements. Clear an existing measurement to add a new one." |

### Implicit Dependencies
- Requires ray-mesh intersection (ray casting). This is computationally non-trivial for large meshes — may need a spatial acceleration structure (BVH/octree) or library support.
- Measurement labels must be readable on dark background (accessibility constraint).

### Design Decision (Orchestrator-confirmed)
- **Hard cap at 3 measurements.** The 4th attempt is blocked with a status bar message. User must clear an existing measurement first.

---

## 10. Cross-Section Slice Plane

### Logic Trigger
If the user activates the cross-section tool (toolbar toggle or View menu):

1. **Plane display:** Show a semi-transparent plane intersecting the model. Default position: model center, oriented along the XY plane (Z normal).
2. **Plane movement:** Draggable along its normal axis (click-drag on the plane). Keyboard input for exact position value.
3. **Plane orientation:** Preset buttons for X, Y, Z orientations. Free rotation via two-axis gizmo for arbitrary orientations.
4. **Clipping:** The plane clips the model, hiding geometry on one side and revealing the internal cross-section.
5. **Cross-section fill:** The exposed cross-section surface is filled (solid color/pattern, not hollow) to show the interior clearly.
6. **Reset button:** Returns the plane to model center with Z orientation.

### Failure States

| Condition | System Response |
|---|---|
| Plane moved outside model bounds | Display the full model without clipping. The plane is visible but has no clipping effect. Status bar: "Slice plane outside model bounds." |
| Model has no interior (2D/open mesh) | Clipping works but cross-section fill may show artifacts. Display info: "Cross-section fill may be incomplete for non-manifold meshes." |
| Free rotation produces degenerate plane | Prevent plane from collapsing to zero thickness. Enforce minimum angle constraints on rotation handles. |

### Implicit Dependencies
- Requires OpenGL clipping plane support or shader-based clipping.
- Cross-section fill requires computing the intersection polygon — non-trivial for arbitrary mesh/plane intersections.

---

## Cross-Feature Contradictions

None identified. The 10 features are complementary and non-conflicting.

## Implicit Dependencies Not Listed in Intake

| Dependency | Required By | Recommendation |
|---|---|---|
| **Undo/Redo stack** | Feature 7 (Repair), Feature 8 (Transforms) | Build as a shared infrastructure component. Must support arbitrary mesh state snapshots. |
| **Ray-mesh intersection** | Feature 9 (Measurement) | Requires spatial indexing for performance. Evaluate library support vs. custom BVH in Phase 1. |
| **User preferences persistence** | Feature 5 (Print Bed — last preset), viewport settings, window geometry | JSON config file in OS-standard location (already defined in Intake Section 5.4). |
| **Keyboard shortcuts system** | Features 2, 5, 8, 9, 10 | Multiple features define keyboard shortcuts (F, W, Escape, Ctrl+Z). Need a centralized shortcut manager. |
| **Status bar** | Features 1, 5, 8, 10 | Multiple features report status messages. Need a shared status bar component. |
| **Progress indicator** | Features 1, 6 | Long operations need non-blocking progress feedback. |
| **Command-line argument parsing** | Feature 1 | For `meshscope myfile.stl` usage. Not listed in intake but implied by desktop application convention. |

## Open Questions for Orchestrator

All questions resolved. No open items remaining.
