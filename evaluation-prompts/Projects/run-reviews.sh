#!/bin/bash
# ==============================================================================
# run-reviews.sh — Execute framework review suite against any project
# ==============================================================================
# Composes base templates + project-type modules, then runs each review
# in a separate Claude Code CLI instance.
#
# USAGE:
#   ./run-reviews.sh <module> [reviewer_numbers...]
#
# EXAMPLES:
#   ./run-reviews.sh web-app              # All 6 reviews for a web app
#   ./run-reviews.sh mobile-app 1 3       # Engineer + Security for mobile
#   ./run-reviews.sh framework            # All 6 reviews for a framework
#   ./run-reviews.sh api-service 2 4 5    # CIO + Legal + TechUser for API
#
# MODULES: web-app, mobile-app, api-service, cli-tool, framework, desktop-app
#
# ENVIRONMENT:
#   PROJECT_DIR  — path to project (default: current directory)
#   REVIEW_DIR   — path to reviews/ directory (default: ./reviews or auto-detect)
#
# OUTPUT:
#   Review files written to the project root directory:
#     senior-engineer-review-v1.md
#     cio-review-v1.md
#     security-review-v1.md
#     legal-review-v1.md
#     technical-user-review-v1.md
#     red-team-review-v1.md
# ==============================================================================

set -euo pipefail

# --- Locate reviews directory ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if compose.sh is alongside this script (reviews/ is the script dir)
# or if reviews/ is a subdirectory
if [ -f "${SCRIPT_DIR}/compose.sh" ]; then
    REVIEW_DIR="${REVIEW_DIR:-$SCRIPT_DIR}"
elif [ -f "${SCRIPT_DIR}/reviews/compose.sh" ]; then
    REVIEW_DIR="${REVIEW_DIR:-${SCRIPT_DIR}/reviews}"
else
    echo "ERROR: Cannot locate compose.sh. Set REVIEW_DIR to the reviews/ directory."
    exit 1
fi

PROJECT_DIR="${PROJECT_DIR:-$(pwd)}"

# --- Validate ---
if ! command -v claude &> /dev/null; then
    echo "ERROR: 'claude' CLI not found. Install Claude Code first."
    exit 1
fi

if [ ! -d "$PROJECT_DIR" ]; then
    echo "ERROR: Project directory not found: $PROJECT_DIR"
    exit 1
fi

chmod +x "${REVIEW_DIR}/compose.sh" 2>/dev/null || true

# --- Args ---
usage() {
    echo "Usage: $0 <module> [reviewer_numbers...]"
    echo ""
    echo "Modules: web-app, mobile-app, api-service, cli-tool, framework, desktop-app"
    echo ""
    echo "Reviewers:"
    echo "  1 = Senior Software Engineer"
    echo "  2 = CIO"
    echo "  3 = SVP IT Security"
    echo "  4 = Corporate Legal"
    echo "  5 = Technical User (Non-Coder)"
    echo "  6 = Red Team / Offensive Security"
    echo ""
    echo "Examples:"
    echo "  $0 web-app           # All 5 reviews"
    echo "  $0 mobile-app 1 3    # Engineer + Security only"
    echo "  $0 framework 2 4 5   # CIO + Legal + TechUser"
    echo ""
    echo "Environment:"
    echo "  PROJECT_DIR=/path/to/project $0 web-app"
    exit 1
}

if [ $# -lt 1 ]; then
    usage
fi

MODULE="$1"
shift

# Validate module exists
if [ ! -f "${REVIEW_DIR}/modules/${MODULE}.md" ]; then
    echo "ERROR: Module '${MODULE}' not found."
    echo "Available modules:"
    ls -1 "${REVIEW_DIR}/modules/"*.md 2>/dev/null | xargs -I{} basename {} .md
    exit 1
fi

# Reviewer definitions
declare -A REVIEWERS
REVIEWERS[1]="engineer|Senior Software Engineer"
REVIEWERS[2]="cio|CIO Strategic"
REVIEWERS[3]="security|SVP IT Security"
REVIEWERS[4]="legal|Corporate Legal"
REVIEWERS[5]="techuser|Technical User (Non-Coder)"
REVIEWERS[6]="redteam|Red Team / Offensive Security"

# Determine which reviews to run
if [ $# -eq 0 ]; then
    TARGETS=(1 2 3 4 5 6)
else
    TARGETS=("$@")
fi

# --- Temp directory for composed prompts ---
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# --- Run ---
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║     PROJECT REVIEW SUITE                        ║"
echo "║     Module: ${MODULE}$(printf '%*s' $((26 - ${#MODULE})) '')║"
echo "║     Reviews: ${#TARGETS[@]}$(printf '%*s' 36 '')║"
echo "║     Project: ${PROJECT_DIR:0:34}$(printf '%*s' $((1)) '')║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

for num in "${TARGETS[@]}"; do
    if [[ ! -v "REVIEWERS[$num]" ]]; then
        echo "WARNING: Review $num does not exist. Valid: 1-6"
        continue
    fi

    entry="${REVIEWERS[$num]}"
    reviewer="${entry%%|*}"
    description="${entry##*|}"
    prompt_file="${TEMP_DIR}/${reviewer}-prompt.md"

    echo "=============================================="
    echo "  REVIEW $num: $description"
    echo "=============================================="
    echo "  Composing: ${reviewer} + ${MODULE}"

    # Compose the prompt
    "${REVIEW_DIR}/compose.sh" "$reviewer" "$MODULE" "$prompt_file"

    echo "  Directory: $PROJECT_DIR"
    echo "  Started: $(date)"
    echo "----------------------------------------------"

    # Run claude code with the composed prompt from the project directory
    (cd "$PROJECT_DIR" && claude -p "$(cat "$prompt_file")")

    echo ""
    echo "  Completed: $(date)"
    echo "=============================================="
    echo ""
done

echo ""
echo "All requested reviews complete."
echo "Output files in: $PROJECT_DIR/"
ls -la "$PROJECT_DIR"/*-review-v1.md 2>/dev/null || echo "(No review files found — check for errors above)"
