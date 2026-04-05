#!/bin/bash
# ==============================================================================
# compose.sh — Assembles a base reviewer template + project-type module
# ==============================================================================
#
# USAGE:
#   ./compose.sh <reviewer> <module> [output_file]
#
# REVIEWERS: engineer, cio, security, legal, techuser, redteam
# MODULES:   web-app, mobile-app, api-service, cli-tool, framework, desktop-app
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASES_DIR="${SCRIPT_DIR}/bases"
MODULES_DIR="${SCRIPT_DIR}/modules"

declare -A REVIEWER_BASE
REVIEWER_BASE[engineer]="01-senior-engineer.md"
REVIEWER_BASE[cio]="02-cio.md"
REVIEWER_BASE[security]="03-security.md"
REVIEWER_BASE[legal]="04-legal.md"
REVIEWER_BASE[techuser]="05-technical-user.md"
REVIEWER_BASE[redteam]="06-red-team-review.md"

declare -A REVIEWER_TAG
REVIEWER_TAG[engineer]="ENGINEER"
REVIEWER_TAG[cio]="CIO"
REVIEWER_TAG[security]="SECURITY"
REVIEWER_TAG[legal]="LEGAL"
REVIEWER_TAG[techuser]="TECHUSER"
REVIEWER_TAG[redteam]="REDTEAM"

if [ $# -lt 2 ]; then
    echo "Usage: $0 <reviewer> <module> [output_file]"
    echo ""
    echo "Reviewers: engineer, cio, security, legal, techuser, redteam"
    echo "Modules:   web-app, mobile-app, api-service, cli-tool, framework, desktop-app"
    exit 1
fi

REVIEWER="$1"
MODULE="$2"
OUTPUT="${3:-}"

if [[ ! -v "REVIEWER_BASE[$REVIEWER]" ]]; then
    echo "ERROR: Unknown reviewer '$REVIEWER'. Valid: engineer, cio, security, legal, techuser, redteam" >&2
    exit 1
fi

BASE_FILE="${BASES_DIR}/${REVIEWER_BASE[$REVIEWER]}"
MODULE_FILE="${MODULES_DIR}/${MODULE}.md"

if [ ! -f "$BASE_FILE" ]; then
    echo "ERROR: Base template not found: $BASE_FILE" >&2
    exit 1
fi

if [ ! -f "$MODULE_FILE" ]; then
    echo "ERROR: Module not found: $MODULE_FILE" >&2
    exit 1
fi

TAG="${REVIEWER_TAG[$REVIEWER]}"

# --- Extract section content between marker tags ---
extract_section() {
    local file="$1"
    local tag="$2"
    local section="$3"
    local open_marker="<!-- ${tag}:${section} -->"
    local end_marker="<!-- /${tag}:${section} -->"

    awk -v om="$open_marker" -v em="$end_marker" '
        index($0, om) { cap=1; next }
        index($0, em) { cap=0; next }
        cap { print }
    ' "$file"
}

# Extract sections from module
SECT_CONTEXT=$(extract_section "$MODULE_FILE" "$TAG" "CONTEXT")
SECT_CATEGORIES=$(extract_section "$MODULE_FILE" "$TAG" "CATEGORIES")
SECT_OUTPUT=$(extract_section "$MODULE_FILE" "$TAG" "OUTPUT")

# --- Assemble: read base line by line, inject content at placeholders ---
assemble() {
    while IFS= read -r line; do
        case "$line" in
            '{{DOMAIN_CONTEXT}}')
                [ -n "$SECT_CONTEXT" ] && printf '%s\n' "$SECT_CONTEXT"
                ;;
            '{{DOMAIN_CATEGORIES}}')
                [ -n "$SECT_CATEGORIES" ] && printf '%s\n' "$SECT_CATEGORIES"
                ;;
            '{{DOMAIN_OUTPUT}}')
                [ -n "$SECT_OUTPUT" ] && printf '%s\n' "$SECT_OUTPUT"
                ;;
            *)
                printf '%s\n' "$line"
                ;;
        esac
    done < "$BASE_FILE"
}

if [ -n "$OUTPUT" ]; then
    assemble > "$OUTPUT"
    echo "Composed: ${REVIEWER} + ${MODULE} → ${OUTPUT}" >&2
else
    assemble
fi
