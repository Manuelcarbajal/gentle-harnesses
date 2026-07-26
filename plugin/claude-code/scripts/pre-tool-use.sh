#!/usr/bin/env bash

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=gentle_ai.sh
source "$SCRIPTS_DIR/gentle_ai.sh"

tool_name="${CLAUDE_TOOL_NAME:-}"
# Note: ${VAR:-{}} appends an extra } in bash when VAR is set — use assignment guard instead
tool_input="${CLAUDE_TOOL_INPUT}"
[ -z "$tool_input" ] && tool_input='{}'
CWD="${CLAUDE_PROJECT_DIR:-$(pwd)}"

[ "$tool_name" != "Bash" ] && exit 0

if ! command -v jq >/dev/null 2>&1; then
    exit 0
fi

cmd=$(printf '%s' "$tool_input" | jq -r '.command // ""' 2>/dev/null)
[ $? -ne 0 ] && exit 0
[ -z "$cmd" ] && exit 0

# ---------------------------------------------------------------------------
# classify_diff: returns LOW / MED / HIGH based on staged diff
# ---------------------------------------------------------------------------
# Fallback used when gentle_ai_review_tier finds no applicable receipt or the CLI is unavailable — the gate itself never starts a review.
classify_diff() {
    local cwd="$1"

    command -v git >/dev/null 2>&1 || { printf 'MED'; return; }

    local shortstat changed_paths total_lines non_doc
    shortstat=$(cd "$cwd" 2>/dev/null && git diff --staged --shortstat 2>/dev/null || echo "")
    changed_paths=$(cd "$cwd" 2>/dev/null && git diff --staged --name-only 2>/dev/null || echo "")

    total_lines=$(printf '%s' "$shortstat" | grep -oE '[0-9]+' | awk '{s+=$1} END {print s+0}')

    if [ "${total_lines:-0}" -gt 400 ]; then
        printf 'HIGH'; return
    fi

    if printf '%s' "$changed_paths" | grep -qiE '(^|[/_.-])(auth|authentication|authorization|update|updater|security|payment|payments|permission|permissions|shell|process|secret|secrets|credential|credentials|token|tokens)([/_.-]|$)'; then
        printf 'HIGH'; return
    fi

    non_doc=$(printf '%s' "$changed_paths" | grep -vE '\.(md|txt|rst|adoc|markdown)$' | grep -v '^[[:space:]]*$')
    if [ -n "$changed_paths" ] && [ -z "$non_doc" ]; then
        printf 'LOW'; return
    fi

    printf 'MED'
}

# ---------------------------------------------------------------------------
# classify_command: returns ALLOW / CONFIRM:<reason> / HARD_DENY:<reason>
# ---------------------------------------------------------------------------
classify_command() {
    local cmd="$1"

    # Hard-deny: rm -rf on root, home root, or wildcard root
    if printf '%s' "$cmd" | grep -qE 'rm[[:space:]]+-[a-zA-Z]*r[a-zA-Z]*f?[[:space:]]+~?/\*?[[:space:]]*$'; then
        printf 'HARD_DENY:rm -rf on root or home path — this command is blocked'; return
    fi

    # Hard-deny: force push to main or master
    if printf '%s' "$cmd" | grep -qE 'git[[:space:]]+push[[:space:]]+(--force|-f)[[:space:]].*[[:space:]](main|master)([[:space:]]|$)'; then
        printf 'HARD_DENY:force push to main/master is permanently blocked'; return
    fi
    if printf '%s' "$cmd" | grep -qE 'git[[:space:]]+push[[:space:]]+.*[[:space:]](main|master)[[:space:]]+(--force|-f)([[:space:]]|$)'; then
        printf 'HARD_DENY:force push to main/master is permanently blocked'; return
    fi

    # Hard-deny: SQL DROP
    if printf '%s' "$cmd" | grep -qiE 'DROP[[:space:]]+(TABLE|DATABASE|SCHEMA)[[:space:]]'; then
        printf 'HARD_DENY:SQL DROP statement is blocked'; return
    fi

    # Hard-deny: overwrite .env (> but not >>)
    if printf '%s' "$cmd" | grep -qE '[^>]>[[:space:]]*.env([[:space:]]|$)'; then
        printf 'HARD_DENY:overwriting .env file is blocked'; return
    fi

    # Confirm: force push to non-main
    if printf '%s' "$cmd" | grep -qE 'git[[:space:]]+push[[:space:]]+.*(--force|-f)'; then
        printf 'CONFIRM:force push requires explicit user confirmation'; return
    fi

    # Confirm: git reset --hard
    if printf '%s' "$cmd" | grep -qE 'git[[:space:]]+reset[[:space:]]+--hard'; then
        printf 'CONFIRM:git reset --hard discards all uncommitted changes'; return
    fi

    # Confirm: recursive delete
    if printf '%s' "$cmd" | grep -qE '(^|&&|\|\||;)[[:space:]]*rm[[:space:]]+-[a-zA-Z]*r[a-zA-Z]*[[:space:]]'; then
        printf 'CONFIRM:recursive deletion requires explicit user confirmation'; return
    fi

    printf 'ALLOW'
}

# Safety guard classification
guard_result=$(classify_command "$cmd")
guard_class="${guard_result%%:*}"
guard_reason="${guard_result#*:}"

if [ "$guard_class" = "HARD_DENY" ]; then
    printf '{"decision":"block","reason":"%s"}\n' "$guard_reason"
    exit 2
fi

if [ "$guard_class" = "CONFIRM" ]; then
    printf '{"decision":"block","reason":"Requires explicit confirmation — %s. Ask the user to confirm, then reissue the command."}\n' "$guard_reason"
    exit 2
fi

# Risk-based review gate for git commit
if printf '%s' "$cmd" | grep -qE '(^|&&|\|\||;)[[:space:]]*git[[:space:]]+commit([[:space:]]|$)'; then
    tier=$(gentle_ai_review_tier "$CWD") || tier=$(classify_diff "$CWD")
    if [ "$tier" != "LOW" ]; then
        if ! gentle_ai_validate "pre-commit" "$CWD"; then
            printf '%s\n' '{"decision":"block","reason":"review gate denied: receipt missing or invalidated — run the review cycle first (gentle-ai review start)"}'
            exit 2
        fi
    fi
fi

if printf '%s' "$cmd" | grep -qE '(^|&&|\|\||;)[[:space:]]*git[[:space:]]+push([[:space:]]|$)'; then
    if ! gentle_ai_validate "pre-push" "$CWD"; then
        printf '%s\n' '{"decision":"block","reason":"review gate denied: receipt missing or invalidated — run the review cycle first (gentle-ai review start)"}'
        exit 2
    fi
fi

exit 0
