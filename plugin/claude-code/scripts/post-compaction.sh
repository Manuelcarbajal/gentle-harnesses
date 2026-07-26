#!/usr/bin/env bash

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=gentle_ai.sh
source "$SCRIPTS_DIR/gentle_ai.sh"

CWD="${CLAUDE_PROJECT_DIR:-$(pwd)}"

trigger=$(python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('trigger',''))" 2>/dev/null)

[ "$trigger" != "post_compact" ] && exit 0

status=$(gentle_ai_review_status "$CWD")

if [ -n "$status" ]; then
    printf '{"systemMessage":"Context recovered after compaction. Review status: %s"}\n' "$status"
else
    printf '%s\n' '{"systemMessage":"Context compacted. Run gentle-ai review status if needed."}'
fi
