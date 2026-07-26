#!/usr/bin/env bats
# test_pre_tool_use.bats — Phase 4 and Phase 4b tests

load "helpers"

# ---------------------------------------------------------------------------
# Phase 4 — existing behavior
# ---------------------------------------------------------------------------

@test "non-bash tool exits 0" {
    export CLAUDE_TOOL_NAME="Read"
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_success
}

@test "empty command exits 0" {
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":""}'
    create_stub_jq
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_success
}

@test "other bash command exits 0" {
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"echo hello"}'
    create_stub_jq
    create_stub_gentle_ai
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_success
}

@test "git commit blocked when gate fails" {
    create_stub_jq
    create_stub_gentle_ai
    create_stub_git
    export STUB_GENTLE_AI_VALIDATE_EXIT=1
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"git commit -m test"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
    assert_output --partial '"decision":"block"'
}

@test "git commit allowed when gate passes" {
    create_stub_jq
    create_stub_gentle_ai
    create_stub_git
    export STUB_GENTLE_AI_VALIDATE_EXIT=0
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"git commit -m test"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_success
}

@test "git push blocked when gate fails" {
    create_stub_jq
    create_stub_gentle_ai
    export STUB_GENTLE_AI_VALIDATE_EXIT=1
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"git push"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
    assert_output --partial '"decision":"block"'
}

@test "git push allowed when gate passes" {
    create_stub_jq
    create_stub_gentle_ai
    export STUB_GENTLE_AI_VALIDATE_EXIT=0
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"git push"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_success
}

@test "git commit in chained && command is blocked" {
    create_stub_jq
    create_stub_gentle_ai
    create_stub_git
    export STUB_GENTLE_AI_VALIDATE_EXIT=1
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"npm test && git commit -m test"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
}

@test "git commit in chained ; command is blocked" {
    create_stub_jq
    create_stub_gentle_ai
    create_stub_git
    export STUB_GENTLE_AI_VALIDATE_EXIT=1
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"npm test; git commit -m test"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
}

@test "no gentle-ai binary fails open" {
    create_stub_jq
    create_stub_git
    # Do NOT create gentle-ai stub — binary missing
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"git commit -m test"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_success
}

@test "invalid json tool input exits 0" {
    create_stub_jq
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='not json'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_success
}

# ---------------------------------------------------------------------------
# Phase 4b — risk routing
# ---------------------------------------------------------------------------

@test "risk LOW: only .md files staged skips gate" {
    create_stub_jq
    create_stub_gentle_ai
    create_stub_git
    export STUB_GENTLE_AI_VALIDATE_EXIT=1
    export STUB_GIT_NAMES="README.md CHANGELOG.md"
    export STUB_GIT_SHORTSTAT=" 2 files changed, 10 insertions(+)"
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"git commit -m docs"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_success
}

@test "risk MED: mixed files staged validates gate" {
    create_stub_jq
    create_stub_gentle_ai
    create_stub_git
    export STUB_GENTLE_AI_VALIDATE_EXIT=1
    export STUB_GIT_NAMES="src/main.sh README.md"
    export STUB_GIT_SHORTSTAT=" 2 files changed, 10 insertions(+)"
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"git commit -m feat"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
}

@test "risk HIGH: >400 lines validates gate" {
    create_stub_jq
    create_stub_gentle_ai
    create_stub_git
    export STUB_GENTLE_AI_VALIDATE_EXIT=1
    export STUB_GIT_SHORTSTAT=" 5 files changed, 300 insertions(+), 150 deletions(-)"
    export STUB_GIT_NAMES="src/main.sh src/utils.sh"
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"git commit -m feat"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
}

@test "risk HIGH: auth path validates gate" {
    create_stub_jq
    create_stub_gentle_ai
    create_stub_git
    export STUB_GENTLE_AI_VALIDATE_EXIT=1
    export STUB_GIT_NAMES="src/auth/login.sh"
    export STUB_GIT_SHORTSTAT=" 1 file changed, 5 insertions(+)"
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"git commit -m feat"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
}

@test "risk MED: no staged files validates gate" {
    create_stub_jq
    create_stub_gentle_ai
    create_stub_git
    export STUB_GENTLE_AI_VALIDATE_EXIT=1
    export STUB_GIT_NAMES=""
    export STUB_GIT_SHORTSTAT=""
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"git commit -m feat"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
}

# ---------------------------------------------------------------------------
# Phase 4b — safety guards
# ---------------------------------------------------------------------------

@test "hard-deny: rm -rf / is blocked" {
    create_stub_jq
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"rm -rf /"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
    assert_output --partial '"decision":"block"'
}

@test "hard-deny: rm -rf /* is blocked" {
    create_stub_jq
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"rm -rf /*"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
}

@test "hard-deny: force push to main is blocked" {
    create_stub_jq
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"git push --force origin main"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
}

@test "hard-deny: force push -f to master is blocked" {
    create_stub_jq
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"git push -f origin master"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
}

@test "hard-deny: DROP TABLE is blocked" {
    create_stub_jq
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"psql -c \"DROP TABLE users\""}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
}

@test "hard-deny: overwriting .env is blocked" {
    create_stub_jq
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"echo \"SECRET=abc\" > .env"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
}

@test "confirm: git push --force to non-main is blocked" {
    create_stub_jq
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"git push --force origin feature-branch"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
    assert_output --partial 'confirmation'
}

@test "confirm: git reset --hard is blocked" {
    create_stub_jq
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"git reset --hard"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
    assert_output --partial 'confirmation'
}

@test "confirm: rm -rf non-root is blocked" {
    create_stub_jq
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"rm -rf ./dist"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_failure
}

@test "allow: normal git push passes safety guard" {
    create_stub_jq
    # Do NOT create gentle-ai stub — fail-open
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"git push"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_success
}

@test "allow: rm single file passes" {
    create_stub_jq
    export CLAUDE_TOOL_NAME="Bash"
    export CLAUDE_TOOL_INPUT='{"command":"rm somefile.txt"}'
    run bash "$SCRIPTS_DIR/pre-tool-use.sh"
    assert_success
}
