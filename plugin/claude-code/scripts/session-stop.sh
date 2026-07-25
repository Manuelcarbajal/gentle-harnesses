#!/usr/bin/env bash

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=gentle_ai.sh
source "$SCRIPTS_DIR/gentle_ai.sh"

CWD="${CLAUDE_PROJECT_DIR:-$(pwd)}"

if gentle_ai_validate "post-apply" "$CWD"; then
    exit 0
else
    printf '%s\n' '{"systemMessage":"⚠️  review gate check failed — run gentle-ai review validate --gate post-apply for details"}'
fi
