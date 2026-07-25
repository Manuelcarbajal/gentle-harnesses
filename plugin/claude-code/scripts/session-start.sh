#!/usr/bin/env bash

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=gentle_ai.sh
source "$SCRIPTS_DIR/gentle_ai.sh"

CWD="${CLAUDE_PROJECT_DIR:-$(pwd)}"

issues=()

bin=$(gentle_ai_bin)
version=""
if [ -z "$bin" ]; then
    issues+=("gentle-ai binary: gentle-ai not found")
else
    raw_version=$(timeout 5 "$bin" --version 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$raw_version" ]; then
        issues+=("gentle-ai binary: version check failed")
    else
        version=$(printf '%s' "$raw_version" | sed 's/^gentle-ai //' | tr -d '[:space:]')
    fi

    if ! gentle_ai_doctor; then
        issues+=("gentle-ai doctor: health check failed")
    fi
fi

if ! command -v codegraph >/dev/null 2>&1; then
    issues+=("codegraph binary not in PATH — install via gentle-ai (community-tool:codegraph)")
fi

if [ ${#issues[@]} -gt 0 ]; then
    bullet_list=""
    for issue in "${issues[@]}"; do
        bullet_list="${bullet_list}  • ${issue}\n"
    done
    printf '{"systemMessage":"⚠️  gentle-ai ecosystem issues detected:\n%sRun `gentle-ai doctor` or `gentle-ai sync` to fix."}\n' \
        "$bullet_list"
else
    printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"gentle-ai %s — ecosystem healthy"}}\n' \
        "$version"
fi
