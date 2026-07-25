#!/usr/bin/env bash

gentle_ai_bin() {
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

gentle_ai_review_status() {
    local cwd="$1"
    local bin
    bin=$(gentle_ai_bin)
    [ -z "$bin" ] && echo "" && return 1
    local out
    out=$(timeout 5 "$bin" review status --cwd "$cwd" \
        --contract gentle-ai.review-integration/v1 \
        --next-transition 2>/dev/null) || { echo ""; return 1; }
    echo "$out"
}
