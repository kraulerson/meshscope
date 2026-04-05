#!/usr/bin/env bash
set -euo pipefail

# Solo Orchestrator — Session-Start Version Check
# Checks all tools against minimum versions and latest available.
# Reports status and offers interactive update with user approval.
#
# Usage:
#   scripts/check-versions.sh       # Full check + update prompt
#   scripts/check-versions.sh --help

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/lib/helpers.sh" ]; then
  source "$SCRIPT_DIR/lib/helpers.sh"
else
  if [ -t 1 ]; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
    BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
  else
    RED=''; GREEN=''; YELLOW=''; BLUE=''; CYAN=''; BOLD=''; NC=''
  fi
  print_ok()   { echo -e "${GREEN}  [OK]${NC} $1"; }
  print_fail() { echo -e "${RED}[FAIL]${NC} $1"; }
  print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
  print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
fi

# --- Argument parsing ---
while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h)
      echo "Usage: scripts/check-versions.sh [--help]"
      echo ""
      echo "Checks all tools against minimum version requirements and latest"
      echo "available versions. Offers interactive update with user approval."
      echo ""
      echo "Run at the start of every development session."
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# --- Version comparison ---
# Returns 0 if $1 >= $2 (version A meets minimum B)
version_gte() {
  local a="$1" b="$2"
  # Strip common prefixes (v, jq-, etc.)
  a=$(echo "$a" | sed 's/^[^0-9]*//' | sed 's/[^0-9.].*//')
  b=$(echo "$b" | sed 's/^[^0-9]*//' | sed 's/[^0-9.].*//')

  if [ "$a" = "$b" ]; then return 0; fi

  local IFS='.'
  local -a av=($a) bv=($b)
  local max=${#av[@]}
  [ ${#bv[@]} -gt $max ] && max=${#bv[@]}

  for ((i=0; i<max; i++)); do
    local ai=${av[$i]:-0}
    local bi=${bv[$i]:-0}
    if [ "$ai" -gt "$bi" ] 2>/dev/null; then return 0; fi
    if [ "$ai" -lt "$bi" ] 2>/dev/null; then return 1; fi
  done
  return 0
}

# --- Latest version lookup ---
get_latest_version() {
  local method="$1"
  local package="$2"

  case "$method" in
    npm)
      npm view "$package" version 2>/dev/null | tr -d '[:space:]'
      ;;
    pip)
      # Use PyPI JSON API
      curl -s "https://pypi.org/pypi/$package/json" 2>/dev/null | jq -r '.info.version // empty' 2>/dev/null | tr -d '[:space:]'
      ;;
    brew)
      brew info --json=v2 "$package" 2>/dev/null | jq -r '.formulae[0].versions.stable // empty' 2>/dev/null | tr -d '[:space:]'
      ;;
    github_release)
      curl -s "https://api.github.com/repos/$package/releases/latest" 2>/dev/null | jq -r '.tag_name // empty' 2>/dev/null | sed 's/^v//' | tr -d '[:space:]'
      ;;
    git_tag)
      git ls-remote --tags "$package" 2>/dev/null | grep -oP 'refs/tags/v?\K[0-9]+\.[0-9]+\.[0-9]+' | sort -V | tail -1 | tr -d '[:space:]'
      ;;
    *)
      echo ""
      ;;
  esac
}

# --- Load tool matrix ---
MATRIX_DIR="templates/tool-matrix"
if [ ! -d "$MATRIX_DIR" ]; then
  # Try from orchestrator source
  if [ -f ".claude/orchestrator-source.json" ] && command -v jq &>/dev/null; then
    src=$(jq -r '.source_dir // empty' ".claude/orchestrator-source.json" 2>/dev/null)
    [ -n "$src" ] && [ -d "$src/templates/tool-matrix" ] && MATRIX_DIR="$src/templates/tool-matrix"
  fi
fi

if [ ! -d "$MATRIX_DIR" ]; then
  print_fail "Tool matrix not found. Cannot check versions."
  exit 1
fi

# Load project context for filtering
PLATFORM=""
LANGUAGE=""
TRACK=""
if [ -f ".claude/tool-preferences.json" ] && command -v jq &>/dev/null; then
  PLATFORM=$(jq -r '.context.platform // empty' ".claude/tool-preferences.json" 2>/dev/null || echo "")
  LANGUAGE=$(jq -r '.context.language // empty' ".claude/tool-preferences.json" 2>/dev/null || echo "")
  TRACK=$(jq -r '.context.track // empty' ".claude/tool-preferences.json" 2>/dev/null || echo "")
fi

# --- Collect tools to check ---
# Load common.json + platform-specific
ALL_TOOLS=$(jq '.tools' "$MATRIX_DIR/common.json")
if [ -n "$PLATFORM" ] && [ -f "$MATRIX_DIR/${PLATFORM}.json" ]; then
  ALL_TOOLS=$(echo "$ALL_TOOLS" | jq --slurpfile p "$MATRIX_DIR/${PLATFORM}.json" '. + $p[0].tools')
fi

