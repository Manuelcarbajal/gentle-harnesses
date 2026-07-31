#!/usr/bin/env bats
# test_user_prompt_submit.bats

load "helpers"

@test "no gentle-ai and no registry produces no output" {
    create_stub_jq
    # No gentle-ai stub, no registry file, no vendor content is ever injected
    # anymore (see HARNESS-AUDIT.md SS16) — nothing populates $parts.
    run bash "$SCRIPTS_DIR/user-prompt-submit.sh"
    assert_success
    assert_output ""
}

@test "vendor/gentle-pi content is never injected, redundant with gentle-ai's global install" {
    create_stub_jq
    create_stub_gentle_ai
    export STUB_GENTLE_AI_REVIEW_STATUS='{"action":"in-progress","next_transition":{"kind":"execute","execute":{"operation":"pre-commit"}}}'
    run bash "$SCRIPTS_DIR/user-prompt-submit.sh"
    assert_success
    refute_output --partial "Adapter Assets"
    refute_output --partial "Doc — review integration"
    refute_output --partial "Agent —"
    refute_output --partial "Delegation rules"
    refute_output --partial "Memory protocol"
    refute_output --partial "Skills discovery"
    refute_output --partial "SDD workflow"
    refute_output --partial "Chain —"
    refute_output --partial "Support —"
    refute_output --partial "skill style guide"
}

@test "review pending outputs systemMessage warning" {
    create_stub_jq
    create_stub_gentle_ai
    export STUB_GENTLE_AI_REVIEW_STATUS='{"action":"in-progress","next_transition":{"kind":"execute","execute":{"operation":"review.start"}}}'
    run bash "$SCRIPTS_DIR/user-prompt-submit.sh"
    assert_success
    assert_output --partial '"systemMessage"'
    assert_output --partial 'REVIEW REQUIRED'
}

@test "non-pending review injects status into context" {
    create_stub_jq
    create_stub_gentle_ai
    export STUB_GENTLE_AI_REVIEW_STATUS='{"action":"in-progress","next_transition":{"kind":"execute","execute":{"operation":"pre-commit"}}}'
    run bash "$SCRIPTS_DIR/user-prompt-submit.sh"
    assert_success
    assert_output --partial 'action=in-progress'
}

@test "injects skill registry from .atl/skill-registry.md" {
    create_stub_jq
    create_stub_gentle_ai
    mkdir -p "$CLAUDE_PROJECT_DIR/.atl"
    echo "skill: test" > "$CLAUDE_PROJECT_DIR/.atl/skill-registry.md"
    run bash "$SCRIPTS_DIR/user-prompt-submit.sh"
    assert_success
    assert_output --partial 'skill: test'
}

@test "both registry and review status combined" {
    create_stub_jq
    create_stub_gentle_ai
    export STUB_GENTLE_AI_REVIEW_STATUS='{"action":"in-progress","next_transition":{"kind":"execute","execute":{"operation":"pre-commit"}}}'
    mkdir -p "$CLAUDE_PROJECT_DIR/.atl"
    echo "skill: combined" > "$CLAUDE_PROJECT_DIR/.atl/skill-registry.md"
    run bash "$SCRIPTS_DIR/user-prompt-submit.sh"
    assert_success
    assert_output --partial 'skill: combined'
    assert_output --partial 'action=in-progress'
}

@test "missing registry exits cleanly with review status only" {
    create_stub_jq
    create_stub_gentle_ai
    export STUB_GENTLE_AI_REVIEW_STATUS='{"action":"in-progress","next_transition":{"kind":"execute","execute":{"operation":"pre-commit"}}}'
    # No registry file
    run bash "$SCRIPTS_DIR/user-prompt-submit.sh"
    assert_success
    assert_output --partial 'action=in-progress'
}

@test "missing jq exits cleanly instead of leaking a raw shell error" {
    # No create_stub_jq, and PATH excludes $HOME/.local/bin (where jq lives on
    # this dev machine) — simulates the real Claude Code hook PATH, which does
    # not include it. /usr/bin and /bin stay so cat/rm/tr (needed by bats'
    # own teardown and the script) remain available.
    export PATH="/usr/bin:/bin:/usr/local/bin"
    # No gentle-ai stub (its output needs jq to parse anyway). The skill
    # registry path needs no jq at all, so it alone populates $parts, forcing
    # the script down to the final printf | jq call.
    mkdir -p "$CLAUDE_PROJECT_DIR/.atl"
    echo "skill: test" > "$CLAUDE_PROJECT_DIR/.atl/skill-registry.md"
    run bash "$SCRIPTS_DIR/user-prompt-submit.sh"
    assert_success
    refute_output --partial "command not found"
}
