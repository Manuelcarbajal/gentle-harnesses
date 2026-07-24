#!/usr/bin/env python3
"""
Stop hook: attempts gentle-ai review validate --gate post-apply.
- Receipt exists and matches  → systemMessage confirming allow
- Receipt missing             → silent (no review was run this session, normal)
- Scope changed / invalidated → systemMessage warning with action hint
"""
import json
import os
import subprocess


def run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 1, ""


cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

code, out = run(["gentle-ai", "review", "validate", "--gate", "post-apply", "--cwd", cwd])

if not out:
    raise SystemExit(0)

try:
    data = json.loads(out)
except (json.JSONDecodeError, ValueError):
    raise SystemExit(0)

result = data.get("result", "")
allowed = data.get("allowed", False)
reason = data.get("reason", "")
denial = data.get("context", {}).get("denial", {})
denial_code = denial.get("code", "")

if allowed:
    lineage = data.get("context", {}).get("lineage_id", "")
    tag = f" ({lineage})" if lineage else ""
    print(json.dumps({
        "systemMessage": f"✅ review gate: allow{tag} — {reason}"
    }))

elif denial_code == "receipt_missing":
    raise SystemExit(0)

else:
    action_hints = {
        "candidate-or-paths-mismatch": "scope changed — run review cycle again on current state",
        "invalidated":                 "receipt invalidated — explicit maintainer action required",
        "authority_corrupted":         "authority corrupted — run `gentle-ai review status` to diagnose",
        "receipt_missing":             "",
    }
    hint = action_hints.get(denial_code, f"code={denial_code}")
    print(json.dumps({
        "systemMessage": f"⚠️  review gate: {result} — {hint or reason}"
    }))
