# Framework Upgrade Session Prompt

Copy everything below the line into a new meshscope Claude Code session.

---

## Session Context

The Solo Orchestrator Framework has been upgraded with two major changes since this project was initialized:

1. **Documentation Artifact Remediation (PR #6)** — 10 new templates in `templates/generated/`, new artifact directories (`docs/ADR documentation/`, `docs/api and interfaces/`, `docs/snapshots/`), updated reference docs, and CLAUDE.md template enhancements
2. **Process Enforcement (PR #7)** — `scripts/process-checklist.sh` state machine, `scripts/pre-commit-gate.sh` commit gating hook, `scripts/track-tool-usage.sh` tool usage tracking, updated session hooks

All new files have already been copied into this project. The upgrade document at `docs/framework-upgrade-2026-04-08.md` has the full details of what changed and what was installed.

Your job is to bring meshscope's project artifacts up to spec with the new framework. Work through the items below in order. Each item is a discrete task — commit after each one.

**Important constraints:**
- Read the relevant template from `templates/generated/` before creating each artifact
- Read existing project files (PRODUCT_MANIFESTO.md, PROJECT_BIBLE.md, existing feature specs in `docs/superpowers/specs/`) to pull accurate content — don't guess
- The 8 completed features are: file-loading, 3d-viewport, mesh-info-panel, format-conversion, print-bed-visualization, manifold-watertight-check, basic-mesh-repair, scale-rotate-mirror
- Feature specs and plans are in `docs/superpowers/specs/` and `docs/superpowers/plans/` respectively
- UAT session 4 found 7 bugs (UAT4-001 through UAT4-007). Check `tests/uat/` for session results.
- This project uses Python 3.13 + PySide6 + VTK + Nuitka on macOS

## Tasks

### 1. Create FEATURES.md
Read `templates/generated/features.tmpl` for structure. Populate with all 8 completed features. For each feature, reference the design spec and note the build date. Use the git log and spec files to get accurate dates and descriptions.

### 2. Create CHANGELOG.md
Read `templates/generated/changelog.tmpl` for the 8-category structure. Backfill entries for all 8 features. Group by logical release (all 8 are pre-release / Phase 2 construction). Use git log dates.

### 3. Create BUGS.md
Read `templates/generated/bugs.tmpl` for structure. Populate with bugs from UAT session 4 (UAT4-001 through UAT4-007). Check `tests/uat/sessions/` for the actual test results and bug details. Set status based on what was fixed vs deferred.

### 4. Create Architecture Decision Records
Read `templates/generated/adr.tmpl` for the standard ADR format. Create these in `docs/ADR documentation/`:

- `0001-architecture-selection.md` — Python + PySide6 + VTK stack (from Phase 1 / Project Bible)
- `0002-python-version-selection.md` — Python 3.13, not 3.14, due to PySide6/VTK/Nuitka compatibility chain failure
- `0003-packaging-with-nuitka.md` — Nuitka selected; must use targeted `--include-module` not `--include-package-data` for VTK (causes infinite dependency analysis)
- `0004-stl-as-primary-format.md` — STL as primary mesh format (if this was a deliberate decision)
- Any other non-trivial decisions discoverable from the specs and Project Bible

### 5. Create interface documentation
In `docs/api and interfaces/`, document the public component interfaces. Read the source code in `src/meshscope/` to understand the actual API surface. Focus on:
- Main window / application entry point
- 3D viewport component interface
- Mesh operations (load, repair, convert, scale, rotate, mirror, manifold check)
- File I/O interfaces (supported formats, import/export)
- Print bed visualization interface

### 6. Update CLAUDE.md
Read `templates/generated/claude-md.tmpl` for the current template structure. Update the existing CLAUDE.md to add these missing sections (do NOT replace the whole file — merge new sections into the existing content):

- **Engineering Principles** section (Priority Hierarchy + Best Practices) — add after Framework Reference
- **Process enforcement** commands in Construction Rules section — add the `process-checklist.sh` commands for Build Loop tracking
- **Context Health Check** — every 3-4 features, verify PROJECT_BIBLE.md still reflects the codebase
- **Phase 3-4 Documentation** section — what artifacts to produce and how to use process-checklist.sh for those phases
- **UAT HTML template** reference — update Testing & Bug Workflow to reference `templates/uat/templates/test-session-template.html` for generating interactive HTML test sessions instead of Markdown tables
- **Qdrant Persistent Memory** section (if Qdrant is configured) — what to store and when
- Add references to new artifact locations: `docs/ADR documentation/`, `docs/api and interfaces/`, `docs/snapshots/`, `FEATURES.md`, `BUGS.md`

### 7. Verify Phase 2 initialization
Run: `scripts/process-checklist.sh --verify-init`
This will auto-check what it can (remote repo, lockfile, hooks, CI) and prompt for manual attestation on items that can't be auto-verified. Complete the verification so the process enforcement system knows Phase 2 init is done.

### 8. Align PROJECT_BIBLE.md with template
Read `templates/generated/project-bible.tmpl` and compare against the current `PROJECT_BIBLE.md`. Add any missing sections or `<!-- Last Updated: YYYY-MM-DD -->` freshness markers. Don't rewrite existing content — augment with the structural elements the template provides.

### 9. Store key decisions in Qdrant (if configured)
If Qdrant MCP is available, store these for future session retrieval:
- The Python 3.13 version chain decision and why
- The Nuitka `--include-module` workaround for VTK
- Any architectural patterns established across the 8 features
- The UAT session 4 debugging insights

### 10. Create phase gate snapshot
Copy the current state of key artifacts to `docs/snapshots/phase-1-to-2/`:
- A brief summary noting when Phase 1→2 was approved and what the key decisions were
- This is for audit trail purposes — git history has the actual file states

---

After completing all items, run `scripts/process-checklist.sh --status` to verify the process state is clean, then report what was done.
