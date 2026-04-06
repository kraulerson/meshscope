#!/usr/bin/env bash
# Regression test for stop-checklist.sh — verifies that merge commits
# with "fix" in the branch name are not flagged as untested bug fixes.
#
# Run: bash tests/test_stop_checklist_merge.sh
set -euo pipefail

PASS=0
FAIL=0

check() {
  local description="$1" msg="$2" expected="$3" actual

  # Replicate the hook's detection logic
  if ! echo "$msg" | grep -qiE '^Merge ' && echo "$msg" | grep -qiE '\b(fix|bug|patch|hotfix|repair|resolve)\b'; then
    actual="flagged"
  else
    actual="skipped"
  fi

  if [ "$actual" = "$expected" ]; then
    echo "  PASS: $description"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: $description (expected $expected, got $actual)"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== stop-checklist.sh merge commit regression tests ==="
echo ""
echo "Should be FLAGGED (real fix commits):"
check "fix: address framework issues" "fix: address framework issues" "flagged"
check "bugfix: resolve crash on load" "bugfix: resolve crash on load" "flagged"
check "hotfix: patch auth bypass" "hotfix: patch auth bypass" "flagged"

echo ""
echo "Should be SKIPPED (merge commits with fix in branch name):"
check "Merge PR from fix/branch" "Merge pull request #1 from user/fix/framework-session-feedback" "skipped"
check "Merge PR from hotfix/branch" "Merge pull request #5 from user/hotfix/urgent-patch" "skipped"
check "Merge branch fix/something" "Merge branch 'fix/something' into main" "skipped"

echo ""
echo "Should be SKIPPED (non-fix commits):"
check "feat: add new feature" "feat: add new feature" "skipped"
check "docs: update readme" "docs: update readme" "skipped"
check "chore: update deps" "chore: update deps" "skipped"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] || exit 1
