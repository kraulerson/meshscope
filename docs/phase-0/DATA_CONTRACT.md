# Data Contract — meshscope

**Phase:** 0, Step 0.3
**Source:** PROJECT_INTAKE.md Section 5
**Date:** 2026-04-05

---

## 1. Inputs

### 1.1 Mesh Files

| Property | STL | OBJ | 3MF | PLY |
|---|---|---|---|---|
| **Encoding** | Binary or ASCII | ASCII text | ZIP archive (XML + binary) | ASCII or binary (little/big endian) |
| **Max file size** | 500MB | 500MB | 500MB (uncompressed estimate from archive) | 500MB |
| **Validation** | Header check (binary: 80-byte header + triangle count; ASCII: "solid" keyword). Triangle data integrity. | Syntax validation per line. Vertex/face index bounds check. | ZIP integrity. 3MF schema validation. Mesh data extraction. | Header parse. Element count validation. Data block integrity. |
| **Sensitivity** | Public | Public | Public | Public |
| **Units** | Assumed mm (STL has no unit spec) | No standard unit — detect suspiciously small/large bounding boxes | Defined in 3MF spec (mm) | No standard unit — same detection as OBJ |
| **Required?** | At least one format required | Yes | Yes | Yes |

### 1.2 User Preferences File

| Property | Value |
|---|---|
| **Format** | JSON |
| **Location** | OS-standard config directory: macOS `~/Library/Application Support/meshscope/config.json`, Windows `%APPDATA%/meshscope/config.json`, Linux `~/.config/meshscope/config.json` |
| **Max size** | <10KB (trivially small) |
| **Validation** | JSON schema validation on load. If invalid, log warning and use defaults. Never crash on bad config. |
| **Sensitivity** | Internal (no PII, no secrets) |
| **Required?** | No — defaults used if missing or invalid |

**Preferences schema (initial):**

```json
{
  "window": {
    "width": 1280,
    "height": 800,
    "x": null,
    "y": null,
    "maximized": false
  },
  "viewport": {
    "render_mode": "solid",
    "show_wireframe": false
  },
  "print_bed": {
    "last_preset": "ender3",
    "custom_x": 200,
    "custom_y": 200
  },
  "export": {
    "last_format": "stl",
    "last_directory": null
  },
  "recent_files": []
}
```

---

## 2. Transformations

Each transformation is a discrete, undoable operation on the in-memory mesh.

### 2.1 File Parse Pipeline

```
Raw file bytes
  → Format detection (extension + header inspection)
  → Format-specific parser (STL/OBJ/3MF/PLY)
  → Raw vertex array (float32, Nx3) + face index array (uint32, Mx3)
  → Optional: normal array (float32, Mx3 or Nx3)
  → In-memory mesh object
  → Viewport render + info panel calculation
```

**Invariants:**
- Vertex positions are stored as 32-bit floats (sufficient precision for 3D printing; consistent with STL binary format).
- Face indices are 0-based internally regardless of source format (OBJ uses 1-based).
- All meshes are triangulated on load. Quad faces (OBJ, PLY) are split into two triangles during parsing.

### 2.2 Analysis Pipeline

```
In-memory mesh
  → Topology analysis (edge map construction)
    → Manifold check (every edge shared by exactly 2 faces)
    → Hole detection (boundary edge loops)
    → Non-manifold edge detection (edges shared by >2 faces)
    → Degenerate face detection (zero-area triangles)
    → Normal consistency check (neighbor face orientation)
  → Geometry analysis
    → Bounding box (min/max per axis)
    → Surface area (sum of triangle areas)
    → Volume (sum of signed tetrahedron volumes — valid only if manifold)
```

**Invariants:**
- Volume calculation only runs if manifold check passes. Otherwise returns None.
- All calculations operate on the current mesh state (post-transforms, post-repair).

### 2.3 Repair Pipeline

```
Analysis results (holes, normals, degenerate faces)
  → Snapshot current mesh state to undo stack
  → Remove degenerate faces (zero-area triangles deleted)
  → Orient normals consistently (graph traversal + flip)
  → Fill holes (boundary loop detection → ear clipping triangulation)
  → Produce repaired mesh object
  → Re-run analysis pipeline on repaired mesh
```

**Invariants:**
- Repair never modifies the mesh in place. A new mesh object is created.
- The original mesh is preserved in the undo stack.
- Repair operations are atomic — if any step fails, the entire repair is rolled back.

### 2.4 Transform Pipeline

```
User input (scale factor / rotation degrees / mirror axis)
  → Validate input (reject invalid values per FRD Feature 8)
  → Snapshot current mesh state to undo stack
  → Compute transformation matrix (4x4 homogeneous)
  → Apply matrix to all vertex positions
  → For mirror: flip face winding order
  → Recalculate normals
  → Update viewport + info panel
```

### 2.5 Export Pipeline

```
In-memory mesh (current state, post-transforms)
  → Format-specific serializer (STL/OBJ/3MF/PLY)
  → Write to temporary file
  → Verify temp file size > 0
  → Atomic rename to target path
  → Confirm success in status bar
```

