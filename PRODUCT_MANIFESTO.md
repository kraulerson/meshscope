# Product Manifesto — meshscope

**Phase:** 0, Step 0.4
**Date:** 2026-04-05
**Status:** Active — this is the governing constraint for all subsequent phases.

---

## Product Intent

meshscope is a lightweight, cross-platform desktop application that consolidates the most common 3D mesh pre-print tasks — viewing, inspecting, measuring, repairing, and converting — into a single fast tool. It exists because the current options are either expensive commercial suites (overkill for inspection tasks), fragmented open-source tools (each handles one thing), or online viewers (privacy concerns, limited features). meshscope targets 3D printing hobbyists and technical professionals who need to quickly validate a mesh file before it moves to the next step in their workflow. It is also a showcase for the Solo Orchestrator Framework, demonstrating that a single technologist with AI can build a polished, functional desktop application in days.

---

## MVP Cutline

The 10 features below are the **complete scope** of the first release. Nothing else is built in Phase 2. Features are listed in build priority order (dependencies first).

| # | Feature | Summary | FRD Reference |
|---|---|---|---|
| 1 | **File Loading** | Open STL, OBJ, 3MF, PLY via dialog, drag-drop, or CLI. Parse and display. <5s for 50MB. | FRD Section 1 |
| 2 | **3D Viewport** | Interactive viewport with orbit, pan, zoom, fit-to-view, lighting, wireframe toggle. | FRD Section 2 |
| 3 | **Mesh Info Panel** | Vertex/face count, bounding box, surface area, volume (if manifold), manifold status. Unit mismatch detection. | FRD Section 3 |
| 4 | **Format Conversion** | Export As to STL (binary default), OBJ, 3MF, PLY. Current mesh state including transforms. | FRD Section 4 |
| 5 | **Print Bed Visualization** | Scaled grid overlay with printer presets (Ender 3 220x220, Prusa MK4 250x210, Voron 2.4 350x350, custom). Overflow detection with hatching + text. | FRD Section 5 |
| 6 | **Manifold/Watertight Check** | Manifold status, hole/open edge/degenerate face/non-manifold edge counts. Optional viewport highlighting with distinct line styles. | FRD Section 6 |
| 7 | **Basic Mesh Repair** | Fill small holes, fix normals, remove degenerate faces. Non-destructive (undo). Pre-repair impact warning. | FRD Section 7 |
| 8 | **Scale/Rotate/Mirror** | Uniform/non-uniform scale, rotate around X/Y/Z, mirror across X/Y/Z. All undoable. Info panel updates immediately. | FRD Section 8 |
| 9 | **Measurement Tool** | Point-to-point distance on mesh surface. Euclidean distance in mm. Hard cap at 3 measurements. | FRD Section 9 |
| 10 | **Cross-Section Slice Plane** | Draggable clipping plane with X/Y/Z presets and free rotation. Interior fill. Reset button. | FRD Section 10 |

### Infrastructure (not user-facing features, but required)

| Component | Required By |
|---|---|
| Undo/Redo stack (capped at 10 entries) | Features 7, 8 |
| Ray-mesh intersection | Feature 9 |
| User preferences (JSON config) | Features 5, viewport state, window geometry |
| Keyboard shortcut manager | Features 2, 5, 8, 9, 10 |
| Status bar | Features 1, 5, 8, 10 |
| Progress indicator (non-blocking) | Features 1, 6 |
| Empty-state viewport prompt | First-launch UX |

---

## Manifesto Rules

1. **Architecture that contradicts this Manifesto is rejected.** If an architecture decision in Phase 1 makes a Cutline feature impossible or impractical, the architecture is wrong — not the feature.

2. **Features not in the MVP Cutline are not built in Phase 2.** No exceptions. If a feature seems essential during construction, it goes to the Post-MVP Backlog and is evaluated after launch.

3. **Post-MVP is prioritized by user feedback, not this document.** The Should-Have list below is a starting point, not a commitment.

4. **Every UI element must be usable without color vision.** This is a hard constraint, not a guideline. Status indicators, warnings, highlights, and tool states use icon + text + shape/pattern. Color may supplement but never carry meaning alone.

