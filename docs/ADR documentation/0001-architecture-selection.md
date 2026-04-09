# ADR-0001: Architecture Selection — Python + PySide6 + VTK

**Status:** Accepted
**Date:** 2026-04-05

## Context

meshscope is a cross-platform desktop application for 3D mesh inspection, analysis, and repair targeting 3D printing hobbyists and technical professionals. The architecture must support interactive 3D rendering of meshes up to 1M+ triangles, embed within a native desktop GUI, package into standalone executables for macOS/Windows/Linux, and operate fully offline with zero network dependencies.

Three options were evaluated:

- **Option A: trimesh + custom OpenGL** — Lower product quality ceiling. Hand-written OpenGL produces a functional but unsophisticated viewport. Every post-MVP rendering feature (clipping planes, measurement widgets, LOD, scalar visualization) requires writing shader code from scratch.
- **Option B: trimesh + VTK + PySide6** — Industry-standard scientific 3D visualization. VTK powers ParaView, 3D Slicer, and FreeCAD. Native support for clipping planes, measurement widgets, pick/ray-cast, LOD, and scalar mapping. C++ rendering core handles millions of polygons at interactive frame rates. Qt integration via QVTKRenderWindowInteractor is a mature, documented pattern.
- **Option C: Open3D** — Visualizer does not embed in a Qt widget, resulting in a two-window UX that contradicts the Product Manifesto's single-window design. ~500MB installed with Nuitka packaging risk.

## Decision

Selected **Option B: trimesh + VTK + PySide6** with single-process MVC architecture:

| Component | Library | Version |
|---|---|---|
| Language | Python | 3.13.12 |
| UI Framework | PySide6 | 6.9.3 |
| Mesh I/O & Analysis | trimesh | 4.7.4 |
| 3D Rendering | VTK | 9.4.2 |
| VTK-Qt Bridge | vtkmodules.qt.QVTKRenderWindowInteractor | (bundled) |
| Math | numpy | 2.2.6 |
| Packaging | Nuitka | 2.8.2 |

Architecture pattern: **Model** (MeshDocument) → **View** (VTK viewport + Qt panels) → **Controller** (Qt signals/slots).

## Consequences

**Easier:**
- Post-MVP rendering features (wall thickness heatmaps, mesh decimation viz, multi-model) map directly to existing VTK capabilities
- Professional-grade viewport out of the box (orbit, pan, zoom, pick, clipping, measurement)
- Mature Qt integration path with QVTKRenderWindowInteractor

**More difficult:**
- Nuitka + VTK packaging requires targeted `--include-module` declarations (see ADR-0003)
- VTK's C++ core can segfault if passed invalid data — requires a controlled adapter layer
- VTK dependency is large (~200MB in wheel), resulting in ~462MB standalone binary
- macOS OpenGL deprecation is a long-term risk (VTK roadmap includes Metal backend)