**Invariants:**
- Export writes to a temp file first, then renames. This prevents corrupt partial writes on disk-full or crash.
- Export always writes the current mesh state (including all applied transforms and repairs).

---

## 3. Outputs

| Output | Format | Destination | Latency |
|---|---|---|---|
| Rendered mesh in viewport | OpenGL framebuffer | Screen | <16ms per frame (60fps target) |
| Mesh info (vertex/face count, dimensions, area, volume) | Text in UI panel | Screen | <2 seconds after load |
| Printability analysis results | Text + icons in UI panel | Screen | <10 seconds (progress indicator if >2s) |
| Exported mesh file | STL (binary) / OBJ / 3MF / PLY | User-selected filesystem path | <5 seconds for files up to 50MB |
| User preferences | JSON | OS config directory | On change (debounced, <1s delay) |

---

## 4. Third-Party Data

None. meshscope is fully offline. No network calls, no telemetry, no update checks, no analytics.

**Verification:** The application must function identically with and without network connectivity. No feature degrades when offline.

---

## 5. State Boundaries

### 5.1 Persisted Across Sessions

| Data | Storage | Lifecycle |
|---|---|---|
| User preferences (window geometry, last preset, render mode, recent files) | JSON config file | Written on change. Read on launch. Survives app restarts. |

### 5.2 Ephemeral (Session Only)

| Data | Storage | Lifecycle |
|---|---|---|
| Loaded mesh (vertices, faces, normals) | In-memory (RAM) | Created on file load. Destroyed on app close or new file load. |
| Undo stack (mesh state snapshots) | In-memory (RAM) | Created on transform/repair. Destroyed on app close or new file load. |
| Analysis results (manifold check, holes, etc.) | In-memory (RAM) | Created on analysis run. Invalidated on transform/repair. Destroyed on app close. |
| Measurement points and lines | In-memory (RAM) | Created on measurement. Cleared on tool deactivation or user clear. Destroyed on app close. |
| Cross-section plane state (position, orientation) | In-memory (RAM) | Created on tool activation. Reset on tool deactivation. Destroyed on app close. |
| Print bed state (visible, preset selection) | In-memory (RAM) | Preset selection persisted via preferences. Visibility is session-only. |
| Viewport camera state (position, rotation, zoom) | In-memory (RAM) | Reset on new file load (auto-frame). Destroyed on app close. |

### 5.3 Memory Budget Estimates

| Component | Estimate (50MB STL, ~1M triangles) |
|---|---|
| Vertex array (float32, 3 components) | ~12MB (1M vertices x 3 x 4 bytes) |
| Face index array (uint32, 3 components) | ~12MB (1M faces x 3 x 4 bytes) |
| Normal array (float32, 3 components per face) | ~12MB |
| GPU buffer (duplicate of above) | ~36MB |
| Undo stack (1 snapshot) | ~36MB per entry |
| Edge map (topology analysis) | ~24MB (estimated, depends on implementation) |
| **Total for one loaded model** | **~130MB with 1 undo entry** |
| **Total with 5 undo entries** | **~310MB** |

**Implication:** The undo stack should have a maximum depth (suggest 10 entries). For a 500MB file (~10M triangles), one undo entry could be ~360MB. An uncapped undo stack on large files would exhaust RAM. **Flag: undo stack depth should be configurable or capped. Recommend default cap of 10 entries.**

---

## 6. Data Flow Diagram

```
[User drops/opens file]
        │
        v
[File Validation] ──fail──> [Error Dialog]
        │ pass
        v
[Format Detection]
        │
        v
[Format-Specific Parser] ──fail──> [Error Dialog with parse details]
        │ success
        v
[In-Memory Mesh Object]
        │
        ├──> [Viewport Renderer] ──> [Screen]
        │
        ├──> [Geometry Analysis] ──> [Info Panel]
        │
        ├──> [User: Printability Check] ──> [Topology Analysis] ──> [Results Panel]
        │                                                               │
        │                                          [User: Repair] <────┘
        │                                               │
        │                                               v
        │                                    [Undo Stack: snapshot]
        │                                               │
        │                                               v
        │                                    [Repair Pipeline] ──> [Updated Mesh]
        │
        ├──> [User: Transform] ──> [Undo Stack: snapshot] ──> [Transform Pipeline] ──> [Updated Mesh]
        │
        ├──> [User: Measure] ──> [Ray-Mesh Intersection] ──> [Measurement Overlay]
        │
        ├──> [User: Cross-Section] ──> [Clipping Plane] ──> [Viewport with clip]
        │
        ├──> [User: Print Bed] ──> [Bed Grid Overlay] ──> [Overflow Check] ──> [Viewport with bed]
        │
        └──> [User: Export As] ──> [Format Serializer] ──> [Temp File] ──> [Rename] ──> [Disk]
```

---

## Open Questions for Orchestrator

All questions resolved. No open items remaining.

**Design Decisions (Orchestrator-confirmed):**
- Undo stack capped at 10 entries. Oldest entry evicted when cap is reached.
