#!/usr/bin/env bash

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=gentle_ai.sh
source "$SCRIPTS_DIR/gentle_ai.sh"

CWD="${CLAUDE_PROJECT_DIR:-$(pwd)}"
ADAPTER_ROOT="$(cd "$SCRIPTS_DIR/../../.." && pwd)"

# ---------------------------------------------------------------------------
# adapter_skill_rows: emit registry table rows for skills not already present
# in the official registry. Scans $1 (dir) with scope label $2.
# Deduplicates against $3 (existing registry content).
# ---------------------------------------------------------------------------
adapter_skill_rows() {
    local dir="$1" scope="$2" existing="$3"
    [ -d "$dir" ] || return 0
    for skill_md in "$dir"/*/SKILL.md; do
        [ -f "$skill_md" ] || continue
        local name description
        name="$(basename "$(dirname "$skill_md")")"
        printf '%s' "$existing" | grep -qF "| \`${name}\`" && continue
        description=$(awk 'BEGIN{f=0} /^---/{f++; next} f==1 && /^description:/{
            sub(/^description:[[:space:]]*/,""); gsub(/^"/,""); gsub(/"$/,""); print; exit
        }' "$skill_md")
        [ -z "$description" ] && description="(no description)"
        printf '| `%s` | %s | %s | `%s` |\n' "$name" "$description" "$scope" "$skill_md"
    done
}

# ---------------------------------------------------------------------------
# inject_adapter_skills: append adapter-owned skills to the official registry.
# Priority: plugin skills override vendor skills of the same name.
# REMOVE this function if gentle-ai adds native support for these paths.
# ---------------------------------------------------------------------------
inject_adapter_skills() {
    local registry="$1"
    local plugin_dir="$ADAPTER_ROOT/plugin/claude-code/skills"
    local vendor_dir="$ADAPTER_ROOT/vendor/gentle-pi/skills"

    local plugin_rows vendor_rows
    plugin_rows=$(adapter_skill_rows "$plugin_dir" "plugin" "$registry")
    local augmented="${registry}${plugin_rows}"
    vendor_rows=$(adapter_skill_rows "$vendor_dir" "adapter" "$augmented")

    [ -z "$plugin_rows" ] && [ -z "$vendor_rows" ] && { printf '%s' "$registry"; return; }

    local header
    header="$(printf '\n\n## Adapter Skills\n\n| Skill | Trigger / description | Scope | Path |\n| --- | --- | --- | --- |')"
    printf '%s%s\n%s%s' "$registry" "$header" "$plugin_rows" "$vendor_rows"
}

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
    registry=$(inject_adapter_skills "$registry")
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
