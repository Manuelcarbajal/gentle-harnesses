#!/usr/bin/env python3
"""
PreToolUse gate: blocks git commit and git push when no valid review receipt exists.
Exit 2 = block the tool call. Exit 0 = allow.
"""
import json
import os
import re
import shutil
import subprocess
import sys

_gentle_ai = shutil.which("gentle-ai") or "gentle-ai"


def gate(name: str, cwd: str) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            [_gentle_ai, "review", "validate", "--gate", name, "--cwd", cwd],
            capture_output=True, text=True, timeout=4
        )
        if r.returncode == 0:
            return True, ""
        data = json.loads(r.stdout) if r.stdout.strip() else {}
        reason = data.get("reason", "receipt missing or invalidated")
        return False, reason
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return True, ""  # tool unavailable → fail-open, never block commits
    except Exception as exc:
        return True, str(exc)


def main() -> None:
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    tool_input = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
    cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    if tool_name != "Bash":
        sys.exit(0)
        return

    try:
        command = json.loads(tool_input).get("command", "")
    except (json.JSONDecodeError, AttributeError):
        sys.exit(0)
        return

    if re.search(r"(?:^|&&|\|\||;)\s*git\s+commit(?:\s|$)", command):
        allowed, reason = gate("pre-commit", cwd)
        if not allowed:
            print(json.dumps({
                "decision": "block",
                "reason": f"review gate denied: {reason} — run the review cycle first (gentle-ai review start)"
            }))
            sys.exit(2)
            return

    if re.search(r"(?:^|&&|\|\||;)\s*git\s+push(?:\s|$)", command):
        allowed, reason = gate("pre-push", cwd)
        if not allowed:
            print(json.dumps({
                "decision": "block",
                "reason": f"review gate denied: {reason} — run the review cycle first (gentle-ai review start)"
            }))
            sys.exit(2)
            return

    sys.exit(0)


if __name__ == "__main__":
    main()
