# ADR-0004: STL as Primary Mesh Format

**Status:** Accepted
**Date:** 2026-04-06

## Context

meshscope supports four mesh formats: STL, OBJ, 3MF, and PLY. The application needs a default format for export operations and a primary format to optimize for in terms of loading performance and test coverage.

STL is the de facto standard for 3D printing workflows:
- Every slicer accepts STL
- Most 3D model repositories distribute STL files
- The format is simple (triangles only — no materials, textures, or scene graphs)
- Binary STL is compact and fast to parse

OBJ, 3MF, and PLY serve specific niches (CAD interchange, rich metadata, point clouds) but STL dominates the target user base of 3D printing hobbyists and professionals.

## Decision

STL (binary) is the **primary format** for meshscope:
- Default export format in the Export As dialog
- Binary STL is the default sub-format (not ASCII — smaller files, faster I/O)
- Primary test format for fixtures and performance benchmarks
- All other formats are fully supported but are secondary choices

Format-specific loading is used for all formats (never trimesh's generic `load()`) per the threat model.

## Consequences

**Easier:**
- Aligns with target user expectations — STL is what 3D printing users expect
- Binary STL is the simplest format to validate and test
- Performance benchmarks use the most common real-world format

**More difficult:**
- STL has no metadata (no units, no material, no scene structure) — requires unit mismatch heuristics in the info panel
- STL stores redundant vertex data (3 vertices per triangle, no indexing) — larger files than equivalent OBJ/PLY
- Export to STL from richer formats loses data (data loss warnings implemented in Feature 4)
