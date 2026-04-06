# User Journey Map — meshscope

**Phase:** 0, Step 0.2
**Persona Source:** PROJECT_INTAKE.md Section 2.2
**Date:** 2026-04-05
**Agent Persona:** Skeptical Product Manager

---

## Primary Persona

**Name:** Alex (composite)
**Role:** 3D printing hobbyist/maker
**Skill level:** Intermediate — comfortable with slicers (Cura, PrusaSlicer), downloads models from Thingiverse/Printables, occasionally designs in TinkerCAD or Fusion 360. Not a CAD professional.
**Goal:** Quickly check, measure, and prepare a downloaded mesh file before sending it to a slicer.
**Emotional state on arrival:** Mildly impatient. Has a model they want to print. Doesn't want to learn a new tool — wants to verify and move on. Tolerates ~30 seconds of orientation before expecting to be productive.
**Environment:** Home office or workshop. Possibly distracted. May have multiple apps open. Likely found meshscope from a forum recommendation or GitHub search.

## Secondary Persona

**Name:** Jordan (composite)
**Role:** Technical professional (engineer, product designer, procurement)
**Skill level:** High technical skill but unfamiliar with 3D printing workflow. Receives mesh files from vendors or colleagues.
**Goal:** Inspect geometry, verify dimensions match specifications, convert to a format their downstream tool accepts.
**Emotional state on arrival:** Task-focused. Needs specific measurements and format conversion. Will not explore features — goes straight to what they need.

---

## Entry Points

### E1: First Launch (No File)
Alex installs meshscope and launches it. The viewport is empty.

**What they see:** Dark-themed window with an empty viewport area, a toolbar with greyed-out tools, and a prompt in the viewport center: "Open a file or drag one here. Supports STL, OBJ, 3MF, PLY."

**Risk — dead-end confusion:** If there is NO empty-state prompt, the user sees an empty dark window and has no idea what to do. They may close the app thinking it's broken. The empty-state prompt is load-bearing — it is the only onboarding the app provides.

**Risk — supported formats unclear:** If the prompt doesn't list formats, the user may try to open a .gcode or .step file and get a cryptic error before ever succeeding. List formats in the empty-state prompt.

### E2: Open via File Dialog
User selects File > Open or presses Ctrl+O / Cmd+O.

**What they see:** Native OS file dialog filtered to show only .stl, .obj, .3mf, .ply files. Default directory: last-used directory (persisted), or user's home/Documents on first use.

**Risk — filter hides files:** If the user's files have uppercase extensions (.STL) and the filter is case-sensitive, they won't see their files. Filter MUST be case-insensitive. Also provide an "All Files" fallback option.

### E3: Drag and Drop
User drags a file from Finder/Explorer onto the meshscope window.

**Risk — drop target unclear:** If there's no visual drop zone indicator (border highlight, overlay text), the user doesn't know if the app accepts drops. Show a full-window overlay: "Drop file to open" when a file is dragged over the window.

**Risk — wrong file type dropped:** User drops a .png or .pdf. Must show a clear error immediately, not silently ignore the drop.

### E4: Command-Line Open
User runs `meshscope model.stl` from terminal.

**Risk — path resolution:** Relative paths, paths with spaces, symlinks. All must work. If the file doesn't exist, print error to stderr AND show GUI error (the user may not be watching the terminal).

### E5: File Association (Post-MVP)
Double-click a .stl file in Finder/Explorer to open in meshscope. Not in MVP scope, but users will attempt it. If file associations aren't set up, nothing happens from the user's perspective — they'll think the app is broken. Post-MVP, but note it for v1.1.

---

## Success Path: Alex Checks a Downloaded Model

### Step 1: Load the File

**Action:** Alex drags `benchy.stl` (3MB) from Downloads onto the meshscope window.
**System response:** File loads in <1 second. The viewport shows the 3D Benchy model, auto-framed to fit. The info panel populates: 225,564 vertices, 75,188 faces, 60.00mm x 31.00mm x 48.00mm, manifold: Yes.
**Feedback:** The transition from empty state to loaded model is immediate and unambiguous. The model is lit and clearly visible.

**Failure — corrupt file:** Alex downloaded a partial file (interrupted download). The system shows: "Invalid STL: unexpected EOF at byte 1,048,576. File may be incomplete." Alex understands the file is bad, not the app.

**Failure — huge file:** Alex drags a 200MB scan. The progress indicator appears: "Loading benchy_scan.stl..." with a cancel button. If it takes > 5 seconds, the user knows the app is working, not frozen.

### Step 2: Inspect the Model

**Action:** Alex orbits the model (left-click drag) to see all sides. Zooms in on details (scroll). Checks the info panel for dimensions.
**System response:** Viewport responds instantly to input. Orbit is smooth. Info panel shows dimensions in mm.

**Failure — disorienting controls:** If orbit pivot point is wrong (world origin instead of model center), the model flies off-screen on the first drag. Orbit MUST pivot around the model center. If the user gets lost, double-click or press F to re-frame.

**Failure — can't read info panel:** If the info panel text is too small, too low contrast, or obscured by the viewport, Alex misses critical info. Font must be legible. Panel must not overlap the viewport.

