#!/usr/bin/env bash
# Solo Orchestrator — PostToolUse hook for MCP tool usage tracking
# Logs Context7 and Qdrant tool calls to .claude/tool-usage.json.
# Fires after every tool call — must be fast for non-MCP tools.

# Don't use set -e — we never want this hook to block anything
set +e

TOOL_USAGE=".claude/tool-usage.json"

# Read tool info from stdin (Claude Code passes PostToolUse JSON)
INPUT=$(cat)

# Extract tool name
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)

if [ -z "$TOOL_NAME" ]; then
  exit 0
fi

# Fast exit for non-MCP, non-commit tools (vast majority of calls)
case "$TOOL_NAME" in
  *context7*|*qdrant*) ;; # Continue to tracking logic
  Bash)
    # Check if this is a git commit (to increment counter)
    BASH_CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
    if echo "$BASH_CMD" | grep -qE '^\s*git\s+commit' 2>/dev/null; then
      if [ -f "$TOOL_USAGE" ] && command -v jq &>/dev/null; then
        CURRENT=$(jq -r '.commits_since_last_context7 // 0' "$TOOL_USAGE" 2>/dev/null)
        jq ".commits_since_last_context7 = $((CURRENT + 1))" "$TOOL_USAGE" > "$TOOL_USAGE.tmp" 2>/dev/null && mv "$TOOL_USAGE.tmp" "$TOOL_USAGE" 2>/dev/null
      fi
    fi
    exit 0
    ;;
  *) exit 0 ;; # Not an MCP tool, not a commit — exit fast
esac

# Ensure tool-usage.json exists
if [ ! -f "$TOOL_USAGE" ]; then
  mkdir -p .claude
  cat > "$TOOL_USAGE" << 'EOF'
{
  "session_id": null,
  "calls": [],
  "commits_since_last_context7": 0,
  "qdrant_find_called": false,
  "qdrant_store_called": false
}
EOF
fi

command -v jq &>/dev/null || exit 0

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Track Context7 calls
if echo "$TOOL_NAME" | grep -q "context7" 2>/dev/null; then
  jq --arg tool "$TOOL_NAME" --arg ts "$TIMESTAMP" \
    '.calls += [{"tool": $tool, "timestamp": $ts}] | .commits_since_last_context7 = 0' \
    "$TOOL_USAGE" > "$TOOL_USAGE.tmp" && mv "$TOOL_USAGE.tmp" "$TOOL_USAGE"
fi

# Track Qdrant calls
if echo "$TOOL_NAME" | grep -q "qdrant" 2>/dev/null; then
  if echo "$TOOL_NAME" | grep -q "find" 2>/dev/null; then
    jq --arg tool "$TOOL_NAME" --arg ts "$TIMESTAMP" \
      '.calls += [{"tool": $tool, "timestamp": $ts}] | .qdrant_find_called = true' \
      "$TOOL_USAGE" > "$TOOL_USAGE.tmp" && mv "$TOOL_USAGE.tmp" "$TOOL_USAGE"
  elif echo "$TOOL_NAME" | grep -q "store" 2>/dev/null; then
    jq --arg tool "$TOOL_NAME" --arg ts "$TIMESTAMP" \
      '.calls += [{"tool": $tool, "timestamp": $ts}] | .qdrant_store_called = true' \
      "$TOOL_USAGE" > "$TOOL_USAGE.tmp" && mv "$TOOL_USAGE.tmp" "$TOOL_USAGE"
  fi
fi

exit 0
