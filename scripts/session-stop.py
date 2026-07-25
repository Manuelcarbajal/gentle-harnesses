#!/usr/bin/env python3
"""
Stop hook: validates gentle-ai review gate post-apply.
"""
from gentle_ai import run, parse_validate_result
import json
import os

DENIAL_HINTS = {
    "candidate-or-paths-mismatch": "scope changed — run review cycle again",
    "invalidated":                 "receipt invalidated — explicit maintainer action required",
    "authority_corrupted":         "run `gentle-ai review status` to diagnose",
}


def build_gate_msg(cwd: str) -> str:
    _, out = run(["gentle-ai", "review", "validate", "--gate", "post-apply", "--cwd", cwd])
    if not out:
        return ""
    data = parse_validate_result(out)
    if not data:
        return ""
    allowed = data.get("allowed", False)
    reason = data.get("reason", "")
    denial_code = data.get("context", {}).get("denial", {}).get("code", "")
    if allowed:
        lineage = data.get("context", {}).get("lineage_id", "")
        tag = f" ({lineage})" if lineage else ""
        return f"review gate: allow{tag} — {reason}"
    if denial_code != "receipt_missing":
        hint = DENIAL_HINTS.get(denial_code, f"code={denial_code}")
        return f"⚠️  review gate: {data.get('result','')} — {hint or reason}"
    return ""


def main() -> None:
    cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    gate_msg = build_gate_msg(cwd)

    if gate_msg and gate_msg.startswith("⚠️"):
        print(json.dumps({"systemMessage": gate_msg}))
    elif gate_msg:
        print(json.dumps({"systemMessage": f"✅ {gate_msg}"}))


if __name__ == "__main__":
    main()
