#!/usr/bin/env bats
# test_subagent_stop.bats

load "helpers"

@test "no Key Learnings section produces no output" {
    create_stub_jq
    run bash -c "echo '{\"last_assistant_message\":\"did some work\"}' | bash '$SCRIPTS_DIR/subagent-stop.sh'"
    assert_success
    assert_output ""
}

@test "Key Learnings section triggers additionalContext nudge" {
    create_stub_jq
    run bash -c "echo '{\"last_assistant_message\":\"done.\\n\\n## Key Learnings:\\n1. thing\"}' | bash '$SCRIPTS_DIR/subagent-stop.sh'"
    assert_success
    assert_output --partial '"hookSpecificOutput"'
    assert_output --partial '"hookEventName":"SubagentStop"'
    assert_output --partial 'mem_capture_passive'
    echo "$output" | jq -e . > /dev/null
}

@test "Spanish Aprendizajes Clave section triggers nudge" {
    create_stub_jq
    run bash -c "echo '{\"last_assistant_message\":\"## Aprendizajes Clave:\\n- x\"}' | bash '$SCRIPTS_DIR/subagent-stop.sh'"
    assert_success
    assert_output --partial 'mem_capture_passive'
}

@test "invalid stdin exits 0 with no output" {
    run bash -c "echo 'not json' | bash '$SCRIPTS_DIR/subagent-stop.sh'"
    assert_success
    assert_output ""
}

@test "does not shell out to the nonexistent gentle-ai mem subcommand" {
    cat > "$STUB_DIR/gentle-ai" << 'STUB_EOF'
#!/usr/bin/env bash
echo "invoked: $*" >> "$STUB_DIR/gentle-ai-calls.log"
exit 0
STUB_EOF
    chmod +x "$STUB_DIR/gentle-ai"
    create_stub_jq
    run bash -c "echo '{\"last_assistant_message\":\"## Key Learnings:\\n- x\"}' | bash '$SCRIPTS_DIR/subagent-stop.sh'"
    assert_success
    [ ! -f "$STUB_DIR/gentle-ai-calls.log" ]
}
