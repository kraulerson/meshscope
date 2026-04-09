# Project Bible — meshscope

**Version:** 1.0
**Date:** 2026-04-05
**Status:** Active — this is the governing technical constraint for Phase 2 onward.

---

## 1. Product Manifesto
<!-- Last Updated: 2026-04-05 -->

See `PRODUCT_MANIFESTO.md` (Phase 0, Step 0.4). The Manifesto defines:
- Product intent and target users
- MVP Cutline (10 features, hard boundary)
- Will-Not-Have exclusions
- Hard constraints (Python, PySide6, Nuitka, offline, colorblind-accessible)
- Success criteria

**Rule:** Features not in the Manifesto's MVP Cutline are not built in Phase 2.

---

## 2. Revenue Model & Cost Constraints
<!-- Last Updated: 2026-04-05 -->

- **Price:** Free, open source
- **Budget:** $0 — no hosting, no API calls, no paid dependencies
- **Distribution cost:** $0 (GitHub Releases)
- **Code signing:** Deferred to post-MVP ($99/yr Apple Developer, ~$300/yr Windows EV cert)

No revenue model. No break-even calculation. This is a showcase project.

---

## 3. Architecture Decision Record
<!-- Last Updated: 2026-04-08 -->

### Selected Architecture: trimesh + VTK (Option B)

| Component | Library | Version |
|---|---|---|
| Language | Python | 3.13.12 (Homebrew — 3.14 incompatible with Nuitka 2.8.2) |
| UI Framework | PySide6 | 6.9.3 |
| Mesh I/O & Analysis | trimesh | 4.7.4 |
| 3D Rendering | VTK | 9.4.2 |
| VTK-Qt Bridge | vtkmodules.qt.QVTKRenderWindowInteractor | (bundled with VTK) |
| Math | numpy | 2.2.6 |
| Packaging | Nuitka | 2.8.2 |
| Logging | Python stdlib `logging` | stdlib |
| Config persistence | JSON (stdlib `json`) | stdlib |

### Architecture Pattern

Single-process MVC:
- **Model:** MeshDocument (mesh data, analysis, undo stack, measurements, tool state)
- **View:** VTK viewport (QVTKRenderWindowInteractor) + Qt panels (QDockWidget)
- **Controller:** Qt signals/slots connecting UI actions to model operations and view updates

### Rejected Alternatives

**Option A (trimesh + custom OpenGL):** Lower product quality ceiling. Hand-written OpenGL produces a functional but unsophisticated viewport. Every post-MVP rendering feature requires writing shader code from scratch. No built-in support for clipping planes, measurement widgets, LOD, or scalar field visualization. The rendering layer is the product — settling for a worse rendering engine to simplify packaging is the wrong trade-off.

**Option C (Open3D):** Open3D's visualizer does not embed in a Qt widget. The resulting two-window UX (separate visualization window + Qt controls) contradicts the Product Manifesto's single-window design. Also carries Nuitka packaging risk and is ~500MB installed.

### Why VTK

VTK is the industry standard for scientific 3D visualization. It powers ParaView, 3D Slicer, and FreeCAD — all professional applications in the same domain as meshscope. Key advantages:
- Native clipping planes, measurement widgets, pick/ray-cast, LOD, scalar mapping
- C++ rendering core handles millions of polygons at interactive frame rates
- Post-MVP features (wall thickness heatmaps, mesh decimation viz, multi-model) map directly to existing VTK capabilities
- Qt integration via QVTKRenderWindowInteractor is a mature, documented pattern

**Full ADRs:** `docs/ADR documentation/0001-architecture-selection.md`, `docs/ADR documentation/0002-python-version-selection.md`, `docs/ADR documentation/0003-packaging-with-nuitka.md`, `docs/ADR documentation/0004-stl-as-primary-format.md`

### Packaging Risk (Nuitka + VTK)

VTK wheels contain compiled C++ shared libraries. Nuitka must bundle these correctly. **This must be validated as the first Phase 2 task, before any feature code is written.** Use `--include-package=vtkmodules` and `--include-package-data=vtkmodules`. If Nuitka cannot package VTK on any target platform, escalate to Orchestrator with evidence.

---

## 4. Threat Model & Risk/Mitigation Matrix
<!-- Last Updated: 2026-04-05 -->

### Threat Summary

Primary threat vector: **malicious input files** (crafted STL/OBJ/3MF/PLY files from untrusted sources).

