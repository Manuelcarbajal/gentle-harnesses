#!/usr/bin/env python3
"""
SessionStart health check for the gentle-ai + Claude Code ecosystem.
Runs gentle-ai doctor and verifies the context injection hook still works.
Outputs systemMessage on failure, additionalContext with version on success.
"""
import json
import os
import subprocess
import sys

def run(cmd: list[str], timeout: int = 10) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "timeout"
    except FileNotFoundError:
        return 1, "", f"{cmd[0]}: not found"

def check_version() -> tuple[str, str]:
    code, out, err = run(["gentle-ai", "--version"])
    if code == 0 and out:
        return out.replace("gentle-ai ", "").strip(), ""
    return "", err or "gentle-ai not found"

def check_doctor() -> list[str]:
    code, out, _ = run(["gentle-ai", "doctor"], timeout=15)
    if code != 0 or not out:
        return ["gentle-ai doctor failed"]
    failures = []
    for line in out.splitlines():
        if line.strip().startswith("[fail]"):
            failures.append(line.strip())
    return failures

def check_context_hook() -> str:
    script = os.path.join(os.path.dirname(__file__), "gentle-ai-context.py")
    if not os.path.exists(script):
        return f"gentle-ai-context.py not found at {script}"
    code, out, err = run(["python", script], timeout=10)
    if code != 0:
        return f"gentle-ai-context.py exited {code}: {err or out}"
    try:
        data = json.loads(out)
        if "hookSpecificOutput" not in data and out:
            return "gentle-ai-context.py output missing hookSpecificOutput"
    except (json.JSONDecodeError, ValueError):
        if out:
            return f"gentle-ai-context.py produced invalid JSON"
    return ""

version, version_err = check_version()
doctor_failures = check_doctor()
hook_err = check_context_hook()

issues = []
if version_err:
    issues.append(f"gentle-ai binary: {version_err}")
issues.extend(doctor_failures)
if hook_err:
    issues.append(f"context hook: {hook_err}")

if issues:
    bullet_list = "\n".join(f"  • {i}" for i in issues)
    print(json.dumps({
        "systemMessage": (
            f"⚠️  gentle-ai ecosystem issues detected:\n{bullet_list}\n"
            f"Run `gentle-ai doctor` or `gentle-ai upgrade` to fix."
        )
    }))
else:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": f"gentle-ai {version} — ecosystem healthy"
        }
    }))
