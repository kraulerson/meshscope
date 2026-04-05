#!/usr/bin/env bash
set -euo pipefail
echo "Restoring from backup: .claude-backup/2026-04-05T140743"
read -rp "This will remove .claude/framework/ and .claude/project/. Continue? (y/n): " confirm
[ "$confirm" != "y" ] && exit 0
rm -rf .claude/framework .claude/project .claude/manifest.json
[ -f ".claude-backup/2026-04-05T140743/.claude/settings.json" ] && cp ".claude-backup/2026-04-05T140743/.claude/settings.json" .claude/settings.json
echo "Restored. Framework hooks removed, original settings restored."
