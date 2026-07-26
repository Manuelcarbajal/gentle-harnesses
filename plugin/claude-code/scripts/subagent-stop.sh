#!/usr/bin/env bash

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=gentle_ai.sh
source "$SCRIPTS_DIR/gentle_ai.sh"

bin=$(gentle_ai_bin)
[ -z "$bin" ] && exit 0

timeout 10 "$bin" mem capture --passive --quiet 2>/dev/null || true

exit 0