# Filter by language (skip language-specific tools for other languages)
if [ -n "$LANGUAGE" ]; then
  ALL_TOOLS=$(echo "$ALL_TOOLS" | jq --arg lang "$LANGUAGE" '[.[] | select(
    .languages == null or
    (.languages | index("all")) != null or
    (.languages | index($lang)) != null
  )]')
fi

# Only check tools that have a version_command (skip presence-only tools like Android Keystore)
CHECKABLE_TOOLS=$(echo "$ALL_TOOLS" | jq '[.[] | select(.version_command != null and .version_command != "" and .check_command != null)]')

# --- Check each tool ---
echo ""
echo -e "${BOLD}Solo Orchestrator — Version Check${NC}"
echo ""

BELOW_MIN=()
UPDATES=()
UPDATE_CMDS=()
PASS_COUNT=0
CURRENT_CATEGORY=""

TOOL_COUNT=$(echo "$CHECKABLE_TOOLS" | jq 'length')

if [ "$TOOL_COUNT" -eq 0 ]; then
  print_warn "No tools to check"
  exit 0
fi

# Check network availability once (skip if curl is unavailable or sandboxed)
NETWORK_AVAILABLE=false
if command -v curl &>/dev/null; then
  # Use a subshell to prevent sandbox environments from killing the parent process
  if (curl -s --max-time 3 "https://registry.npmjs.org" >/dev/null 2>&1); then
    NETWORK_AVAILABLE=true
  else
    print_info "Network unavailable — latest version check skipped"
    echo ""
  fi
fi

for i in $(seq 0 $((TOOL_COUNT - 1))); do
  TOOL=$(echo "$CHECKABLE_TOOLS" | jq ".[$i]")
  NAME=$(echo "$TOOL" | jq -r '.name')
  CATEGORY=$(echo "$TOOL" | jq -r '.category')
  CHECK_CMD=$(echo "$TOOL" | jq -r '.check_command')
  VERSION_CMD=$(echo "$TOOL" | jq -r '.version_command // empty')
  MIN_VER=$(echo "$TOOL" | jq -r '.min_version // empty')
  LATEST_METHOD=$(echo "$TOOL" | jq -r '.latest_check.method // empty')
  LATEST_PKG=$(echo "$TOOL" | jq -r '.latest_check.package // empty')
  INSTALL_OBJ=$(echo "$TOOL" | jq -r '.install // empty')

  # Category header
  case "$CATEGORY" in
    version_control|json_processor|runtime|containerization|commit_signing)
      NEW_CAT="Core Tools" ;;
    sast|secret_detection|dependency_scanning)
      NEW_CAT="Security Tools" ;;
    ai_agent|claude_plugin|mcp_server)
      NEW_CAT="Plugins & MCP" ;;
    *)
      NEW_CAT="Project Tools" ;;
  esac
  if [ "$NEW_CAT" != "$CURRENT_CATEGORY" ]; then
    echo -e "${BOLD}── $NEW_CAT ──${NC}"
    CURRENT_CATEGORY="$NEW_CAT"
  fi

  # Check if installed
  if ! eval "$CHECK_CMD" &>/dev/null 2>&1; then
    print_warn "$NAME: not installed"
    continue
  fi

  # Get installed version
  INSTALLED=""
  if [ -n "$VERSION_CMD" ]; then
    INSTALLED=$(eval "$VERSION_CMD" 2>/dev/null | tr -d '[:space:]' || echo "")
  fi

  # Check minimum version
  MIN_MET=true
  MIN_DISPLAY=""
  if [ -n "$MIN_VER" ] && [ -n "$INSTALLED" ]; then
    MIN_DISPLAY=" (min: $MIN_VER)"
    if ! version_gte "$INSTALLED" "$MIN_VER"; then
      MIN_MET=false
    fi
  fi

  # Check latest version
  LATEST=""
  LATEST_DISPLAY=""
  if [ "$NETWORK_AVAILABLE" = true ] && [ -n "$LATEST_METHOD" ] && [ "$LATEST_METHOD" != "null" ] && [ -n "$LATEST_PKG" ]; then
    LATEST=$(get_latest_version "$LATEST_METHOD" "$LATEST_PKG")
  fi

  if [ -n "$LATEST" ] && [ -n "$INSTALLED" ]; then
    if version_gte "$INSTALLED" "$LATEST"; then
      LATEST_DISPLAY=" — up to date"
    else
      LATEST_DISPLAY=" — $LATEST available"
    fi
  elif [ -n "$INSTALLED" ] && [ "$NETWORK_AVAILABLE" = false ]; then
    LATEST_DISPLAY=""
  elif [ -n "$INSTALLED" ]; then
    LATEST_DISPLAY=" — up to date"
  fi

  # Output
  if [ "$MIN_MET" = false ]; then
    print_warn "$NAME: $INSTALLED$MIN_DISPLAY — BELOW MINIMUM$LATEST_DISPLAY"
    echo -e "         ${YELLOW}⚠ Continuing with outdated $NAME may cause issues.${NC}"
    BELOW_MIN+=("$NAME")
    # Find update command
    local_update_cmd=""
    if command -v brew &>/dev/null; then
      local_update_cmd=$(echo "$TOOL" | jq -r '.install.darwin_brew // empty')
    fi
    if [ -z "$local_update_cmd" ]; then
      local_update_cmd=$(echo "$TOOL" | jq -r '.install.npm // .install.linux_pip // .install.manual // empty')
    fi
    UPDATES+=("$NAME $INSTALLED → ${LATEST:-latest} (BELOW MINIMUM)")
    UPDATE_CMDS+=("$local_update_cmd")
  elif [ -n "$LATEST" ] && ! version_gte "$INSTALLED" "$LATEST"; then
    print_ok "$NAME: $INSTALLED$MIN_DISPLAY$LATEST_DISPLAY"
    # Find update command
    local_update_cmd=""
    if command -v brew &>/dev/null; then
      local_update_cmd=$(echo "$TOOL" | jq -r '.install.darwin_brew // empty')
    fi
    if [ -z "$local_update_cmd" ]; then
      local_update_cmd=$(echo "$TOOL" | jq -r '.install.npm // .install.linux_pip // .install.manual // empty')
    fi
    UPDATES+=("$NAME $INSTALLED → $LATEST")
    UPDATE_CMDS+=("$local_update_cmd")
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    print_ok "$NAME: ${INSTALLED:-configured}$MIN_DISPLAY$LATEST_DISPLAY"
    PASS_COUNT=$((PASS_COUNT + 1))
  fi
