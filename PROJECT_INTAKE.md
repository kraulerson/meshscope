# Solo Orchestrator — Project Intake Template

## Version 1.0

---

## Document Control

| Field | Value |
|---|---|
| **Document ID** | SOI-004-INTAKE |
| **Version** | 1.0 |
| **Classification** | Project Initialization Template |
| **Date** | 2026-04-05 |
| **Companion Documents** | SOI-002-BUILD v1.0 (Builder's Guide), SOI-003-GOV v1.0 (Enterprise Governance Framework) |

---

## Purpose

This template collects every decision, constraint, and context variable that the AI agent needs to execute the Solo Orchestrator methodology with maximum autonomy. Fill it out completely before starting Phase 0. Incomplete sections will force the agent to stop and ask — every blank field is a round-trip.

### How This Document Flows Into the Process

The Intake is the primary input to the Builder's Guide. Here's where each section goes:

| Intake Section | Consumed By | Purpose |
|---|---|---|
| **1. Project Identity** | Phase 0 initialization, Platform Module selection | Names the project, sets the track, identifies which Platform Module the agent loads |
| **2. Business Context** | Phase 0 Steps 0.1-0.2 | The agent validates and expands this into the FRD and User Journey — it doesn't re-discover it |
| **3. Constraints** | Phase 0 and Phase 1 | Timeline, budget, and user targets constrain architecture and scope |
| **4. Features & Requirements** | Phase 0 Steps 0.1, 0.4 | The agent expands logic triggers and failure states, flags gaps, produces the Manifesto |
| **5. Data & Integrations** | Phase 0 Step 0.3, Phase 1 Step 1.4 | Drives the Data Contract, data model design, and third-party integration architecture |
| **6. Technical Preferences** | Phase 1 Steps 1.2-1.6 | Hard constraints and preferences feed directly into architecture proposals; Competency Matrix determines where automated tooling is mandatory |
| **7. Revenue Model** | Phase 0 Step 0.5, Phase 1 Step 1.2 | Hosting/distribution cost ceiling constrains architecture; pricing model shapes feature decisions |
| **8. Governance Pre-Flight** | Enterprise Governance Framework pre-conditions | Maps directly to the organizational approvals required before Phase 0 can begin |
| **9. Accessibility & UX** | Phase 1 Step 1.5, Phase 3 Step 3.4 | Architectural constraints from Day 1, not Phase 3 afterthoughts |
| **10. Distribution & Operations** | Phase 4, Platform Module | Distribution channels, monitoring, update strategy — platform-dependent |
| **11. Known Risks** | Phase 1 Step 1.3 | Additional inputs for the Iron Logic Stress Test |

The more complete the Intake, the more autonomously the agent can work. Where the Intake is vague or incomplete, the Builder's Guide prompts shift from validation to discovery — the agent will ask targeted questions instead of proposing options it doesn't have enough context to evaluate.

### How to Use This Document

1. Fill out every section. Mark fields N/A where they genuinely don't apply — don't leave blanks.
2. For organizational deployments, complete the Governance Pre-Flight (Section 8) before starting. This section maps to the Enterprise Governance Framework pre-conditions.
3. Once complete, provide this document to the AI agent at the start of Phase 0 with the instruction: "This is the Project Intake. Use it as the primary constraint for all phases. Do not suggest features, architectures, or tooling that contradict it."
4. The agent will use this to generate the Product Manifesto (Phase 0) and Project Bible (Phase 1) without stopping to ask for information that should already be decided.

---

## 1. Project Identity

| Field | Value |
|---|---|
| **Project name** | meshscope |
| **Project codename** (if different from public name) | |
| **One-sentence description** | A cross-platform desktop application for viewing, inspecting, measuring, and converting 3D mesh files with 3D printing utility features. |
| **Project track** | Light |
| **Platform type** | desktop |
| **Platform Module** | SOI-PM-DESKTOP |
| **Target platforms** | macOS 13+ (Apple Silicon primary), Windows 10+, Ubuntu 22.04+ |
| **Is this a personal project or organizational deployment?** | Organizational |
| **Repository URL** | To be created |

---

## 2. Business Context

### 2.1 The Problem

```
Working with 3D mesh files (STL, OBJ, 3MF, PLY) currently requires either
expensive commercial software (Fusion 360, Rhino3D, Meshmixer) or fragmented
open-source tools that each handle one aspect (viewing, repair, conversion)
poorly. For 3D printing hobbyists and makers, basic pre-print tasks — checking
if a model is watertight, verifying dimensions fit a print bed, measuring
distances, converting between formats — require launching multiple tools or
importing into a full CAD suite. There is no lightweight, fast, cross-platform
desktop application that consolidates these common mesh inspection and
preparation tasks into a single tool.
```

### 2.2 Who Has This Problem

| Field | Value |
|---|---|
| **Primary user persona** | 3D printing hobbyist/maker. Intermediate technical skill. Wants to quickly check, measure, and prepare mesh files before sending to a slicer. Not a CAD professional. |
| **Secondary personas** | Technical professionals who receive 3D files and need to inspect geometry, verify dimensions, or convert formats without installing a full CAD suite. |
| **How do they solve this problem today?** | Import into Fusion 360 or Meshmixer (heavyweight, requires account). Use online viewers (limited features, privacy concerns with uploading files). Use command-line tools like meshlab CLI (not user-friendly). |
| **What's wrong with the current solution?** | Commercial tools are overkill for inspection/prep tasks. Online viewers require uploading potentially proprietary geometry. CLI tools lack visual feedback. No single lightweight tool covers view + inspect + measure + repair + convert. |

### 2.3 Success Criteria

| Metric | Target | How Measured |
|---|---|---|
| Solo Orchestrator showcase: build timeline | Complete MVP in ≤7 working days of active development | Git commit history, SOI phase completion timestamps |
| Functional completeness | All 10 MVP features operational on all 3 target platforms | Manual UAT on macOS, Windows, Linux |
| CIO demo reaction | Steve Carpenter and Scott Cummings engage with the application and ask follow-up questions about the SOI framework | Qualitative — post-demo conversation |
| Application startup time | <3 seconds cold start on minimum supported hardware | Manual timing |
| File load performance | STL files up to 50MB load in <5 seconds | Benchmark with test files |

### 2.4 What This Is NOT

1. This is NOT a 3D modeling or CAD application — users cannot create or edit geometry (move vertices, sculpt, boolean operations).
2. This is NOT a slicer — it does not generate G-code or toolpaths for 3D printers.
3. This is NOT a mesh-to-BREP reverse engineering tool (stretch goal for post-MVP only).
4. This is NOT a collaborative or cloud-connected application — no user accounts, no cloud storage, no sharing features.
5. This is NOT a renderer or animation tool — no materials, textures, ray tracing, or animation timeline.

---

## 3. Constraints

### 3.1 Timeline

| Field | Value |
|---|---|
| **Target MVP date** | 2026-04-18 (two weeks from intake) |
| **Hard deadline?** | No — but the value of the demo diminishes with time. The story is "built in days, not months." |
| **Orchestrator availability** | 15-20 hours/week dedicated to this project (evenings and weekends primarily) |
| **Blocked time or interleaved?** | Interleaved with day job — blocked evening/weekend sessions preferred |

### 3.2 Budget

| Field | Value |
|---|---|
| **Monthly infrastructure ceiling** | $0 — fully local, no hosting costs |
| **One-time budget** | $0 — all dependencies are open source. Code signing deferred to post-MVP. |
| **AI subscription** | Already have — Claude Max (consumer) |
| **Who approves spending?** | Self |

### 3.3 Users

| Field | Value |
|---|---|
| **Users at launch** | 2-5 (Karl, Amber, Steve Carpenter, Scott Cummings, selected testers) |
| **Users at 6 months** | 10-50 (if released publicly via GitHub) |
| **Users at 12 months** | 50-200 (organic growth if useful) |
| **Internal only or external?** | External (public GitHub release) |
| **Geographic distribution** | North America primarily. No data sovereignty concerns — all data is local files. |

---

## 4. Features & Requirements

### 4.1 Must-Have Features (MVP)

| # | Feature | Business Logic Trigger | Failure State |
|---|---|---|---|
| 1 | **File Loading** | If the user opens or drags a file with extension .stl, .obj, .3mf, or .ply, the system must parse the mesh and display it in the 3D viewport within 5 seconds for files up to 50MB. | If the file is corrupt, unparseable, or an unsupported format, display a clear error message identifying the problem (e.g., "Invalid STL: unexpected EOF at byte 4096"). Do not crash. Do not display partial/broken geometry silently. |
| 2 | **3D Viewport** | If a mesh is loaded, the system must render it in a 3D viewport supporting orbit (left-click drag), pan (middle-click drag or shift+left-click drag), and zoom (scroll wheel). Lighting must illuminate the model from a default position. | If rendering fails (e.g., GPU incompatibility), display a fallback error with system info rather than a blank or frozen viewport. |
| 3 | **Mesh Info Panel** | If a mesh is loaded, the system must display: vertex count, face count, bounding box dimensions (X/Y/Z in mm), total surface area, and volume (if manifold). | If the mesh is non-manifold, display available metrics and flag "Volume: N/A (non-manifold mesh)" rather than showing an incorrect value. |
| 4 | **Format Conversion** | If the user selects "Export As" and chooses a target format (STL, OBJ, 3MF, PLY), the system must convert and save the mesh to the selected format. Binary STL must be the default STL export (not ASCII). | If conversion fails (e.g., features unsupported in target format), display a warning identifying what was lost. If write fails (permissions, disk space), display the OS error. Do not silently produce a 0-byte file. |
| 5 | **Print Bed Visualization** | If the user activates print bed view, the system must display a scaled grid representing a selectable printer bed size (presets: 220x220mm Ender 3, 250x210mm Prusa MK4, 350x350mm Voron 2.4, custom dimensions). The model must be shown on the bed to indicate fit. | If the model exceeds bed dimensions, visually indicate the overflow (e.g., the model extends beyond the grid boundary) and display a text warning with the overshoot dimensions. |
| 6 | **Manifold/Watertight Check** | If the user triggers a printability check, the system must analyze the mesh and report: manifold status (yes/no), number of holes/open edges, number of degenerate faces, and number of non-manifold edges. | If analysis takes >10 seconds on a large mesh, show a progress indicator. Do not freeze the UI. |
| 7 | **Basic Mesh Repair** | If the mesh has holes (open edges) or flipped normals, the system must offer a one-click repair that fills small holes and corrects normal orientation. The repair must be non-destructive (operate on a copy; original remains available via undo). | If repair fails or would significantly alter geometry (>5% vertex count change), warn the user before applying. If repair is partial (some holes too large to fill automatically), report what was fixed and what remains. |
| 8 | **Scale/Rotate/Mirror** | If the user applies a transform (scale by factor or to target dimension, rotate by degrees around X/Y/Z, mirror across X/Y/Z plane), the system must apply it to the loaded mesh and update the viewport and info panel immediately. | If a scale factor of 0 or negative (non-mirror) is entered, reject with a validation message. All transforms must be undoable. |
| 9 | **Measurement Tool** | If the user activates the measurement tool and clicks two points on the mesh surface, the system must display the Euclidean distance between them in mm, with a visible line connecting the points in the viewport. | If the user clicks off-mesh (empty space), do not create a measurement point — show a subtle indicator that the click did not hit geometry. Support at least 3 simultaneous measurements visible on screen. |
| 10 | **Cross-Section Slice Plane** | If the user activates the cross-section tool, the system must display a draggable plane that clips the model, revealing the internal cross-section. The plane must be movable along its normal axis and rotatable to arbitrary orientations (X/Y/Z presets + free rotation). | If the slice plane is outside the model bounds, display the full model without clipping (don't show an empty viewport). Provide a "Reset" button to return the plane to model center. |

### 4.2 Should-Have Features (Post-MVP v1.1)

1. Wall thickness analysis — heatmap visualization showing thin regions that may fail during 3D printing.
2. Mesh decimation/simplification — reduce polygon count while preserving shape within a user-defined tolerance.
3. Multiple model loading — load and position multiple meshes in the same viewport for assembly visualization.
4. STL ASCII/Binary toggle on export with file size preview.
5. Recent files list and session restore (reopen last file on launch).

### 4.3 Will-Not-Have Features (Explicit Exclusions)

1. Mesh-to-BREP conversion (stretch goal — explicitly deferred, not MVP).
2. G-code generation or slicer integration.
3. Mesh editing (vertex manipulation, sculpting, boolean operations).
4. Material/texture support or photorealistic rendering.
5. Cloud storage, user accounts, or any network-dependent features.
6. Plugin or extension system.

---

## 5. Data & Integrations

### 5.1 Data Inputs

| Input | Data Type | Validation Rules | Sensitivity | Required? |
|---|---|---|---|---|
| 3D mesh file (STL) | Binary or ASCII STL | Valid STL header, parseable triangles, file size <500MB | Public | Yes (at least one format) |
| 3D mesh file (OBJ) | Wavefront OBJ text | Valid OBJ syntax, vertex/face definitions | Public | Yes |
| 3D mesh file (3MF) | 3MF XML/ZIP archive | Valid 3MF schema, extractable mesh data | Public | Yes |
| 3D mesh file (PLY) | PLY ASCII or binary | Valid PLY header, consistent element counts | Public | Yes |
| User preferences | JSON config | Valid JSON, schema-validated on load | Internal | No — defaults used if missing |

### 5.2 Data Outputs

| Output | Format | Latency Expectation |
|---|---|---|
| Converted mesh file (STL/OBJ/3MF/PLY) | Binary file written to user-selected path | <5 seconds for files up to 50MB |
| Mesh analysis report (info panel) | Displayed in UI | <2 seconds after file load |
| Screenshot of viewport | PNG file | <1 second |

### 5.3 Third-Party Integrations

| Service | What Data We Send/Receive | Auth Method | Fallback if Unavailable | Existing Account? |
|---|---|---|---|---|
| N/A — fully offline application | N/A | N/A | N/A | N/A |

### 5.4 Data Persistence

| Question | Answer |
|---|---|
| **What data must persist across sessions?** | User preferences (window size/position, last-used printer preset, UI theme, recent files list). Stored as JSON config in OS-standard location. |
| **What data can be ephemeral (browser/device only)?** | Loaded mesh data, measurements, viewport state, undo history — all session-only. |
| **Expected data volume at 12 months** | Negligible — config file <10KB. All mesh data is user files on their own filesystem. |
| **Data retention requirements** | N/A — no user data stored by the application beyond preferences. |
| **Backup requirements** | N/A — preferences file is trivially recreatable from defaults. |

---

## 6. Technical Preferences

### 6.1 Orchestrator Technical Profile

| Field | Value |
|---|---|
| **Languages you know well** | None at production level — all coding is AI-directed via Claude Code CLI. Can read and evaluate Python, bash. |
| **Frameworks you've used** | PySide6 (K-PDF project), React Native/Expo (Tender Reminders). |
| **Languages/frameworks you're willing to learn** | Any that Claude Code generates well. |
| **Languages/frameworks you refuse to use** | Java, C++ (too verbose for AI-directed development with limited validation ability). |
| **Database experience** | SQLite (K-PDF, Gameshelf). No database needed for this project. |
| **DevOps experience level** | Advanced (Proxmox, Azure, CI/CD, containerization — professional background). |
| **Mobile development experience** | Some — React Native/Expo with Tender Reminders. Not applicable here. |

### 6.2 Competency Matrix

| Domain | Self-Assessment | Automated Tooling Required? |
|---|---|---|
| Product/UX Logic | Yes | No |
| Frontend Code (HTML/CSS/JS) | Partially | Yes — linting, type checking |
| Backend / API Design | Partially | Yes — but minimal backend in this project |
| Database Design & Queries | Partially | N/A — no database |
| Security (Auth, Injection, IDOR) | Partially | Yes — Semgrep, gitleaks (but attack surface is minimal for offline desktop app) |
| DevOps / Infrastructure | Yes | No |
| Accessibility (WCAG) | Partially | Yes — automated accessibility scans on UI |
| Performance Optimization | Partially | Yes — profiling for large mesh loading |
| Mobile (iOS/Android) | No | N/A |

### 6.3 Development Environment

| Field | Value |
|---|---|
| **Primary development machine** | Mac mini (macOS, Apple Silicon) — primary build and development |
| **Secondary machines** | Lenovo P15V Gen 3 (Ubuntu) — Linux validation. Corsair workstation (Windows 11, AMD Ryzen AI Max+ 395, 96GB RAM) — Windows validation. |
| **IDE/Editor** | Claude Code CLI (terminal-based) |
| **Docker available?** | Yes (on all machines) |
| **Node.js version** | 25.9.0 |
| **Python version** | 3.9.6 (system default — init.sh will detect below 3.10 minimum and offer upgrade via Homebrew) |
| **Claude Code installed?** | Yes |
| **AI subscription tier** | Claude Max (consumer) |

### 6.4 Architecture Preferences & Constraints

**All Platforms:**

| Field | Value | Hard Constraint or Preference? |
|---|---|---|
| **Primary language** | Python | Hard Constraint — matches K-PDF stack, Claude Code generates Python with high consistency, Orchestrator can evaluate output |
| **Data storage** | File system (user mesh files) + JSON config file (preferences) | Hard Constraint |
| **Authentication** | None — offline desktop application | Hard Constraint |

**Desktop Applications:**

| Field | Value | Hard Constraint or Preference? |
|---|---|---|
| **UI framework** | PySide6 (Qt for Python) | Hard Constraint — proven in K-PDF, excellent cross-platform support, strong 3D rendering via QOpenGLWidget |
| **Packaging format** | Nuitka standalone executable | Hard Constraint — proven in K-PDF distribution |
| **Auto-update strategy** | Manual download (GitHub Releases) for MVP | Preference |
| **Offline requirement** | Fully offline — no network dependency | Hard Constraint |

**Cross-Cutting:**

| Field | Value | Hard Constraint or Preference? |
|---|---|---|
| **Monorepo or separate repos?** | Single repo | Hard Constraint |
| **Web + Desktop, Web + Mobile, or single platform?** | Single platform (Desktop) | Hard Constraint |

### 6.5 Existing Infrastructure to Integrate With

| System | Details | Integration Required? |
|---|---|---|
| **SSO / Identity Provider** | N/A | N/A |
| **Logging / SIEM** | N/A | N/A |
| **Monitoring** | N/A | N/A |
| **Data Warehouse** | N/A | N/A |
| **Backup Infrastructure** | N/A | N/A |
| **CI/CD Platform** | GitHub Actions | Yes — for cross-platform builds and releases |
| **Repository Platform** | GitHub | Yes |
| **Other** | N/A | N/A |

---

## 7. Revenue Model (Standard+ Track — skip for internal tools)

| Field | Value |
|---|---|
| **Pricing model** | N/A — open source, free |
| **Target price point** | $0 |
| **Competitive price range** | N/A |
| **Per-user cost estimate** | $0 — no hosting, no API calls |
| **Break-even user count** | N/A |
| **Hosting cost ceiling at launch** | $0 |
| **Hosting cost ceiling at 1,000 users** | $0 (GitHub Releases is free for open source) |
| **Hosting cost ceiling at 10,000 users** | $0 |

---

## 8. Governance Pre-Flight (Organizational Deployments Only)

Deferred — Private POC mode. Governance pre-conditions will be resolved via `scripts/intake-wizard.sh --upgrade-to-production` before any production deployment.

---

## 9. Accessibility & UX Constraints

| Field | Value |
|---|---|
| **Accessibility requirements** | Keyboard navigation for all core functions. Screen reader labels for all controls. No reliance on color alone for any meaning or state communication. |
| **Color vision deficiency considerations** | **Yes — HARD CONSTRAINT from Phase 1.** Never rely on color alone for meaning. All status indicators (manifold pass/fail, overshoot warnings, measurement labels, printability results) must use shape, position, text labels, patterns, or icons IN ADDITION to any color. The Orchestrator is colorblind. This is not a nice-to-have — it is a functional requirement that affects every UI element. |
| **Supported browsers** | N/A — desktop application |
| **Mobile responsive required?** | No |
| **Supported devices** | Desktop only |
| **Branding / style guide** | None — agent's discretion. Dark theme default. Clean, professional, minimal. No rounded-corner "friendly" aesthetic — prefer sharp, technical UI. |
| **Dark mode required?** | Yes — dark theme as default. Light theme nice-to-have. |

---

## 10. Distribution & Operations Preferences

**All Platforms:**

| Field | Value |
|---|---|
| **Notification preferences for alerts** | N/A — no server-side monitoring |
| **Uptime expectation** | N/A — desktop application |
| **Environment strategy** | Production only (single release track) |

**Desktop Applications:**

| Field | Value |
|---|---|
| **Distribution channels** | GitHub Releases (MVP). Homebrew and winget post-MVP. |
| **Code signing** | Deferred to post-MVP |
| **Code signing certificates** | Need to acquire post-MVP. Apple Developer ($99/yr) for macOS notarization. Windows EV cert for SmartScreen. |
| **Auto-update mechanism** | Manual download for MVP. Framework built-in deferred. |
| **Minimum supported OS versions** | macOS 13+ (Ventura), Windows 10+, Ubuntu 22.04+ |
| **Installer format preferences** | macOS: .dmg. Windows: portable .exe (NSIS installer post-MVP). Linux: .AppImage. |

---

## 11. Known Risks & Concerns

```
1. OpenGL compatibility: PySide6's QOpenGLWidget may behave differently across
   GPU vendors (Intel, AMD, NVIDIA, Apple Silicon). The Mac mini (Apple Silicon)
   is the primary dev machine, so Metal-backed OpenGL will be tested first.
   Windows and Linux OpenGL behavior must be validated early in Phase 2.

2. 3D rendering performance: Large meshes (>1M triangles) may require Level of
   Detail (LOD) or progressive loading to maintain interactive frame rates.
   Performance testing with large files should happen mid-Phase 2, not deferred
   to Phase 3.

3. Nuitka packaging with OpenGL dependencies: K-PDF's Nuitka build was
   straightforward because PyMuPDF has minimal native dependencies. This project
   adds OpenGL, numpy, and potentially trimesh/open3d — verify Nuitka can
   package these cleanly on all platforms early.

4. trimesh vs. Open3D vs. PyMuPDF-style direct parsing: Library selection for
   mesh I/O and analysis is a critical architecture decision. trimesh is
   lightweight and well-maintained. Open3D is heavier but provides more
   geometry processing. The agent should evaluate and recommend in Phase 1.

5. Cross-platform 3D rendering: Qt's OpenGL support on macOS uses a
   compatibility profile (Apple deprecated OpenGL in favor of Metal). Verify
   that the required OpenGL features work on macOS 13+ before committing to
   QOpenGLWidget. Alternatives: VTK with Qt integration, or a custom Metal
   backend (too complex for MVP).

6. This project is a showcase for the Solo Orchestrator Framework. Build quality,
   code organization, and process discipline matter as much as features. The
   CIOs evaluating this will look at the repo structure and commit history, not
   just the running application.
```

---

## 11.5. Testing & Bug Tracking

| Field | Value |
|---|---|
| **Testing interval** | Every 2 features |
| **Bug tracking tool** | GitHub Issues |
| **Human tester count** | 1 (Karl) |
| **Beta tester coordination** | N/A — solo tester for MVP |
| **Bug severity SLAs** | SEV-1: 24h, SEV-2: 7d, SEV-3: best effort |

---

## 12. Tooling Configuration

> This section is auto-populated by `init.sh` based on the tool installation matrix. It records what was installed, what needs manual setup, and what is deferred to later phases. Claude reads this to understand the available tooling environment.
>
> If this section is empty, run `init.sh` or manually populate `.claude/tool-preferences.json`.

<!-- AUTO-GENERATED BY INIT.SH — do not edit above this line -->

---

## 13. Agent Initialization Prompt

_Once this template is complete, provide it to the AI agent at the start of Phase 0 along with the Builder's Guide. Copy and customize the bracketed sections._

```
You are the AI execution layer for a Solo Orchestrator project. I am the
Orchestrator. I define intent, constraints, and validation. You provide
architecture, code, and documentation within the constraints I set.

ATTACHED:
1. Project Intake Template (this document) — your primary constraint
2. Solo Orchestrator Builder's Guide v1.0 — your process reference
3. Platform Module: DESKTOP — your platform-specific reference for
   architecture, tooling, testing, and distribution

DOCUMENT RELATIONSHIP:
- The Intake is the DATA SOURCE. It contains my decisions, constraints,
  requirements, technical profile, and governance pre-conditions.
- The Builder's Guide is the PROCESS. It defines the phases, steps,
  quality gates, and remediation procedures you follow.
- The Platform Module is the PLATFORM IMPLEMENTATION GUIDE. When the
  Builder's Guide shows a ⟁ PLATFORM MODULE callout, reference the
  attached Platform Module for platform-specific instructions.
- Where the Builder's Guide shows "With Intake" prompts, use those.
  They direct you to validate and expand my Intake data rather than
  re-discovering it.

RULES:
- The Project Intake is the governing constraint. Do not suggest features,
  architectures, or tooling that contradict it.
- The Builder's Guide defines the phase-by-phase process. Follow it.
- The Platform Module defines platform-specific implementation. Follow it
  at every ⟁ callout point.
- If the Intake specifies a hard constraint, respect it absolutely.
- If the Intake specifies a preference, you may recommend against it with
  justification, but defer to my decision.
- If the Intake leaves a field as "no preference," make a recommendation
  based on the constraints and explain your reasoning.
- If the Intake leaves a field blank or incomplete, flag it immediately
  and ask for the specific missing information before proceeding past
  the step that requires it.
- For any domain where my Competency Matrix (Section 6.2) says "Partially"
  or "No," default to the most conservative, well-documented option and
  ensure automated validation tooling covers that domain.
- Do not add features not in the MVP Cutline (Section 4.1).
- Do not suggest dependencies without justification.
- Every feature must have tests before implementation.
- Flag any conflict between the Intake constraints and technical feasibility
  immediately — do not silently work around it.

ACCESSIBILITY (from Section 9):
Color vision deficiency: NEVER rely on color alone for meaning. Use shape,
position, text labels, patterns, or icons for ALL status indicators,
warnings, pass/fail states, and UI distinctions. The Orchestrator is
colorblind. This is a hard constraint from Phase 1 — not a Phase 3
afterthought. Every UI element must be evaluated against this requirement.

PROJECT TRACK: Standard
PLATFORM: Desktop
TARGET PLATFORMS: macOS 13+ (Apple Silicon primary), Windows 10+, Ubuntu 22.04+

BEGIN: Execute Phase 0, Step 0.1 using the "With Intake — Validation
Prompt" path from the Builder's Guide. Use Sections 2 and 4 of the
Intake as the primary data source. Generate the Functional Requirements
Document by expanding my business logic triggers and failure states.
Where I've been vague, make it specific and flag for my review. Where
I've been contradictory, identify the contradiction and ask me to resolve
it. Where I've omitted an implicit dependency (e.g., features that
require authentication but I didn't list authentication), flag it as a
recommended addition.
```

---

## Checklist Before Starting

- [x] Every field is filled in or explicitly marked N/A
- [x] Must-Have features all have business logic triggers (If X, then Y)
- [x] Must-Have features all have failure states defined
- [x] Will-Not-Have list has at least 3 items
- [x] Data sensitivity classifications are assigned to all inputs
- [x] Competency Matrix is completed honestly
- [x] Budget constraints are realistic (not aspirational)
- [x] Timeline includes Orchestrator availability, not just calendar dates
- [x] For organizational deployments: all Section 8 "Blocking" items are Complete — Deferred (Private POC mode)
- [x] Success/failure exit criteria are defined and a decision-maker is named
- [x] This document has been saved as `PROJECT_INTAKE.md` in the project repository

---

## Document Revision History

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-04-05 | Initial release — filled out for MeshScope project. |

---

## Tooling Configuration

> Auto-generated by init.sh. Full machine-readable config: `.claude/tool-preferences.json`

**Resolved for:** Darwin / desktop / python / standard track

### Installed
| Tool | Category | Version |
|---|---|---|
| Git | version_control | 2.50.1 |
| jq | json_processor | jq-1.7.1-apple |
| Node.js | runtime | 25.9.0 |
| Docker | containerization | 29.3.1 |
| Colima | containerization | ersion |
| GPG | commit_signing | 2.5.18 |
| Semgrep | SAST Scanner | 1.157.0 |
| gitleaks | Secret Detection | 8.30.1 |
| Snyk CLI | Dependency Scanner | 1.1303.2 |
| Claude Code | ai_agent | 2.1.92 (Claude Code) |
| Claude Dev Framework | dev_framework | 8aed038 |
| Superpowers | claude_plugin | installed |
| Context7 MCP | mcp_server | configured |
| Python 3 | runtime | 3.9.6 |
| Xcode Command Line Tools | desktop_build_tools | Xcode 26.4 |
| Qdrant | mcp_server | container running |
