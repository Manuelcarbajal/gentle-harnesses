#!/usr/bin/env bash

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=gentle_ai.sh
source "$SCRIPTS_DIR/gentle_ai.sh"

CWD="${CLAUDE_PROJECT_DIR:-$(pwd)}"

input=$(cat)
hook_source=$(printf '%s' "$input" | jq -r '.source // ""' 2>/dev/null)

[ "$hook_source" != "compact" ] && exit 0

status=$(gentle_ai_review_status "$CWD")

if [ -n "$status" ]; then
    printf '{"systemMessage":"Context recovered after compaction. Review status: %s"}\n' "$status"
else
    printf '%s\n' '{"systemMessage":"Context compacted. Run gentle-ai review status if needed."}'
fi
