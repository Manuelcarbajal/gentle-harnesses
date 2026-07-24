#!/usr/bin/env python3
"""
Injects gentle-ai context (skill registry + review status + SDD phase) into Claude Code
at UserPromptSubmit -- mirrors what gentle-pi does for Pi.
"""
import json
import os
import re
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


def get_sdd_status(cwd: str) -> str:
    try:
        result = subprocess.run(
            ["gentle-ai", "sdd-status"],
            capture_output=True, text=True, timeout=5, cwd=cwd
        )
        if result.returncode != 0 or not result.stdout.strip():
            return ""

        # extract JSON block from markdown output
        match = re.search(r"```json\s*(\{.*?\})\s*```", result.stdout, re.DOTALL)
        if not match:
            return ""

        data = json.loads(match.group(1))
        change = data.get("changeName")
        next_rec = data.get("nextRecommended", "")
        progress = data.get("taskProgress", {})

        # no active change — nothing useful to inject
        if not change:
            return ""

        total = progress.get("total", 0)
        completed = progress.get("completed", 0)
        deps = data.get("dependencies", {})
        ready_phase = next((k for k, v in deps.items() if v == "ready"), None)

        return (
            f"change: {change}\n"
            + (f"phase: {ready_phase}\n" if ready_phase else "")
            + f"tasks: {completed}/{total}\n"
            f"next: {next_rec}"
        )
    except Exception:
        return ""


registry = read_skill_registry(project_dir)
review = get_review_status(project_dir)
sdd = get_sdd_status(project_dir)

parts = []
if registry:
    parts.append(f"## Gentle-AI Skill Registry\n\n{registry}")
if review:
    parts.append(f"## Review Lifecycle\n\n{review}")
if sdd:
    parts.append(f"## SDD Status\n\n{sdd}")

if not parts:
    sys.exit(0)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": "\n\n---\n\n".join(parts)
    }
}))
