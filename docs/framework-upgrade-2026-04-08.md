# Meshscope Framework Upgrade — 2026-04-08

**From:** Solo Orchestrator Framework v1.0 (as installed 2026-04-05)
**To:** Solo Orchestrator Framework v1.0 + PR #6 (Documentation Remediation) + PR #7 (Process Enforcement)
**Applied by:** Karl (Orchestrator) on 2026-04-08

---

## What Changed in the Framework

Two major updates were made to the Solo Orchestrator Framework based on real-world issues discovered during meshscope Phase 2 development:

**PR #6 — Documentation Artifact Remediation:**
- Added 10 new documentation templates (`templates/generated/`) for artifacts the framework requires but never provided templates for
- Introduced a three-tier document structure (Reference / Operational / Artifacts)
- Renamed the canonical reference docs directory from `docs/framework/` to `docs/reference/` (meshscope retains `docs/framework/` — both work)
- Added new artifact directories: `docs/ADR documentation/`, `docs/api and interfaces/`, `docs/snapshots/`
- Updated Builder's Guide Appendix A from 15 to 24 tracked artifacts
- Added CLAUDE.md template sections for process enforcement, Context Health Check, and Phase 3-4 documentation
- Added phase gate snapshot enforcement and FEATURES.md as a living feature index

**PR #7 — Process Enforcement:**
- Added `scripts/process-checklist.sh` — state machine enforcing sequential process steps (Build Loop, UAT, Phase 3, Phase 4)
- Added `scripts/pre-commit-gate.sh` — PreToolUse hook that blocks `git commit` and `gh pr create` when process steps are incomplete
- Added `scripts/track-tool-usage.sh` — PostToolUse hook tracking Context7 and Qdrant usage per session
- Updated `session-test-gate-check.sh` to reset tool usage tracking at session start and add Context Health Check reminders
- Updated `session-end-qdrant-reminder.sh` to report tool usage summary and warn about unused tools
- Updated `test-gate.sh` with Context Health Check counter support

---

## What Was Installed in Meshscope

### New Files Added

| File | Purpose |
|------|---------|
| **Scripts** | |
| `scripts/process-checklist.sh` | Process state machine — tracks Build Loop, UAT, Phase 3, Phase 4 step completion |
| `scripts/pre-commit-gate.sh` | PreToolUse hook — blocks commits when process steps incomplete |
| `scripts/track-tool-usage.sh` | PostToolUse hook — logs Context7 and Qdrant tool calls |
| `scripts/check-changelog.sh` | CI annotation — warns when source changes without CHANGELOG.md update |
| `scripts/check-session-state.sh` | CI annotation — warns when CLAUDE.md hasn't been updated recently |
| **Templates** | |
| `templates/generated/adr.tmpl` | Architecture Decision Record template (standard format) |
| `templates/generated/bugs.tmpl` | Bug tracking template (SEV-1/2/3, status, root cause) |
| `templates/generated/changelog.tmpl` | CHANGELOG template (8 categories: Security, Data Model, Added, Changed, Fixed, Removed, Infrastructure, Documentation) |
| `templates/generated/features.tmpl` | FEATURES.md living feature index |
| `templates/generated/handoff.tmpl` | Maintainer handoff documentation |
| `templates/generated/incident-response.tmpl` | Incident response playbook |
| `templates/generated/product-manifesto.tmpl` | Product Manifesto structural template |
| `templates/generated/project-bible.tmpl` | Project Bible structural template with freshness markers |
| `templates/generated/release-notes.tmpl` | User-facing release notes |
| `templates/generated/claude-md.tmpl` | CLAUDE.md template (updated with process enforcement sections) |
| `templates/generated/approval-log-org.tmpl` | Approval log (organizational) |
| `templates/generated/approval-log-personal.tmpl` | Approval log (personal) |
| `templates/generated/gitignore-base.tmpl` | .gitignore template |
| `templates/uat/templates/test-session-template.html` | Interactive HTML UAT test template (replaces hostile Markdown tables) |
| **State Files** | |
| `.claude/process-state.json` | Process enforcement state (build loop, UAT, phase 3/4 step tracking) |
| `.claude/tool-usage.json` | Context7/Qdrant usage tracking per session |
| **Directories** | |
| `docs/ADR documentation/` | Architecture Decision Records (Phase 1-2) |
| `docs/api and interfaces/` | Interface documentation (per-feature, Phase 2+) |
| `docs/snapshots/` | Phase gate document snapshots |