Attack surface is minimal: no network, no auth, no multi-user, no database, no IPC.

### STRIDE Matrix

| Category | Primary Threat | Mitigation |
|---|---|---|
| **Spoofing** | Crafted file with valid header + malicious payload | Use format-specific loaders (not generic `load()`). Validate declared sizes against actual file size. Cap max allocation. Python memory safety prevents buffer overflows. |
| **Tampering** | Silent file corruption on export (partial write) | Atomic write (temp file + rename). Post-export size verification. |
| **Repudiation** | N/A — single user, no audit trail needed | — |
| **Information Disclosure** | Recent file paths in config reveal work patterns | Accept risk — standard desktop app behavior. Config file protected by OS permissions. Log files: user-only permissions (0600), no mesh content in logs. |
| **Denial of Service** | Mesh bomb (tiny file declares billions of triangles); degenerate mesh causing analysis hang; ZIP bomb in 3MF | Pre-allocation size check. File size vs. declared count validation. Analysis timeout (60s) with cancel. 3MF extraction size limit (2GB). All long operations in worker threads with progress + cancel. |
| **Elevation of Privilege** | Symlink attack on export path | Check for symlinks before writing. Resolve with `os.path.realpath()`. Warn user if target differs from selected path. |

### Architecture Stress Risks

| Risk | Trigger | Mitigation |
|---|---|---|
| VTK + macOS OpenGL deprecation | Apple removes OpenGL in future macOS | VTK roadmap includes Metal backend. Pin max macOS version if needed. Years of runway. |
| VTK + Wayland (Linux) | Ubuntu 22.04+ defaults to Wayland | Test on both X11 and Wayland. `QT_QPA_PLATFORM=xcb` fallback. VTK 9.3 has improved Wayland support. |
| Nuitka + VTK packaging failure | VTK shared libs not discovered by Nuitka | Validate on all 3 platforms as first Phase 2 task. `--include-package=vtkmodules`. Escalate if unsolvable. |
| GIL bottleneck on large meshes | Post-MVP analysis on >5M triangles | Acceptable for MVP (targets <=1M triangles). Future: Rust/C++ backend or multiprocessing. Architecture separates processing from rendering. |
| GPU memory exhaustion | 10M+ triangles on integrated GPU | Detect via VTK. Enable LOD automatically. Warn user. |

### Stack-Specific Vulnerabilities

1. **trimesh `load()` auto-detection:** Use format-specific loaders only. Never pass untrusted files to generic `load()`.
2. **VTK C++ segfaults:** Validate all data before passing to VTK. Controlled adapter layer between trimesh and VTK. Wrap VTK calls in try/except.
3. **numpy memory leak on undo eviction:** Explicit `del` + `gc.collect()` on evicted entries. Monitor memory in debug builds.

---

## 5. Data Model
<!-- Last Updated: 2026-04-07 -->

### In-Memory (Session Only)

Core entity: **MeshDocument** containing:
- `mesh: MeshData` — vertices (float32 Nx3), faces (uint32 Mx3), normals, metadata
- `original_mesh: MeshData` — immutable copy for reset
- `undo_stack: UndoStack` — ring buffer, max 10 entries (scaled down for large meshes: 5 for >100MB, 3 for >250MB)
- `analysis: AnalysisResult | None` — invalidated on any mesh mutation
- `measurements: list[Measurement]` — max 3, model-space coordinates
- `slice_plane: SlicePlane | None`
- `print_bed: PrintBedState | None`

See Phase 1 Step 1.4 output for complete entity definitions and state transitions.

### Persisted (JSON Config)

Location: OS-standard config directory (`~/Library/Application Support/meshscope/config.json` on macOS, `%APPDATA%/meshscope/config.json` on Windows, `~/.config/meshscope/config.json` on Linux).

Schema-versioned (version field enables forward migration). Atomic writes. Schema validation on load with corrupt-file recovery.

---

## 6. Data Migration Plan
<!-- Last Updated: 2026-04-05 -->

N/A — no existing system.

---

## 7. Auth & Identity Strategy
<!-- Last Updated: 2026-04-05 -->

N/A — no authentication. Fully offline. Single user.

---

## 8. Observability & Logging Strategy
<!-- Last Updated: 2026-04-05 -->

