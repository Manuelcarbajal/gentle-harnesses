#!/usr/bin/env bash

input=$(cat)
last_message=$(printf '%s' "$input" | jq -r '.last_assistant_message // ""' 2>/dev/null)

printf '%s' "$last_message" | grep -qiE '## (Key Learnings|Aprendizajes Clave):' || exit 0

# a hook process cannot call MCP tools directly — nudge the agent via
# additionalContext to call mem_capture_passive itself instead
printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"SubagentStop","additionalContext":"Subagent output contains a Key Learnings section — call mem_capture_passive (source=\"subagent-stop\") with that content to persist it."}}'
