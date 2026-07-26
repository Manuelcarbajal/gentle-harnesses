#!/usr/bin/env bats
# test_session_start.bats

load "helpers"

@test "outputs valid json" {
    create_stub_gentle_ai
    create_stub_codegraph
    create_stub_jq
    run bash "$SCRIPTS_DIR/session-start.sh"
    assert_success
    # Verify output is valid JSON
    echo "$output" | "$HOME/.local/bin/jq" -e . > /dev/null
}

@test "healthy ecosystem outputs hookSpecificOutput" {
    export STUB_GENTLE_AI_VERSION="gentle-ai 1.2.3"
    create_stub_gentle_ai
    create_stub_codegraph
    create_stub_jq
    run bash "$SCRIPTS_DIR/session-start.sh"
    assert_success
    assert_output --partial '"hookSpecificOutput"'
    assert_output --partial '1.2.3'
}

@test "missing gentle-ai binary outputs systemMessage" {
    # Do NOT create gentle-ai stub
    create_stub_codegraph
    create_stub_jq
    run bash "$SCRIPTS_DIR/session-start.sh"
    assert_success
    assert_output --partial '"systemMessage"'
    assert_output --partial 'gentle-ai'
}

@test "doctor failure outputs systemMessage" {
    export STUB_GENTLE_AI_DOCTOR_EXIT=1
    create_stub_gentle_ai
    create_stub_codegraph
    create_stub_jq
    run bash "$SCRIPTS_DIR/session-start.sh"
    assert_success
    assert_output --partial '"systemMessage"'
    assert_output --partial 'doctor'
}

@test "gentle-ai version failure outputs systemMessage" {
    export STUB_GENTLE_AI_VERSION=""
    create_stub_gentle_ai
    create_stub_codegraph
    create_stub_jq
    run bash "$SCRIPTS_DIR/session-start.sh"
    assert_success
    assert_output --partial 'version check failed'
}

@test "missing codegraph binary outputs systemMessage" {
    create_stub_gentle_ai
    # Do NOT create codegraph stub
    create_stub_jq
    run bash "$SCRIPTS_DIR/session-start.sh"
    assert_success
    assert_output --partial '"systemMessage"'
    assert_output --partial 'codegraph'
}

@test "multiple issues combined in one systemMessage" {
    # Missing both gentle-ai and codegraph
    create_stub_jq
    run bash "$SCRIPTS_DIR/session-start.sh"
    assert_success
    assert_output --partial '"systemMessage"'
}
