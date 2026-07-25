#!/usr/bin/env bash

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=gentle_ai.sh
source "$SCRIPTS_DIR/gentle_ai.sh"

CWD="${CLAUDE_PROJECT_DIR:-$(pwd)}"

review_raw=$(gentle_ai_review_status "$CWD")

action=""
next_op=""
if [ -n "$review_raw" ] && command -v jq >/dev/null 2>&1; then
    action=$(printf '%s' "$review_raw" | jq -r '.action // ""' 2>/dev/null)
    kind=$(printf '%s' "$review_raw" | jq -r '.next_transition.kind // ""' 2>/dev/null)
    if [ "$kind" = "execute" ]; then
        next_op=$(printf '%s' "$review_raw" | jq -r '.next_transition.execute.operation // ""' 2>/dev/null)
    else
        next_op="$kind"
    fi
fi

if [ -n "$action" ] && [ "$next_op" = "review.start" ]; then
    printf '%s\n' '{"systemMessage":"⚠️  REVIEW REQUIRED — no valid receipt for this workspace.\nRun `gentle-ai review start --cwd .` before any git commit or push.\ngit commit and git push are blocked until the review cycle completes."}'
    exit 0
fi

registry_path="$CWD/.atl/skill-registry.md"
registry=""
if [ -f "$registry_path" ]; then
    registry=$(< "$registry_path" tr -d '\r' 2>/dev/null)
fi

review_summary=""
if [ -n "$action" ]; then
    if [ -n "$next_op" ]; then
        review_summary="action=${action} next=${next_op}"
    else
        review_summary="action=${action}"
    fi
fi

parts=()
[ -n "$registry" ] && parts+=("## Gentle-AI Skill Registry\n\n${registry}")
[ -n "$review_summary" ] && parts+=("## Review Lifecycle\n\n${review_summary}")

if [ ${#parts[@]} -eq 0 ]; then
    exit 0
fi

context=""
for i in "${!parts[@]}"; do
    if [ $i -eq 0 ]; then
        context="${parts[$i]}"
    else
        context="${context}\n\n---\n\n${parts[$i]}"
    fi
done

# jq builds the JSON to safely handle arbitrary content in registry/review strings
printf '%s' "$context" | jq -Rs \
    '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":.}}'
