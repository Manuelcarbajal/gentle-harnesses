#!/usr/bin/env bats
# test_user_prompt_submit.bats

load "helpers"

@test "no gentle-ai and no registry still emits asset manifest" {
    create_stub_jq
    # No gentle-ai stub, no registry file — vendor assets are always injected
    run bash "$SCRIPTS_DIR/user-prompt-submit.sh"
    assert_success
    assert_output --partial "Adapter Assets"
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
