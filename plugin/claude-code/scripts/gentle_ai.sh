#!/usr/bin/env bash

gentle_ai_bin() {
    local local_bin="${CLAUDE_PLUGIN_ROOT}/bin/gentle-ai"
    if [ -x "$local_bin" ]; then
        echo "$local_bin"
        return 0
    fi
    command -v gentle-ai 2>/dev/null || echo ""
}

gentle_ai_version() {
    local bin
    bin=$(gentle_ai_bin)
    [ -z "$bin" ] && return 1
    timeout 5 "$bin" --version >/dev/null 2>&1
}

gentle_ai_doctor() {
    local bin
    bin=$(gentle_ai_bin)
    [ -z "$bin" ] && return 1
    timeout 10 "$bin" doctor >/dev/null 2>&1
}

gentle_ai_validate() {
    local gate="$1" cwd="$2"
    local bin
    bin=$(gentle_ai_bin)
    [ -z "$bin" ] && return 0
    timeout 10 "$bin" review validate --gate "$gate" --cwd "$cwd" >/dev/null 2>&1
    local rc=$?
    [ $rc -eq 124 ] && return 0
    return $rc
}

gentle_ai_review_tier() {
    local cwd="$1"
    local bin
    bin=$(gentle_ai_bin)
    [ -z "$bin" ] && return 1
    local out
    out=$(timeout 10 "$bin" review status --cwd "$cwd" \
        --contract gentle-ai.review-integration/v1 \
        --projection staged 2>/dev/null) || return 1
    local applicability
    applicability=$(printf '%s' "$out" | jq -r '.applicability // empty' 2>/dev/null)
    [ "$applicability" != "current_target" ] && return 1
    local tier
    tier=$(printf '%s' "$out" | jq -r '.frozen.tier // empty' 2>/dev/null)
    case "$tier" in
        low) printf 'LOW' ;;
        medium) printf 'MED' ;;
        high) printf 'HIGH' ;;
        *) return 1 ;;
    esac
}

gentle_ai_review_status() {
    local cwd="$1"
    local bin
    bin=$(gentle_ai_bin)
    [ -z "$bin" ] && echo "" && return 1
    local out
    out=$(timeout 6 "$bin" review status --cwd "$cwd" \
        --contract gentle-ai.review-integration/v1 \
        --next-transition 2>/dev/null) || { echo ""; return 1; }
    echo "$out"
}
