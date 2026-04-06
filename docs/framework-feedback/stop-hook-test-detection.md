# Framework Feedback: Stop Hook Doesn't Recognize Shell Test Files

**Project:** meshscope
**Session:** 2026-04-05
**Category:** False positive in stop-checklist hook

---

## What happened

The `stop-checklist.sh` hook repeatedly blocked session exit with "One or more commits look like a bug fix but have NO regression test" even after:
1. A regression test was added (`tests/test_branch_safety_hook.sh`)
2. The fix and test were squashed into a single commit
3. `git show --stat` confirmed the test file was in the commit

## Root cause

The hook likely only detects Python test files (`test_*.py`) as regression tests. The fix was to a bash script (`.claude/framework/hooks/branch-safety.sh`) and the regression test was also a bash script (`tests/test_branch_safety_hook.sh`). The hook doesn't recognize `.sh` files in `tests/` as valid test files.

## Recommended fix

In `stop-checklist.sh`, expand the test file detection to include shell test scripts:

```bash
# Current (probable): only matches test_*.py
# Should match: test_*.py, test_*.sh, test_*.js, test_*.ts, *_test.go, etc.
```

The detection should match any file in `tests/` or any file matching common test naming conventions regardless of extension.
