#!/usr/bin/env python3
"""
PreToolUse gate: blocks git commit and git push when no valid review receipt exists.
Exit 2 = block the tool call. Exit 0 = allow.
"""
import json
import os
import subprocess
import sys

tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
tool_input = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())


def gate(name: str) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            ["gentle-ai", "review", "validate", "--gate", name, "--cwd", cwd],
            capture_output=True, text=True, timeout=8
        )
        if r.returncode == 0:
            return True, ""
        data = json.loads(r.stdout) if r.stdout.strip() else {}
        reason = data.get("reason", "receipt missing or invalidated")
        return False, reason
    except Exception as exc:
        return False, str(exc)


if tool_name != "Bash":
    sys.exit(0)

try:
    command = json.loads(tool_input).get("command", "")
except (json.JSONDecodeError, AttributeError):
    sys.exit(0)

if "git commit" in command:
    allowed, reason = gate("pre-commit")
    if not allowed:
        print(json.dumps({
            "decision": "block",
            "reason": f"review gate denied: {reason} — run the review cycle first (gentle-ai review start)"
        }))
        sys.exit(2)

if "git push" in command:
    allowed, reason = gate("pre-push")
    if not allowed:
        print(json.dumps({
            "decision": "block",
            "reason": f"review gate denied: {reason} — run the review cycle first (gentle-ai review start)"
        }))
        sys.exit(2)

sys.exit(0)
