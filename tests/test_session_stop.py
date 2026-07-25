import json
from unittest.mock import patch

import pytest

from conftest import load_script

stop = load_script("session-stop")


# ── build_gate_msg ────────────────────────────────────────────────────────────

def test_build_gate_msg_allow() -> None:
    payload = json.dumps({
        "allowed": True, "reason": "artifacts match",
        "context": {"lineage_id": "review-abc123", "denial": {}}
    })
    with patch.object(stop, "run", return_value=(0, payload)):
        msg = stop.build_gate_msg("/repo")
    assert msg
    assert "allow" in msg
    assert "review-abc123" in msg


def test_build_gate_msg_scope_changed() -> None:
    payload = json.dumps({
        "allowed": False, "result": "deny", "reason": "mismatch",
        "context": {"denial": {"code": "candidate-or-paths-mismatch"}}
    })
    with patch.object(stop, "run", return_value=(0, payload)):
        msg = stop.build_gate_msg("/repo")
    assert msg
    assert "scope changed" in msg
    assert "⚠️" in msg


def test_build_gate_msg_receipt_missing_returns_empty() -> None:
    payload = json.dumps({
        "allowed": False, "result": "deny", "reason": "",
        "context": {"denial": {"code": "receipt_missing"}}
    })
    with patch.object(stop, "run", return_value=(0, payload)):
        msg = stop.build_gate_msg("/repo")
    assert msg == ""


def test_build_gate_msg_empty_output() -> None:
    with patch.object(stop, "run", return_value=(1, "")):
        msg = stop.build_gate_msg("/repo")
    assert msg == ""


def test_build_gate_msg_invalid_json() -> None:
    with patch.object(stop, "run", return_value=(0, "not-json")):
        msg = stop.build_gate_msg("/repo")
    assert msg == ""


# ── main output ───────────────────────────────────────────────────────────────

def test_main_warning_output(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")
    monkeypatch.setattr(stop, "build_gate_msg", lambda cwd: "⚠️  review gate: deny — scope changed")

    stop.main()

    out = json.loads(capsys.readouterr().out)
    assert "systemMessage" in out
    assert "⚠️" in out["systemMessage"]


def test_main_allow_output(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")
    monkeypatch.setattr(stop, "build_gate_msg", lambda cwd: "review gate: allow (review-abc) — match")

    stop.main()

    out = json.loads(capsys.readouterr().out)
    assert "systemMessage" in out
    assert "✅" in out["systemMessage"]


def test_main_no_gate_msg_no_output(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")
    monkeypatch.setattr(stop, "build_gate_msg", lambda cwd: "")

    stop.main()

    assert capsys.readouterr().out.strip() == ""
