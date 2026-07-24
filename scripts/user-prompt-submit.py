#!/usr/bin/env python3
"""
Injects gentle-ai context (skill registry + review status) into Claude Code
at UserPromptSubmit — mirrors what gentle-pi does for Pi.
"""
import json
import os
import subprocess
import sys

project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

def read_skill_registry(cwd: str) -> str:
    path = os.path.join(cwd, ".atl", "skill-registry.md")
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def get_review_status(cwd: str) -> str:
    try:
        result = subprocess.run(
            ["gentle-ai", "review", "status",
             "--cwd", cwd,
             "--contract", "gentle-ai.review-integration/v1",
             "--next-transition"],
            capture_output=True, text=True, timeout=5, cwd=cwd
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            action = data.get("action", "")
            next_t = data.get("next_transition", {})
            kind = next_t.get("kind", "")
            op = next_t.get("execute", {}).get("operation", "") if kind == "execute" else kind
            return f"action={action} next={op}" if op else f"action={action}"
    except Exception:
        pass
    return ""

registry = read_skill_registry(project_dir)
review = get_review_status(project_dir)

parts = []
if registry:
    parts.append(f"## Gentle-AI Skill Registry\n\n{registry}")
if review:
    parts.append(f"## Review Lifecycle\n\n{review}")

if not parts:
    sys.exit(0)

context = "\n\n---\n\n".join(parts)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": context
    }
}))
