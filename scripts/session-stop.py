#!/usr/bin/env python3
"""
Stop hook:
1. Validates gentle-ai review gate post-apply.
2. Saves session snapshot to Engram so next session resumes with context.
"""
import json
import os
import re
import subprocess


def run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 1, ""


cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

# ── 1. Review gate ──────────────────────────────────────────────────────────

code, out = run(["gentle-ai", "review", "validate", "--gate", "post-apply", "--cwd", cwd])
gate_msg = None

if out:
    try:
        data = json.loads(out)
        allowed = data.get("allowed", False)
        reason = data.get("reason", "")
        denial_code = data.get("context", {}).get("denial", {}).get("code", "")

        if allowed:
            lineage = data.get("context", {}).get("lineage_id", "")
            tag = f" ({lineage})" if lineage else ""
            gate_msg = f"review gate: allow{tag} — {reason}"
        elif denial_code != "receipt_missing":
            hints = {
                "candidate-or-paths-mismatch": "scope changed — run review cycle again",
                "invalidated":                 "receipt invalidated — explicit maintainer action required",
                "authority_corrupted":         "run `gentle-ai review status` to diagnose",
            }
            hint = hints.get(denial_code, f"code={denial_code}")
            gate_msg = f"⚠️  review gate: {data.get('result','')} — {hint or reason}"
    except (json.JSONDecodeError, ValueError):
        pass

# ── 2. Session snapshot → Engram ────────────────────────────────────────────

def sdd_snapshot() -> str:
    _, out = run(["gentle-ai", "sdd-status"], timeout=2)
    if not out:
        return ""
    match = re.search(r"```json\s*(.*?)\s*```", out, re.DOTALL)
    if not match:
        return ""
    try:
        d = json.loads(match.group(1))
        change = d.get("changeName")
        if not change:
            return ""
        next_rec = d.get("nextRecommended", "")
        prog = d.get("taskProgress", {})
        return f"sdd:{change} next:{next_rec} tasks:{prog.get('completed',0)}/{prog.get('total',0)}"
    except Exception:
        return ""


def git_snapshot() -> str:
    _, log = run(["git", "-C", cwd, "log", "--oneline", "-3"], timeout=2)
    return log or ""


def review_snapshot() -> str:
    if gate_msg:
        return gate_msg
    _, out = run(["gentle-ai", "review", "status", "--cwd", cwd], timeout=2)
    if not out:
        return ""
    try:
        entries = json.loads(out).get("entries", [])
        if entries:
            e = entries[0]
            return f"review:{e.get('lineage_id','')} state:{e.get('state','')}"
    except Exception:
        pass
    return ""


project = os.path.basename(cwd.rstrip("/\\"))
parts = [x for x in [sdd_snapshot(), review_snapshot(), git_snapshot()] if x]

if parts:
    summary = " | ".join(parts)
    run(
        ["engram", "save", f"session-end:{project}", summary,
         "--type", "project", "--project", project],
        timeout=3
    )

# ── 3. Output ───────────────────────────────────────────────────────────────

if gate_msg and gate_msg.startswith("⚠️"):
    print(json.dumps({"systemMessage": gate_msg}))
elif gate_msg:
    print(json.dumps({"systemMessage": f"✅ {gate_msg}"}))
