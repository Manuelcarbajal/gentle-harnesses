#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys


def run(cmd: list[str], timeout: int = 10, cwd: str | None = None) -> tuple[bool, str]:
    """Run a CLI command. Returns (ok, stdout)."""
    resolved = shutil.which(cmd[0]) or cmd[0]
    try:
        r = subprocess.run(
            [resolved, *cmd[1:]], capture_output=True, text=True, timeout=timeout,
            cwd=cwd, encoding="utf-8", errors="replace",
        )
        return r.returncode == 0, r.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, ""


def version() -> str:
    ok, out = run(["gentle-ai", "--version"], timeout=3)
    if ok and out:
        return out.replace("gentle-ai ", "").strip()
    return ""


def doctor() -> list[str]:
    ok, out = run(["gentle-ai", "doctor"], timeout=5)
    if not ok or not out:
        return ["gentle-ai doctor failed"]
    return [line.strip() for line in out.splitlines() if line.strip().startswith("[fail]")]


def parse_review_status(raw: str) -> dict:
    """Parse and structurally validate review status output. Fail-open on mismatch."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict) or "action" not in data:
        print("gentle-ai review status: unexpected response shape", file=sys.stderr)
        return {}
    return data


def parse_validate_result(raw: str) -> dict:
    """Parse and structurally validate review validate output. Fail-open on mismatch."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict) or "allowed" not in data:
        print("gentle-ai review validate: unexpected response shape", file=sys.stderr)
        return {}
    return data


def review_status(cwd: str) -> dict:
    ok, out = run(
        ["gentle-ai", "review", "status", "--cwd", cwd,
         "--contract", "gentle-ai.review-integration/v1", "--next-transition"],
        timeout=5, cwd=cwd,
    )
    if not ok or not out:
        return {}
    return parse_review_status(out)


def review_validate(gate: str, cwd: str) -> tuple[bool, str]:
    return run(["gentle-ai", "review", "validate", "--gate", gate, "--cwd", cwd])
