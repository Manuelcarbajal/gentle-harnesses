#!/usr/bin/env bats
# test_post_compaction.bats

load "helpers"

@test "non-compact source exits 0 with no output" {
    create_stub_gentle_ai
    create_stub_jq
    run bash -c "echo '{\"source\":\"startup\"}' | bash '$SCRIPTS_DIR/post-compaction.sh'"
    assert_success
    assert_output ""
}

@test "compact source with status outputs systemMessage with status" {
    create_stub_gentle_ai
    create_stub_jq
    export STUB_GENTLE_AI_REVIEW_STATUS='{"action":"in-progress"}'
    run bash -c "echo '{\"source\":\"compact\"}' | bash '$SCRIPTS_DIR/post-compaction.sh'"
    assert_success
    assert_output --partial '"systemMessage"'
    assert_output --partial 'in-progress'
}

@test "compact source without status outputs generic message" {
    create_stub_jq
    # No gentle-ai stub — no status available
    run bash -c "echo '{\"source\":\"compact\"}' | bash '$SCRIPTS_DIR/post-compaction.sh'"
    assert_success
    assert_output --partial 'Context compacted'
}

@test "invalid stdin exits 0" {
    run bash -c "echo 'not json' | bash '$SCRIPTS_DIR/post-compaction.sh'"
    assert_success
}
