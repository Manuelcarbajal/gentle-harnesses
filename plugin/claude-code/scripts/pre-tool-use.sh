#!/usr/bin/env bash

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=gentle_ai.sh
source "$SCRIPTS_DIR/gentle_ai.sh"

tool_name="${CLAUDE_TOOL_NAME:-}"
tool_input="${CLAUDE_TOOL_INPUT:-{}}"
CWD="${CLAUDE_PROJECT_DIR:-$(pwd)}"

[ "$tool_name" != "Bash" ] && exit 0

if ! command -v jq >/dev/null 2>&1; then
    exit 0
fi

cmd=$(printf '%s' "$tool_input" | jq -r '.command // ""' 2>/dev/null)
[ $? -ne 0 ] && exit 0
[ -z "$cmd" ] && exit 0

if printf '%s' "$cmd" | grep -qE '(^|&&|\|\||;)[[:space:]]*git[[:space:]]+commit([[:space:]]|$)'; then
    if ! gentle_ai_validate "pre-commit" "$CWD"; then
        printf '%s\n' '{"decision":"block","reason":"review gate denied: receipt missing or invalidated — run the review cycle first (gentle-ai review start)"}'
        exit 2
    fi
fi

if printf '%s' "$cmd" | grep -qE '(^|&&|\|\||;)[[:space:]]*git[[:space:]]+push([[:space:]]|$)'; then
    if ! gentle_ai_validate "pre-push" "$CWD"; then
        printf '%s\n' '{"decision":"block","reason":"review gate denied: receipt missing or invalidated — run the review cycle first (gentle-ai review start)"}'
        exit 2
    fi
fi

exit 0