5. **The application is fully offline.** No network calls of any kind. No telemetry, no update checks, no analytics, no cloud features. The application must function identically with no network.

---

## Post-MVP Backlog

Prioritized by estimated user value, not effort. Final priority set by user feedback after MVP launch.

| Priority | Feature | Notes |
|---|---|---|
| P1 | Wall thickness analysis (heatmap) | High value for 3D printing users. Requires accessible color mapping (not color-only). |
| P1 | Recent files list and session restore | Quality-of-life. Partially implemented (preferences store recent files). |
| P2 | Mesh decimation/simplification | Reduce polygon count preserving shape. |
| P2 | Multiple model loading | Load and position multiple meshes in one viewport. |
| P2 | STL ASCII/Binary toggle on export | With file size preview. |
| P3 | File associations (OS-level) | Double-click .stl to open in meshscope. Platform-specific. |
| P3 | Auto-update mechanism | Check GitHub Releases on launch. |
| P3 | Light theme | Dark is default. Light is accessibility/preference. |
| Deferred | Mesh-to-BREP conversion | Explicitly excluded from near-term. Research required. |

---

## Will-Not-Have (Explicit Exclusions)

These are not deferred — they are permanently out of scope for this product:

1. **Mesh editing** — no vertex manipulation, sculpting, or boolean operations. meshscope is a viewer and inspector, not an editor.
2. **G-code generation or slicer integration** — meshscope prepares files for slicers, it does not replace them.
3. **Material/texture support** — no photorealistic rendering, no texture mapping, no material assignment.
4. **Cloud storage, user accounts, network features** — the application is permanently offline-only.
5. **Plugin or extension system** — the application is self-contained.
6. **Animation or timeline** — static meshes only.

---

## Hard Constraints (from Intake)

| Constraint | Source |
|---|---|
| Python + PySide6 | Intake 6.4 — Hard Constraint |
| Nuitka standalone executable | Intake 6.4 — Hard Constraint |
| Fully offline, no network | Intake 6.4 — Hard Constraint |
| macOS 13+, Windows 10+, Ubuntu 22.04+ | Intake 1 |
| Colorblind-accessible UI | Intake 9 — Hard Constraint |
| Dark theme default | Intake 9 |
| $0 budget | Intake 3.2 |
| Single repo | Intake 6.4 — Hard Constraint |
| File system + JSON config (no database) | Intake 6.4 — Hard Constraint |

---

## Success Criteria (from Intake)

| Metric | Target | Measurement |
|---|---|---|
| Build timeline | MVP in <=7 working days active development | Git history + phase timestamps |
| Feature completeness | All 10 MVP features on all 3 platforms | Manual UAT |
| CIO demo engagement | Steve Carpenter and Scott Cummings ask follow-up questions about SOI | Post-demo qualitative |
| Startup time | <3 seconds cold start | Manual timing |
| File load performance | 50MB STL in <5 seconds | Benchmark |

---

## Competency Matrix (from Intake Section 6.2)

| Domain | Self-Assessment | Automated Tooling Required? | Tool |
|---|---|---|---|
| Product/UX Logic | Yes | No | — |
| Frontend Code (PySide6/Qt) | Partially | Yes | Linting, type checking (mypy) |
| Backend / Core Logic (Python) | Partially | Yes | Automated testing (pytest) |
| Database Design | N/A | N/A | N/A |
| Security | Partially | Yes | Semgrep, gitleaks (minimal attack surface — offline app, no auth, no network) |
| DevOps / Infrastructure | Yes | No | — |
| Accessibility (WCAG) | Partially | Yes | Automated accessibility scans |
| Performance Optimization | Partially | Yes | Profiling for large mesh loading |
| Build & Packaging (Nuitka) | Partially | Yes | CI builds on all 3 platforms |

**Domains requiring automated tooling in CI before Phase 2:** Frontend (linting/type checking), core logic (pytest), security (Semgrep, gitleaks), accessibility, performance, packaging (cross-platform CI builds).

---

## Revision History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-04-05 | Initial release from Phase 0 synthesis. |
