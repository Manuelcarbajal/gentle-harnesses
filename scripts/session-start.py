#!/usr/bin/env python3
"""
SessionStart health check for the gentle-ai + Claude Code ecosystem.
Verifies: gentle-ai binary, ecosystem health, codegraph binary, codegraph MCP config.
"""
import json
import os
import pathlib
import shutil
import subprocess


def run(cmd: list[str], timeout: int = 10) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "timeout"
    except FileNotFoundError:
        return 1, "", f"{cmd[0]}: not found"


def check_version() -> tuple[str, str]:
    code, out, err = run(["gentle-ai", "--version"], timeout=3)
    if code == 0 and out:
        return out.replace("gentle-ai ", "").strip(), ""
    return "", err or "gentle-ai not found"


def check_doctor() -> list[str]:
    code, out, _ = run(["gentle-ai", "doctor"], timeout=12)
    if code != 0 or not out:
        return ["gentle-ai doctor failed"]
    return [
        line.strip()
        for line in out.splitlines()
        if line.strip().startswith("[fail]")
    ]


def check_codegraph_binary() -> str:
    if shutil.which("codegraph"):
        return ""
    return "codegraph binary not in PATH — install via gentle-ai (community-tool:codegraph)"


def ensure_gga(cwd: str) -> str:
    if not shutil.which("gga"):
        return ""
    git_dir = pathlib.Path(cwd) / ".git"
    if not git_dir.exists():
        return ""
    hook = git_dir / "hooks" / "pre-commit"
    if hook.exists() and "gga" in hook.read_text(encoding="utf-8", errors="ignore"):
        return ""
    try:
        r = subprocess.run(
            "gga install", shell=True,
            capture_output=True, text=True, timeout=5, cwd=cwd,
            encoding="utf-8", errors="replace"
        )
        if r.returncode != 0:
            return f"gga install failed: {r.stderr.strip()}"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""
    return ""


def check_codegraph_mcp() -> str:
    settings_path = pathlib.Path.home() / ".claude" / "settings.json"
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        if "codegraph" not in data.get("mcpServers", {}):
            return (
                'codegraph missing from ~/.claude/settings.json mcpServers — '
                'add: {"command": "codegraph", "args": ["serve", "--mcp"]}'
            )
    except FileNotFoundError:
        return "~/.claude/settings.json not found"
    except (json.JSONDecodeError, ValueError) as exc:
        return f"~/.claude/settings.json parse error: {exc}"
    return ""


project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")

version, version_err = check_version()
doctor_failures = check_doctor()
codegraph_bin_err = check_codegraph_binary()
codegraph_mcp_err = check_codegraph_mcp()
gga_err = ensure_gga(project_dir) if project_dir else ""

issues = []
if version_err:
    issues.append(f"gentle-ai binary: {version_err}")
issues.extend(doctor_failures)
if codegraph_bin_err:
    issues.append(codegraph_bin_err)
if codegraph_mcp_err:
    issues.append(codegraph_mcp_err)
if gga_err:
    issues.append(gga_err)

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
