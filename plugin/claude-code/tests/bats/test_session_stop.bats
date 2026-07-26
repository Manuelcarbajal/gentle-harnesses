#!/usr/bin/env bats
# test_session_stop.bats

load "helpers"

@test "always exits 0" {
    run bash "$SCRIPTS_DIR/session-stop.sh"
    assert_success
}

@test "exits 0 with no message when validate passes" {
    create_stub_gentle_ai
    export STUB_GENTLE_AI_VALIDATE_EXIT=0
    run bash "$SCRIPTS_DIR/session-stop.sh"
    assert_success
    assert_output ""
}

@test "exits 0 and delivers systemMessage synchronously when validate fails" {
    create_stub_gentle_ai
    export STUB_GENTLE_AI_VALIDATE_EXIT=1
    run bash "$SCRIPTS_DIR/session-stop.sh"
    assert_success
    assert_output --partial '"systemMessage"'
    assert_output --partial 'review gate check failed'
}
