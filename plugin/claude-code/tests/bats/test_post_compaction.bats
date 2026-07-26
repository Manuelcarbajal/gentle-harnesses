#!/usr/bin/env bats
# test_post_compaction.bats

load "helpers"

@test "non-compact trigger exits 0 with no output" {
    create_stub_gentle_ai
    run bash -c "echo '{\"trigger\":\"other\"}' | bash '$SCRIPTS_DIR/post-compaction.sh'"
    assert_success
    assert_output ""
}

@test "post_compact trigger with status outputs systemMessage with status" {
    create_stub_gentle_ai
    export STUB_GENTLE_AI_REVIEW_STATUS='{"action":"in-progress"}'
    run bash -c "echo '{\"trigger\":\"post_compact\"}' | bash '$SCRIPTS_DIR/post-compaction.sh'"
    assert_success
    assert_output --partial '"systemMessage"'
    assert_output --partial 'in-progress'
}

@test "post_compact trigger without status outputs generic message" {
    # No gentle-ai stub — no status available
    run bash -c "echo '{\"trigger\":\"post_compact\"}' | bash '$SCRIPTS_DIR/post-compaction.sh'"
    assert_success
    assert_output --partial 'Context compacted'
}

@test "invalid stdin exits 0" {
    run bash -c "echo 'not json' | bash '$SCRIPTS_DIR/post-compaction.sh'"
    assert_success
}
