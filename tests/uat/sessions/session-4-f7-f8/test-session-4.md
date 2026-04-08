# UAT Test Session 4

**Date:** 2026-04-08
**Features Under Test:** Feature 7 (Basic Mesh Repair), Feature 8 (Scale/Rotate/Mirror)
**Tester:** [Your name]

---

## Instructions

1. For each feature below, follow the test scenarios step by step
2. Mark each scenario Pass or Fail
3. If Fail, fill in the bug details in the Bugs Found section below
4. Drop your completed file in `tests/uat/sessions/session-4-f7-f8/submissions/`
5. Tell the Orchestrator agent "results are in" when done

---

## Test Scenarios

### Feature 7: Basic Mesh Repair

| # | Scenario | Steps | Expected Result | Pass/Fail | Notes |
|---|---|---|---|---|---|
| 1 | Repair available after analysis finds issues | 1. Open a mesh file (cube.stl) 2. Click Analyze (A) 3. Check Repair button state | Repair button disabled (cube has no issues) | | |
| 2 | Repair fills holes on open mesh | 1. Open a mesh with holes (remove faces or use open mesh) 2. Click Analyze (A) 3. Click Repair (R) 4. Confirm in dialog | Repair dialog shows planned actions, mesh is repaired, info panel updates, status bar shows summary | | |
| 3 | Repair confirmation dialog shows details | 1. Load mesh with issues 2. Analyze 3. Click Repair | Dialog lists specific repairs: "Fill N hole(s)", "Fix N flipped normal(s)", "Remove N degenerate face(s)" | | |
| 4 | Undo reverses repair | 1. Load mesh with issues 2. Analyze 3. Repair 4. Press Ctrl+Z | Mesh reverts to pre-repair state, info panel updates, Redo becomes available | | |
| 5 | Redo reapplies repair | 1. After undoing a repair, press Ctrl+Shift+Z | Repaired mesh is restored | | |
| 6 | Multiple repairs create separate undo entries | 1. Load mesh 2. Repair once 3. Analyze again 4. Repair again (if issues remain) 5. Undo twice | Each Ctrl+Z reverses one repair at a time | | |
| 7 | Repair disabled when no mesh loaded | 1. Launch app without loading a file 2. Check Repair button | Repair button is greyed out | | |
| 8 | Repair disabled after clean analysis | 1. Load a clean mesh (cube.stl) 2. Analyze | Repair button stays disabled (no issues found) | | |
| 9 | Edit menu has Undo and Redo | 1. Open Edit menu | Undo (Ctrl+Z) and Redo (Ctrl+Shift+Z) visible in menu | | |
| 10 | Undo/Redo disabled with empty stack | 1. Load a fresh file 2. Check Undo/Redo state | Both are greyed out until a modification is made | | |
| 11 | High impact warning shown | 1. Load mesh where repair changes face count by >5% 2. Analyze 3. Click Repair | Confirmation dialog includes percentage warning about face count change | | |
| 12 | Print bed refreshes after repair | 1. Load mesh 2. Toggle print bed on (P) 3. Analyze 4. Repair | Print bed overlay updates to match repaired mesh dimensions | | |

### Feature 8: Scale/Rotate/Mirror

| # | Scenario | Steps | Expected Result | Pass/Fail | Notes |
|---|---|---|---|---|---|
| 13 | Transform dialog opens | 1. Load a mesh 2. Press Ctrl+T (or click Transform in toolbar) | Tabbed dialog opens with Scale, Rotate, Mirror tabs | | |
| 14 | Scale by factor 2x | 1. Open Transform 2. Set factor to 2.0 3. Click OK | Mesh doubles in size, info panel shows doubled dimensions, status bar shows "Scaled by 2.0x" | | |
| 15 | Scale preview updates live | 1. Open Transform (Scale tab) 2. Change factor value | "After" dimensions update in real-time as factor changes | | |
| 16 | Scale factor 0 rejected | 1. Open Transform 2. Try to enter 0 in scale factor | Spin box minimum is 0.001, cannot reach 0 | | |
| 17 | Extreme scale warning | 1. Open Transform 2. Set factor to 20000 3. Click OK | Status bar shows warning about model being very large | | |
| 18 | Rotate 90 degrees around Z | 1. Open Transform 2. Switch to Rotate tab 3. Select Z axis, enter 90 degrees 4. Click OK | Mesh rotates, viewport updates, info panel updates, status bar shows "Rotated 90.0 around Z axis" | | |
| 19 | Rotate 360 degrees returns to original | 1. Note current mesh position 2. Rotate 360 around any axis | Mesh returns to original orientation | | |
| 20 | Mirror across X axis | 1. Open Transform 2. Switch to Mirror tab 3. Select X (YZ plane) 4. Click OK | Mesh is mirrored, viewport updates, status bar shows "Mirrored across YZ plane" | | |
| 21 | Mirror twice returns to original | 1. Mirror across X 2. Mirror across X again | Mesh returns to original geometry | | |
| 22 | Undo reverses transform | 1. Scale mesh by 2x 2. Press Ctrl+Z | Mesh reverts to original size | | |
| 23 | Redo reapplies transform | 1. After undoing a transform, press Ctrl+Shift+Z | Transformed mesh restored | | |
| 24 | Multiple transforms accumulate and undo individually | 1. Scale 2x 2. Rotate 90 Z 3. Mirror X 4. Undo three times | Each Ctrl+Z reverses one transform, in reverse order | | |
| 25 | Transform disabled when no mesh loaded | 1. Launch app without file 2. Check Transform button | Transform is greyed out | | |
| 26 | Cancel dialog does nothing | 1. Open Transform 2. Change values 3. Click Cancel | No changes to mesh, no status bar update | | |
| 27 | Analysis invalidated after transform | 1. Load mesh 2. Analyze 3. Scale 2x | Analysis results cleared from info panel, analysis needs re-run | | |
| 28 | Print bed refreshes after transform | 1. Load mesh 2. Toggle print bed on 3. Scale 2x | Print bed overlay updates, overflow warning if mesh now exceeds bed | | |
| 29 | Transform in Edit menu | 1. Open Edit menu | Transform (Ctrl+T) visible after Undo/Redo | | |
| 30 | Rotate axis buttons are exclusive | 1. Open Transform, Rotate tab 2. Click Y, then Z | Only the last-clicked axis is selected (highlighted) | | |

---

## Bugs Found

| # | Severity | Feature | Description | Steps to Reproduce | Expected vs Actual |
|---|---|---|---|---|---|
| | SEV-? | | | | |

### Severity Guide
- **SEV-1:** Data loss, security breach, app crash on core flow
- **SEV-2:** Feature broken but workaround exists, significant UX failure
- **SEV-3:** Minor UX issue, cosmetic, non-core edge case
- **SEV-4:** Enhancement, suggestion, polish

---

## Overall Notes

_Free-form observations, UX concerns, suggestions, things that felt wrong even if they technically worked._