### Step 3: Check Printability

**Action:** Alex clicks the "Printability Check" button in the toolbar.
**System response:** Analysis runs (<2 seconds for 75K faces). Results appear in the info panel or a dedicated results section:
- Manifold: Yes (checkmark icon + "Yes" text)
- Holes: 0
- Open edges: 0
- Degenerate faces: 2
- Non-manifold edges: 0

**Feedback:** Alex sees "2 degenerate faces" with a warning icon. This is informational — 2 degenerate faces in 75K is negligible and won't affect printing.

**Failure — what does "degenerate face" mean?** Alex is an intermediate user, not a geometry expert. The term "degenerate face" is opaque. Consider a tooltip or one-line explanation: "Degenerate faces: 2 (zero-area triangles — negligible, won't affect printing)." Without this, Alex may panic and attempt unnecessary repairs.

**Failure — analysis hangs on large mesh:** If Alex loads a 5M face scan, analysis could take 30+ seconds. Without a progress indicator and cancel button, Alex thinks the app froze and force-quits.

### Step 4: Check Fit on Print Bed

**Action:** Alex clicks the print bed toggle in the toolbar. Selects "Ender 3 (220x220mm)" from the dropdown.
**System response:** A grid appears in the viewport beneath the model. The model is centered on the bed. The Benchy fits within the grid boundary.

**Feedback:** Alex visually confirms the model fits. No warning text appears (it fits).

**Failure — model too big:** Alex loads a large model that overflows the bed. The overflow region is marked with hatching pattern (not color alone). The info panel shows: "Model exceeds bed by X: +15.2mm." Alex knows exactly how much to scale down.

