#!/usr/bin/env python3
"""
SessionStart health check for the gentle-ai + Claude Code ecosystem.
Verifies: gentle-ai binary, ecosystem health, codegraph binary.
"""
import gentle_ai
import json
import os
import shutil


def check_version() -> tuple[str, str]:
    v = gentle_ai.version()
    return (v, "") if v else ("", "gentle-ai not found")


def check_doctor() -> list[str]:
    return gentle_ai.doctor()


def check_codegraph_binary() -> str:
    if shutil.which("codegraph"):
        return ""
    return "codegraph binary not in PATH — install via gentle-ai (community-tool:codegraph)"



def main() -> None:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")

    version, version_err = check_version()
    doctor_failures = check_doctor() if not version_err else []
    codegraph_bin_err = check_codegraph_binary()

    issues: list[str] = []
    if version_err:
        issues.append(f"gentle-ai binary: {version_err}")
    issues.extend(doctor_failures)
    if codegraph_bin_err:
        issues.append(codegraph_bin_err)

    if issues:
        bullet_list = "\n".join(f"  • {i}" for i in issues)
        print(json.dumps({
            "systemMessage": (
                f"⚠️  gentle-ai ecosystem issues detected:\n{bullet_list}\n"
                "Run `gentle-ai doctor` or `gentle-ai sync` to fix."
            )
        }))
    else:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": f"gentle-ai {version} — ecosystem healthy"
            }
        }))


if __name__ == "__main__":
    main()
