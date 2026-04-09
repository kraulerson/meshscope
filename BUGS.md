# Bug Tracker

<!--
  This file tracks bugs found during UAT sessions and ad hoc testing.
  Status and severity patterns are read by scripts/test-gate.sh for phase gate checks.
  Do NOT change the table format — the column order and status values are parsed by scripts.
-->

| # | Severity | Status | Feature | Description | Session | Disposition |
|---|---|---|---|---|---|---|
| UAT4-001 | SEV-2 | Fixed | Scale/Rotate/Mirror | Camera position resets to default view during transforms, undo, redo, and repair operations | Session 4 | Fix Now |
| UAT4-002 | SEV-2 | Fixed | Scale/Rotate/Mirror | Rotate tab axis buttons not mutually exclusive — all buttons can be deselected, leaving no axis selected | Session 4 | Fix Now |
| UAT4-003 | SEV-2 | Fixed | Scale/Rotate/Mirror | Mirror tab axis buttons not mutually exclusive — same deselection issue as rotate tab | Session 4 | Fix Now |
| UAT4-004 | SEV-3 | Fixed | Scale/Rotate/Mirror | Rotation axis labels lack direction indicators — unclear which way rotation goes per axis | Session 4 | Fix Now |
| UAT4-005 | SEV-2 | Fixed | Print Bed Visualization | Print bed overlay positioned at world origin instead of under the model — bed and model visually disconnected | Session 4 | Fix Now |
| UAT4-006 | SEV-2 | Fixed | Scale/Rotate/Mirror | Axis button checked/selected state nearly invisible on macOS — default Qt QPushButton styling provides no visual distinction | Session 4 | Fix Now |
| UAT4-007 | SEV-3 | Fixed | Print Bed Visualization | No X/Y/Z axis indicators at print bed origin — users cannot determine orientation in viewport | Session 4 | Fix Now |
| UAT5-001 | SEV-2 | Fixed | Measurement Tool | Left-click in measure mode passed to VTK interactor, causing orbit rotation instead of point placement | Session 5 | Fix Now |
| UAT5-002 | SEV-2 | Fixed | Cross-Section Slice Plane | Slice overlay panel compressed to invisible size — buttons and text not readable | Session 5 | Fix Now |
| UAT5-003 | SEV-2 | Fixed | Cross-Section Slice Plane | Interactor obtained via roundabout GetRenderWindow().GetInteractor() chain — returned wrong object | Session 5 | Fix Now |
| UAT5-004 | SEV-3 | Fixed | Cross-Section Slice Plane | Escape key didn't exit slice mode — keyPressEvent not reached when VTK widget had focus | Session 5 | Fix Now |
| UAT5-005 | SEV-3 | Fixed | Cross-Section Slice Plane | Plane widget center handle too small to grab on macOS | Session 5 | Fix Now |

## Status Guide

| Status | Meaning |
|---|---|
| **Open** | Bug confirmed, not yet fixed |
| **Fixed** | Fix implemented and verified |
| **Deferred** | Tracked with justification — must be resolved or feature removed at Phase 2→3 gate |
| **Won't Fix** | Accepted as-is with documented rationale (SEV-3/4 only) |
| **Post-MVP** | Moved to post-MVP backlog (SEV-4 enhancements only) |
| **Removed** | Feature containing the bug was removed |

## Severity Guide

| Severity | Definition | Examples | Can Defer? |
|---|---|---|---|
| **SEV-1** | Data loss, security breach, app crash on core flow | Auth bypass, database corruption, crash on login | No — must fix immediately |
| **SEV-2** | Feature broken but workaround exists, significant UX failure | Form submits wrong data, layout broken on one platform | Yes — but must resolve or remove feature at Phase 2→3 gate |
| **SEV-3** | Minor UX issue, cosmetic, non-core edge case | Alignment off, tooltip truncated, rare edge case | Yes |
| **SEV-4** | Enhancement, suggestion, polish | "Would be nice if...", performance optimization | Automatic Post-MVP |

## Session Summary

| Session | Date | Features Tested | Bugs Found | Bugs Fixed | Bugs Deferred |
|---|---|---|---|---|---|
| Session 1 | 2026-04-07 | File Loading, 3D Viewport | 1 | 1 | 0 |
| Session 2 | 2026-04-07 | Mesh Info Panel, Format Conversion | 1 | 1 | 0 |
| Session 3 | 2026-04-07 | Print Bed Visualization, Manifold/Watertight Check | 3 | 3 | 0 |
| Session 4 | 2026-04-08 | Basic Mesh Repair, Scale/Rotate/Mirror | 7 | 7 | 0 |
| Session 5 | 2026-04-08 | Measurement Tool, Cross-Section Slice Plane | 5 | 5 | 0 |