**Failure — bed preset wrong:** Alex selects Ender 3 but actually has an Ender 3 V2 (same bed size, but Alex doesn't know that). The presets must be clearly labeled. A "Custom" option covers all other printers.

**Risk — bed orientation ambiguous:** The grid shows 220x220 but which axis is which? Label the X and Y axes on the grid. Without labels, Alex doesn't know if the model overflow is width or depth.

### Step 5: Measure a Specific Dimension

**Action:** Alex activates the measurement tool and clicks two points on the Benchy's hull to verify height.
**System response:** Two points appear on the mesh surface. A line connects them. A label shows "48.02mm" at the midpoint.

**Failure — can't click the right spot:** On small features, clicking precisely on the mesh surface is hard, especially for detailed models. If the ray-cast snaps to the wrong face, the measurement is wrong and Alex won't know it. Consider a zoom-to-cursor feature or a temporary crosshair indicator showing exactly where the point will land.

**Failure — measurement label obscured:** If the label renders behind the mesh or is the same color as the background, Alex can't read it. Labels must always render in front (screen-space overlay) with a contrasting background.

### Step 6: Export for Slicer

**Action:** Alex has verified the model. Selects File > Export As > STL (binary).
**System response:** Save dialog opens. Alex saves to Desktop. File writes successfully. Status bar: "Exported to benchy_export.stl (2.8MB)."

**Failure — exports to same file:** Alex accidentally overwrites the original. The warning dialog catches this: "Overwriting the currently loaded file. Continue?" If Alex clicks Yes, they've at least been warned.

**Failure — silent export failure:** If the export fails but the app doesn't report it, Alex sends a corrupt/empty file to the slicer and wastes a print. The post-export size verification catches 0-byte files.

---

## Success Path: Jordan Converts a File for a Colleague

### Step 1: Load Vendor-Supplied OBJ

**Action:** Jordan opens a vendor-supplied .obj file (mechanical part, 12MB) via File > Open.
**System response:** File loads. A warning toast appears: "This OBJ file contains materials and texture data which are not supported. These will be ignored." The mesh renders without textures.

**Feedback:** Jordan sees the warning and understands that materials were stripped. The geometry is intact.

### Step 2: Verify Dimensions

**Action:** Jordan checks the info panel for bounding box dimensions: 150.00mm x 80.00mm x 40.00mm. Uses measurement tool to verify hole spacing: clicks two hole centers, reads "25.00mm."

**Feedback:** Dimensions match the vendor's spec sheet. Jordan is done.

**Failure — dimensions wrong because file is in inches:** OBJ files have no inherent unit. If the vendor saved in inches and meshscope assumes mm, all dimensions are 25.4x too small. The info panel shows "5.91mm x 3.15mm x 1.57mm" for what should be 150mm. **This is a real-world problem with no automatic solution.** Consider: if bounding box is suspiciously small (< 1mm) or large (> 10,000mm), display a warning: "Dimensions may indicate a unit mismatch. Consider scaling by 25.4 (inches to mm) or 0.0394 (mm to inches)."

### Step 3: Convert to STL

**Action:** Jordan selects File > Export As > STL.
**System response:** Export completes. Jordan sends the STL to their colleague.

---

## Success Path: Alex Repairs a Problem Mesh

### Step 1: Load and Discover Issues

**Action:** Alex loads a model from Thingiverse. Runs printability check.
**System response:** Results show: Manifold: No (warning icon + "No" text), Holes: 3, Open edges: 12, Degenerate faces: 0, Non-manifold edges: 4.

**Feedback:** Alex sees multiple issues. The viewport optionally highlights problem areas with distinct line styles (thick dashed for open edges, dotted for non-manifold).

### Step 2: Attempt Repair

**Action:** Alex clicks "Repair" in the toolbar.
**System response:** Pre-repair summary: "Fill 3 holes (12 open edges), fix 4 non-manifold edges. Vertex change: +18 (+0.02%). Apply?" Alex clicks "Apply."
**Post-repair:** Analysis re-runs automatically. Results show: Manifold: Yes, Holes: 0, Open edges: 0. Status bar: "Repair complete. 3 holes filled, 4 non-manifold edges fixed."

**Failure — repair makes it worse:** Repair fills holes but the fill geometry is wrong (e.g., fills across a gap that was intentional). Undo (Ctrl+Z) restores the original. The pre-repair warning about >5% vertex change catches catastrophic repairs.

**Failure — repair can't fix everything:** 2 of 3 holes are too large. Post-repair message: "Repaired: 1 hole filled, 4 non-manifold edges fixed. Remaining: 2 holes too large to fill automatically (diameter > 15mm)." Alex knows the repair was partial and what remains.

### Step 3: Scale to Fit Bed

**Action:** Alex's repaired model is 280mm wide but the Ender 3 bed is 220mm. Alex opens Edit > Scale, enters target X dimension: 210mm (with margin).
**System response:** Uniform scale applied (factor: 0.75). Viewport updates. Info panel shows new dimensions: 210.00mm x 157.50mm x 120.00mm. Print bed view confirms it fits.

---

## Cross-Section Exploration Path

### Step 1: Activate Cross-Section

**Action:** Alex activates the cross-section tool to inspect internal geometry of a complex model.
**System response:** A semi-transparent plane appears at the model center (Z orientation). The model clips at the plane, revealing the interior cross-section.

### Step 2: Move and Rotate Plane

**Action:** Alex drags the plane along Z to scan through the model. Clicks "X" preset to switch to sagittal view.
**System response:** Plane moves smoothly. Cross-section updates in real-time. Interior fill is visible.

**Failure — plane dragged outside model:** The model appears unclipped (full model visible). Status bar: "Slice plane outside model bounds." Alex presses Reset to return to center.

**Failure — cross-section fill artifacts on non-manifold mesh:** The interior fill shows gaps or flickering. Info text: "Cross-section fill may be incomplete for non-manifold meshes." Alex understands this is a mesh quality issue, not an app bug.

---

## Exit Points & Recovery

| Exit Point | Cause | Recovery |
|---|---|---|
| **Empty state — no prompt** | User doesn't know how to start | Empty-state prompt with drag hint and format list |
| **Disorienting orbit** | User rotates into bad camera angle | Double-click or F key resets to fit-to-view |
| **Cryptic error on load** | User doesn't understand the error | Error messages use plain language, name the file, suggest cause |
| **Measurement confusion** | User clicks empty space, nothing happens | "No hit" indicator at cursor explains the miss |
| **Feature overload** | Too many toolbar buttons, user overwhelmed | Group tools logically. Prioritize: Open, Orbit, Info, Check, Export. Advanced tools (measure, slice, repair) secondary. |
| **Undo uncertainty** | User doesn't know if they can undo | Always show undo availability in Edit menu and toolbar. Greyed = nothing to undo. |
| **Performance stall** | Large file freezes perception | Progress indicators for any operation > 2 seconds |

---

## Feature Gaps Identified

1. **Unit mismatch detection:** OBJ and PLY files have no standard unit. If dimensions look suspicious (bounding box < 1mm or > 10,000mm), warn the user and suggest common scale factors (25.4 for inch-to-mm). Not a new feature — an enhancement to the Info Panel (Feature 3).

2. **Empty-state onboarding:** Not listed as a feature but is critical for first-launch experience. The viewport must show a clear prompt when no file is loaded. This is a UI design requirement, not a separate feature.

3. **Tooltip/help text for technical terms:** "Degenerate face," "non-manifold edge," "manifold" — these are opaque to the primary persona. Short (one-sentence) tooltips or inline explanations reduce confusion. Not a feature — a UX polish item for Phase 2.

4. **Scale factor suggestion for bed overflow:** When the model overflows the bed (Feature 5), the system shows the overshoot in mm. It could also show the required scale factor to fit: "Scale to 0.78x to fit bed." Enhancement to Feature 5, not a new feature.

---

## Accessibility Notes (Cross-Cutting)

Per Intake Section 9 (hard constraint — Orchestrator is colorblind):

- All status indicators (manifold pass/fail, printability results, bed overflow) use **icon + text label**, never color alone.
- Measurement labels use **high-contrast text with background**, not colored lines without labels.
- Problem highlighting (open edges, non-manifold edges) uses **line style + text label**, not color coding.
- Toolbar button states (active/inactive tool) use **shape change or border**, not just color fill change.
- Print bed overflow uses **hatching pattern + text warning**, not red shading.