### Updated Files

| File | What Changed |
|------|-------------|
| `scripts/session-end-qdrant-reminder.sh` | Added tool usage summary report and Phase 2 warnings for unused Context7/Qdrant |
| `scripts/session-test-gate-check.sh` | Added tool-usage.json reset at session start and Context Health Check reminder |
| `scripts/test-gate.sh` | Added Context Health Check counter support |
| `docs/framework/builders-guide.md` | Added process checkpoint references at Build Loop, UAT, Phase 3, Phase 4 steps (+50 lines) |
| `docs/framework/user-guide.md` | Added process enforcement documentation section (+48 lines) |
| `docs/framework/governance-framework.md` | Minor updates for consistency (+5 lines) |
| `.claude/settings.json` | Registered 4 new hooks (see below) |

### New Hooks Registered

| Hook Point | Script | Trigger |
|------------|--------|---------|
| PreToolUse (Bash) | `scripts/pre-commit-gate.sh` | Before `git commit` or `gh pr create` |
| PostToolUse (all) | `scripts/track-tool-usage.sh` | After every tool call (fast no-op for non-MCP tools) |
| SessionStart | `scripts/session-version-check.sh` | Session start — checks tool versions |
| SessionStart | `scripts/session-test-gate-check.sh` | Session start — resets tool tracking, checks test gate |
| Stop | `scripts/session-end-qdrant-reminder.sh` | Session end — tool usage summary and Qdrant reminder |

---

## New Document Structure

The framework now organizes all project files into three tiers:

### Tier 1 — Framework Reference (read-only)
Installed by init.sh. Updated only via `scripts/check-updates.sh`.

```
docs/framework/          ← meshscope uses this name (new projects use docs/reference/)
  builders-guide.md
  user-guide.md
  governance-framework.md
  executive-review.md
  cli-setup-addendum.md
  security-scan-guide.md
docs/platform-modules/
  desktop.md
evaluation-prompts/
```

### Tier 2 — Operational (drives agent behavior)
```
CLAUDE.md                          ← Agent instructions
PROJECT_INTAKE.md                  ← Project configuration
APPROVAL_LOG.md                    ← Phase gate audit trail
.claude/phase-state.json           ← Phase tracking
.claude/build-progress.json        ← Feature counter + test intervals
.claude/process-state.json         ← NEW: Process enforcement state
.claude/tool-usage.json            ← NEW: MCP tool usage tracking
.claude/tool-preferences.json      ← Resolved tool selections
.claude/settings.json              ← Claude Code permissions + hooks
.claude/framework/                 ← Development Guardrails (hooks/rules)
.github/workflows/ci.yml           ← CI pipeline
scripts/                           ← All utility scripts
```

### Tier 3 — Project Artifacts (generated during development)
```
Root level:
  PRODUCT_MANIFESTO.md             ← Phase 0 output
  PROJECT_BIBLE.md                 ← Phase 1 output (living document)
  FEATURES.md                      ← NEW: Living feature index
  CHANGELOG.md                     ← NEW: Append-only change log
  CONTRIBUTING.md                  ← Coding standards
  BUGS.md                          ← NEW: Bug tracking
  USER_GUIDE.md                    ← Phase 3 output
  HANDOFF.md                       ← Phase 4 output
  RELEASE_NOTES.md                 ← Phase 4 output
  sbom.json                        ← Phase 3 SBOM

docs/ subdirectories:
  docs/ADR documentation/          ← NEW: Architecture Decision Records
  docs/api and interfaces/         ← NEW: Interface documentation
  docs/snapshots/                  ← NEW: Phase gate snapshots
  docs/test-results/               ← Phase 3 scan results
```