done

# --- Summary ---
echo ""
echo -e "${BOLD}── Summary ──${NC}"
echo -e "  ${GREEN}✓ $PASS_COUNT up to date${NC}"
if [ ${#UPDATES[@]} -gt 0 ]; then
  echo -e "  ${CYAN}⬆ ${#UPDATES[@]} updates available${NC}"
fi
if [ ${#BELOW_MIN[@]} -gt 0 ]; then
  echo -e "  ${YELLOW}⚠ ${#BELOW_MIN[@]} below minimum (${BELOW_MIN[*]}) — update recommended before continuing${NC}"
fi

# --- Interactive update prompt ---
if [ ${#UPDATES[@]} -gt 0 ] && [ -t 0 ]; then
  echo ""
  echo -e "${BOLD}Updates available:${NC}"
  for idx in "${!UPDATES[@]}"; do
    echo "  $((idx+1)). ${UPDATES[$idx]}"
  done
  echo ""
  echo -e "${BOLD}Update options:${NC}"
  echo "  a) Update all ($(seq -s, 1 ${#UPDATES[@]}))"
  echo "  b) Select which to update (enter numbers: e.g., 1,3)"
  echo "  c) Skip for now"
  echo ""

  read -rp "$(echo -e "${BOLD}Choice [a/b/c]${NC}: ")" choice

  case "$choice" in
    a|A)
      echo ""
      for idx in "${!UPDATE_CMDS[@]}"; do
        cmd="${UPDATE_CMDS[$idx]}"
        uname="${UPDATES[$idx]%%  *}"
        uname="${uname%% *}"
        if [ -n "$cmd" ] && [ "$cmd" != "null" ]; then
          print_info "Updating $uname..."
          if eval "$cmd" 2>/dev/null; then
            print_ok "$uname updated"
          else
            print_fail "Could not update $uname. Run manually: $cmd"
          fi
        else
          print_warn "$uname: no auto-update command available"
        fi
      done
      ;;
    b|B)
      read -rp "Enter numbers (comma-separated): " selections
      IFS=',' read -ra sel_arr <<< "$selections"
      echo ""
      for sel in "${sel_arr[@]}"; do
        sel=$(echo "$sel" | tr -d '[:space:]')
        idx=$((sel - 1))
        if [ "$idx" -ge 0 ] && [ "$idx" -lt ${#UPDATE_CMDS[@]} ]; then
          cmd="${UPDATE_CMDS[$idx]}"
          uname="${UPDATES[$idx]%%  *}"
          uname="${uname%% *}"
          if [ -n "$cmd" ] && [ "$cmd" != "null" ]; then
            print_info "Updating $uname..."
            if eval "$cmd" 2>/dev/null; then
              print_ok "$uname updated"
            else
              print_fail "Could not update $uname. Run manually: $cmd"
            fi
          fi
        fi
      done
      ;;
    c|C|*)
      if [ ${#UPDATES[@]} -gt 0 ]; then
        echo ""
        echo "Manual update commands:"
        for idx in "${!UPDATES[@]}"; do
          echo "  ${UPDATES[$idx]%%  *}: ${UPDATE_CMDS[$idx]}"
        done
      fi
      ;;
  esac
elif [ ${#UPDATES[@]} -gt 0 ]; then
  # Non-interactive: just print commands
  echo ""
  echo "Update commands (run manually):"
  for idx in "${!UPDATES[@]}"; do
    uname="${UPDATES[$idx]%%  *}"
    echo "  $uname: ${UPDATE_CMDS[$idx]}"
  done
fi

# Exit code
if [ ${#BELOW_MIN[@]} -gt 0 ]; then
  exit 1
else
  exit 0
fi
