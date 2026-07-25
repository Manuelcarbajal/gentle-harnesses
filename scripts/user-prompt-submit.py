#!/usr/bin/env python3
"""
Injects gentle-ai context (skill registry + review status + SDD phase) into Claude Code
at UserPromptSubmit -- mirrors what gentle-pi does for Pi.
"""
import gentle_ai
import json
import os
import sys

def read_skill_registry(cwd: str) -> str:
    path = os.path.join(cwd, ".atl", "skill-registry.md")
    try:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def get_review_status(cwd: str) -> str:
    data = gentle_ai.review_status(cwd)
    if not data:
        return ""
    action = data.get("action", "")
    next_t = data.get("next_transition", {})
    kind = next_t.get("kind", "")
    op = next_t.get("execute", {}).get("operation", "") if kind == "execute" else kind
    return f"action={action} next={op}" if op else f"action={action}"



def main() -> None:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    registry = read_skill_registry(project_dir)
    review = get_review_status(project_dir)

    review_pending = review and "next=review.start" in review
    if review_pending:
        print(json.dumps({
            "systemMessage": (
                "⚠️  REVIEW REQUIRED — no valid receipt for this workspace.\n"
                "Run `gentle-ai review start --cwd .` before any git commit or push.\n"
                "git commit and git push are blocked until the review cycle completes."
            )
        }))
        sys.exit(0)
        return

    parts = []
    if registry:
        parts.append(f"## Gentle-AI Skill Registry\n\n{registry}")
    if review:
        parts.append(f"## Review Lifecycle\n\n{review}")

    if not parts:
        sys.exit(0)
        return

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "\n\n---\n\n".join(parts)
        }
    }))


if __name__ == "__main__":
    main()