---

## What Meshscope Needs to Come Up to Spec

The framework files are installed, but meshscope has 8 completed features that were built before these templates and enforcement mechanisms existed. The following items need to be created or updated by the agent in the next session:

### Must Do (Artifact Creation)

1. **Create `FEATURES.md`** from `templates/generated/features.tmpl` — populate with all 8 completed features (file-loading, 3d-viewport, mesh-info-panel, format-conversion, print-bed-visualization, manifold-watertight-check, basic-mesh-repair, scale-rotate-mirror)

2. **Create `CHANGELOG.md`** from `templates/generated/changelog.tmpl` — backfill entries for all 8 features with dates and categories

3. **Create `BUGS.md`** from `templates/generated/bugs.tmpl` — populate with any known bugs from UAT sessions (7 bugs from UAT session 4 were reported)

4. **Create ADRs** in `docs/ADR documentation/` using `templates/generated/adr.tmpl`:
   - `0001-architecture-selection.md` — Python + PySide6 + VTK stack selection (from Phase 1)
   - `0002-python-version.md` — Python 3.13 selection (not 3.14) due to PySide6/VTK/Nuitka compatibility
   - `0003-packaging-tool.md` — Nuitka with targeted --include-module (not --include-package-data)
   - Any other non-trivial decisions from the 8 feature builds

5. **Create interface documentation** in `docs/api and interfaces/` — document the public API surface (component interfaces, data flow contracts)

6. **Update `CLAUDE.md`** with new sections from `templates/generated/claude-md.tmpl`:
   - Add Engineering Principles section (Priority Hierarchy)
   - Add process enforcement commands to Construction Rules
   - Add Phase 3-4 documentation section
   - Add Context Health Check section
   - Add UAT HTML template reference
   - Update Framework Reference to include new artifact locations

7. **Verify Phase 2 initialization** — run `scripts/process-checklist.sh --verify-init` to validate and mark Phase 2 init as verified

8. **Create phase gate snapshot** in `docs/snapshots/` — snapshot of Phase 1→2 gate state

### Should Do (Process Alignment)

9. **Restructure `PROJECT_BIBLE.md`** — compare against `templates/generated/project-bible.tmpl` and add any missing sections or freshness markers

10. **Update `PRODUCT_MANIFESTO.md`** — compare against `templates/generated/product-manifesto.tmpl` for structural alignment

11. **Store architecture decisions in Qdrant** — if configured, store key decisions and patterns from the first 8 features

### Won't Automate (Orchestrator Actions)

12. **Review BUGS.md triage** — Orchestrator needs to verify bug dispositions from UAT session 4

13. **Create `docs/snapshots/phase-0-to-1/`** — if Phase 0→1 artifacts should be snapshot (they're already committed in git history, so this is optional)

---

## How Process Enforcement Works Going Forward

Starting with feature 9, the Build Loop is mechanically enforced:

```
# Start a feature
scripts/process-checklist.sh --start-feature "feature-name"

# Complete each step in order (out-of-order is blocked)
scripts/process-checklist.sh --complete-step build_loop:tests_written
scripts/process-checklist.sh --complete-step build_loop:tests_verified_failing
scripts/process-checklist.sh --complete-step build_loop:implemented
scripts/process-checklist.sh --complete-step build_loop:security_audit
scripts/process-checklist.sh --complete-step build_loop:documentation_updated
scripts/process-checklist.sh --complete-step build_loop:feature_recorded

# Commits are blocked until all steps pass
# Documentation-only commits (.md, .json, .yml) skip the gate
```

UAT sessions are similarly gated with 9 required steps. Phase 3 and Phase 4 each have their own step sequences.

### Emergency Escape
If the enforcement blocks a legitimate action:
```
scripts/process-checklist.sh --reset build_loop    # Clear one process
scripts/process-checklist.sh --reset-all           # Clear everything
```
These are for the Orchestrator only — they log to stderr.
