#!/usr/bin/env bash
# Regression test for branch-safety.sh — verifies the hook catches
# gh CLI commands that push to protected branches, not just git push.
#
# Run: bash tests/test_branch_safety_hook.sh
set -euo pipefail

HOOK="$(cd "$(dirname "$0")/../.claude/framework/hooks" && pwd)/branch-safety.sh"
PASS=0
FAIL=0

check() {
  local description="$1" command="$2" expected_exit="$3"
  local input actual_exit
  input=$(printf '{"tool_input":{"command":"%s"}}' "$command")

  set +e
  echo "$input" | CLAUDE_PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)" bash "$HOOK" 2>/dev/null
  actual_exit=$?
  set -e

  if [ "$actual_exit" -eq "$expected_exit" ]; then
    echo "  PASS: $description (exit $actual_exit)"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: $description (expected exit $expected_exit, got $actual_exit)"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== branch-safety.sh regression tests ==="
echo ""
echo "Pattern matching (should be detected as push commands):"
check "git push" "git push origin main" 0
check "gh repo create --push" "gh repo create org/repo --public --source=. --push" 0
check "gh pr merge" "gh pr merge 42" 0

echo ""
echo "Pattern matching (should NOT be detected as push commands):"
check "git status" "git status" 0
check "git commit" "git commit -m test" 0
check "gh pr create" "gh pr create --title test" 0
check "echo push" "echo push" 0

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] || exit 1