| Component | Implementation |
|---|---|
| **Structured logging** | Python `logging` with JSON formatter. Fields: timestamp (ISO 8601), severity, component, message, correlation_id (per-operation). |
| **Log destination** | Rotating file in config directory. Max 5MB per file, 3 files retained. User-only permissions (0600). |
| **Log levels** | ERROR: failures affecting user operations. WARNING: recoverable issues (corrupt config, partial repair). INFO: user-initiated actions (load, export, transform). DEBUG: internal state (VTK pipeline, memory usage). |
| **Error reporting** | No remote telemetry (offline constraint). Errors shown to user via dialogs/status bar. Full details in log file. |
| **Crash reporting** | Python `sys.excepthook` for uncaught exceptions. Write to log file before exit. Display user-friendly crash message with log file path. |
| **Performance logging** | DEBUG-level timing for: file load, analysis, export, VTK render frame time. |

**No correlation IDs with external systems** — single-process, no network. Correlation ID tracks a single user operation (e.g., "load file X" generates a UUID used across all log entries for that load operation).

---

## 9. UI Component Specifications
<!-- Last Updated: 2026-04-08 -->

### Layout

- **QMainWindow** root with vertical QToolBar (left), QDockWidget (Info Panel, left-bottom), QVTKRenderWindowInteractor (center), QStatusBar (bottom), QMenuBar (top)
- Dark theme default (#262626 background, light text)
- Sharp, technical aesthetic — no rounded corners, no "friendly" styling

### Component States

Every interactive component has 4 defined states: Empty, Loading, Error, Success. See Phase 1 Step 1.5 output for complete state specifications per component.

### Accessibility (Hard Constraint)

- All toolbar buttons: icon + text label (never icon-only)
- All status indicators: icon shape + text label (never color alone)
- Keyboard navigation for all core functions with visible focus indicators
- Screen reader labels (`setAccessibleName()`) on all widgets
- 4.5:1 contrast ratio minimum for all text
- Tool active state indicated by border/outline change, not color change

---

## 10. Coding Standards
<!-- Last Updated: 2026-04-05 -->

### Python

- **Formatter:** `black` (default config, line length 88)
- **Linter:** `ruff` (replaces flake8 + isort + pyupgrade)
- **Type checking:** `mypy` (strict mode)
- **Naming:** snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE for constants
- **Imports:** stdlib → third-party → local, separated by blank lines (enforced by ruff)
- **Docstrings:** Google style. Required for public classes and functions. Not required for private/internal methods where the name is self-explanatory.

### Never Do This

- Never use trimesh's generic `load()` — always use format-specific loading with explicit `file_type`
- Never pass raw user data directly to VTK — always go through the adapter layer
- Never trust file headers without validating against actual file size
- Never use color alone for any UI meaning
- Never make network calls (no telemetry, no update checks, no analytics)
- Never store secrets or credentials (there are none to store)
- Never use `eval()`, `exec()`, or `pickle.load()` on any data

---

## 11. Build & Distribution Strategy
<!-- Last Updated: 2026-04-08 -->

### Build Pipeline

| Platform | Build Environment | Output |
|---|---|---|
| macOS | GitHub Actions `macos-latest` (Apple Silicon) | .dmg containing .app bundle |
| Windows | GitHub Actions `windows-latest` | Portable .exe (NSIS installer post-MVP) |
| Linux | GitHub Actions `ubuntu-22.04` | .AppImage |

### Nuitka Configuration (Validated 2026-04-05)

**CRITICAL:** Do NOT use `--include-package=vtkmodules` or `--include-package-data=vtkmodules` — causes infinite dependency analysis loop. Use targeted `--include-module` for specific VTK modules only.

```
nuitka --standalone
       --enable-plugin=pyside6
       --include-module=vtkmodules.vtkRenderingOpenGL2
       --include-module=vtkmodules.vtkRenderingCore
       --include-module=vtkmodules.vtkRenderingFreeType
       --include-module=vtkmodules.vtkInteractionStyle
       --include-module=vtkmodules.vtkFiltersSources
       --include-module=vtkmodules.vtkFiltersGeneral
       --include-module=vtkmodules.vtkFiltersCore
       --include-module=vtkmodules.vtkCommonCore
       --include-module=vtkmodules.vtkCommonDataModel
       --include-module=vtkmodules.vtkCommonExecutionModel
       --include-module=vtkmodules.vtkCommonMath
       --include-module=vtkmodules.vtkCommonTransforms
       --include-module=vtkmodules.vtkIOGeometry
       --include-module=vtkmodules.vtkIOXML
       --include-module=vtkmodules.vtkIOPLY
       --include-module=vtkmodules.vtkIOLegacy
       --include-module=vtkmodules.qt.QVTKRenderWindowInteractor
       --nofollow-import-to=vtkmodules.test
       --nofollow-import-to=vtkmodules.web
       --nofollow-import-to=vtkmodules.wx
       --nofollow-import-to=vtkmodules.tk
       --nofollow-import-to=matplotlib
       --nofollow-import-to=PIL
       --include-package=trimesh
       --include-package=numpy
       --output-dir=dist/
       --company-name="meshscope"
       --product-name="meshscope"
       --product-version="{version}"
       src/meshscope/main.py
```

Add VTK `--include-module` entries as new VTK modules are used during feature development. Validated on macOS (Apple Silicon), Python 3.13.12, ~3 min build, 462MB binary.

### Distribution

- **MVP:** GitHub Releases. Tag with semver. Attach platform binaries + SHA256 checksums.
- **Post-MVP:** Homebrew cask (macOS), winget manifest (Windows).

### Uninstall Data Handling

- macOS: .app bundle removed by dragging to Trash. Preferences at `~/Library/Application Support/meshscope/` persist (documented in README).
- Windows: portable .exe — just delete. Preferences at `%APPDATA%/meshscope/` persist.
- Linux: AppImage — just delete. Preferences at `~/.config/meshscope/` persist.

---

## 12. Test Strategy
<!-- Last Updated: 2026-04-08 -->

### Test Types

| Type | Tool | When | Pass Criteria |
|---|---|---|---|
| **Unit tests** | pytest | Every feature, TDD (write first) | All assertions pass. Coverage >80% for core logic. |
| **Integration tests** | pytest | Every feature | Load → analyze → transform → export pipeline works end-to-end. |
| **UI/E2E tests** | pytest-qt + VTK test utilities | Per-feature, automated on macOS. Manual on Windows/Linux for MVP. | Complete user journey succeeds. |
| **Security scan (SAST)** | Semgrep | Every commit (pre-commit hook + CI) | Zero high/critical findings. |
| **Secret detection** | gitleaks | Every commit (pre-commit hook + CI) | Zero findings. |
| **Dependency scan** | Snyk | CI pipeline | Zero high/critical vulnerabilities in direct dependencies. |
| **License check** | pip-licenses | CI pipeline | No GPL-2.0/3.0/AGPL-3.0 in dependency tree. |
| **Accessibility** | Manual (Accessibility Inspector on macOS, keyboard-only navigation) | Per-feature | All controls keyboard-accessible. All elements have screen reader labels. No color-only indicators. |
| **Performance** | Manual timing + pytest benchmarks | Mid-Phase 2 and Phase 3 | Cold start <3s. 50MB STL load <5s. Viewport 60fps on 1M triangles. |
| **Platform** | Manual testing on macOS, Windows, Linux | Phase 3 | Full user journey completes on all 3 platforms. |

### Test Directory Structure

```
tests/
├── unit/
│   ├── test_mesh_loading.py
│   ├── test_mesh_analysis.py
│   ├── test_mesh_repair.py
│   ├── test_transforms.py
│   ├── test_export.py
│   ├── test_undo_stack.py
│   ├── test_config.py
│   └── test_measurements.py
├── integration/
│   ├── test_load_analyze_export.py
│   ├── test_transform_pipeline.py
│   └── test_vtk_adapter.py
├── ui/
│   ├── test_main_window.py
│   ├── test_viewport.py
│   └── test_info_panel.py
├── fixtures/
│   ├── valid/           # Known-good test files (small)
│   │   ├── cube.stl
│   │   ├── cube.obj
│   │   ├── cube.3mf
│   │   └── cube.ply
│   ├── invalid/         # Crafted broken files
│   │   ├── corrupt.stl
│   │   ├── zero_faces.stl
│   │   ├── oversized_header.stl
│   │   └── malformed.obj
│   └── large/           # Performance test files (gitignored, generated by script)
│       └── generate_test_meshes.py
└── conftest.py          # Shared fixtures
```

### Testing Interval

Every 2 features: stop construction, run UAT session per CLAUDE.md Testing & Bug Workflow.

### Phase 3 Entry/Exit Criteria

**Entry:** All 10 features implemented. All unit and integration tests pass. Zero Semgrep/gitleaks findings. Snyk reports clean.

**Exit:** All platform tests pass. Accessibility audit complete. Performance benchmarks met. Security hardening validated.

---

## 13. Orchestrator Profile Summary
<!-- Last Updated: 2026-04-05 -->

| Domain | Self-Assessment | Automated Tooling |
|---|---|---|
| Product/UX Logic | Yes | — |
| Frontend (PySide6/Qt) | Partially | ruff, mypy, pytest-qt |
| Core Logic (Python) | Partially | pytest (>80% coverage), mypy |
| Security | Partially | Semgrep, gitleaks, Snyk |
| DevOps | Yes | — |
| Accessibility | Partially | Manual audits (Accessibility Inspector, keyboard-only) |
| Performance | Partially | pytest-benchmark, manual timing |
| Build & Packaging | Partially | CI builds on all 3 platforms |

**Rule:** All "Partially" domains have automated tooling in the CI pipeline before Phase 2 feature work begins.

---

## 14. Accessibility Requirements
<!-- Last Updated: 2026-04-05 -->

Source: Intake Section 9. **Hard constraint — not negotiable.**

- Keyboard navigation for all core functions
- Screen reader labels on all controls
- No reliance on color alone for any meaning or state
- Colorblind-safe status indicators: shape + text + icon (checkmark, warning triangle, X)
- 4.5:1 minimum contrast ratio for all text
- Dark theme default
- Print bed overflow: hatching pattern + text (not color shading)
- Problem highlighting: line styles + labels (not color coding)
- Toolbar active state: border/outline change (not color fill)

---

## 15. Platform-Specific Requirements
<!-- Last Updated: 2026-04-05 -->

### macOS (Primary Development)
- Minimum: macOS 13 (Ventura)
- Apple Silicon primary, Intel secondary (universal binary if Nuitka supports it, otherwise Apple Silicon + Intel separate builds)
- Menu bar follows macOS conventions (app name menu with About/Preferences/Quit)
- Retina display rendering
- .dmg distribution

### Windows
- Minimum: Windows 10
- High-DPI display handling
- Standard menu bar (File/Edit/View/etc.)
- Portable .exe for MVP, NSIS installer post-MVP
- No admin privileges required

### Linux
- Minimum: Ubuntu 22.04
- X11 and Wayland compatibility (test both; `QT_QPA_PLATFORM=xcb` fallback documented)
- .AppImage distribution
- No root required

---

## 16. Context Management Plan
<!-- Last Updated: 2026-04-08 -->

meshscope is a small project (<30 files estimated for MVP). Strategy: **Full Bible per session.**

- Provide `PROJECT_BIBLE.md` + `PRODUCT_MANIFESTO.md` at the start of each Phase 2 session
- Source files will be small and focused (per the architecture: MVC with clear separation)
- No module-level summaries or condensed index needed at this scale

If the project grows beyond 30 files post-MVP, upgrade to module-level summaries + master index.

---

## Bug Severity Classification

| Severity | Definition | Examples |
|---|---|---|
| **SEV-1** | App crash on core flow, data loss/corruption, security breach | Crash on file load, export produces corrupt file, segfault in VTK |
| **SEV-2** | Feature broken but workaround exists, significant UX failure | Measurement tool off by >1mm, clipping plane doesn't reset, export fails for one format |
| **SEV-3** | Minor UX issue, cosmetic, non-core edge case | Info panel alignment, tooltip text truncated, wireframe flicker on rotate |
| **SEV-4** | Enhancement, suggestion, polish | "Would be nice if...", performance optimization for edge cases |

**SLAs:** SEV-1: 24h. SEV-2: 7d. SEV-3: best effort. SEV-4: post-MVP backlog.

---

## UAT Plan

| Field | Value |
|---|---|
| Testing interval | Every 2 features |
| Human tester count | 1 (Karl) |
| Bug tracking tool | `BUGS.md` + GitHub Issues |
| UAT format | Interactive HTML (`templates/uat/templates/test-session-template.html`) |

**Process:** Per CLAUDE.md Testing & Bug Workflow (gate check, parallel test agents, consolidate, triage, fix, re-test, reset counter)

---

## Revision History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-04-05 | Initial release from Phase 1 synthesis. |
| 1.1 | 2026-04-08 | Added freshness markers, ADR cross-references, UAT Plan table format. |
