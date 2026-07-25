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


# ── git_snapshot ──────────────────────────────────────────────────────────────

def test_git_snapshot_returns_log() -> None:
    with patch.object(stop, "run", return_value=(0, "abc1234 feat: add thing\ndef5678 fix: bug")):
        out = stop.git_snapshot("/repo")
    assert "abc1234" in out


def test_git_snapshot_empty_on_failure() -> None:
    with patch.object(stop, "run", return_value=(1, "")):
        out = stop.git_snapshot("/repo")
    assert out == ""


# ── sdd_snapshot ──────────────────────────────────────────────────────────────

def test_sdd_snapshot_active_change() -> None:
    output = '```json\n{"changeName":"my-feature","nextRecommended":"apply","taskProgress":{"completed":2,"total":5}}\n```'
    with patch.object(stop, "run", return_value=(0, output)):
        out = stop.sdd_snapshot("/repo")
    assert "my-feature" in out
    assert "2/5" in out


def test_sdd_snapshot_no_change() -> None:
    output = '```json\n{"changeName":null}\n```'
    with patch.object(stop, "run", return_value=(0, output)):
        out = stop.sdd_snapshot("/repo")
    assert out == ""


def test_sdd_snapshot_no_output() -> None:
    with patch.object(stop, "run", return_value=(0, "")):
        out = stop.sdd_snapshot("/repo")
    assert out == ""


# ── review_snapshot ───────────────────────────────────────────────────────────

def test_review_snapshot_uses_gate_msg_when_present() -> None:
    out = stop.review_snapshot("/repo", gate_msg="review gate: allow")
    assert out == "review gate: allow"


def test_review_snapshot_falls_back_to_status() -> None:
    payload = json.dumps({"entries": [{"lineage_id": "review-xyz", "state": "approved"}]})
    with patch.object(stop, "run", return_value=(0, payload)):
        out = stop.review_snapshot("/repo", gate_msg="")
    assert "review-xyz" in out
    assert "approved" in out


def test_review_snapshot_empty_on_failure() -> None:
    with patch.object(stop, "run", return_value=(1, "")):
        out = stop.review_snapshot("/repo", gate_msg="")
    assert out == ""


# ── main output ───────────────────────────────────────────────────────────────

def test_main_warning_output(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")
    monkeypatch.setattr(stop, "build_gate_msg", lambda cwd: "⚠️  review gate: deny — scope changed")
    monkeypatch.setattr(stop, "sdd_snapshot", lambda cwd: "")
    monkeypatch.setattr(stop, "git_snapshot", lambda cwd: "")
    monkeypatch.setattr(stop, "review_snapshot", lambda cwd, gate_msg: gate_msg or "")
    monkeypatch.setattr(stop, "run", lambda cmd, timeout=10: (0, ""))

    stop.main()

    out = json.loads(capsys.readouterr().out)
    assert "systemMessage" in out
    assert "⚠️" in out["systemMessage"]


def test_main_allow_output(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")
    monkeypatch.setattr(stop, "build_gate_msg", lambda cwd: "review gate: allow (review-abc) — match")
    monkeypatch.setattr(stop, "sdd_snapshot", lambda cwd: "")
    monkeypatch.setattr(stop, "git_snapshot", lambda cwd: "abc1234 feat: done")
    monkeypatch.setattr(stop, "review_snapshot", lambda cwd, gate_msg: gate_msg or "")
    monkeypatch.setattr(stop, "run", lambda cmd, timeout=10: (0, ""))

    stop.main()

    out = json.loads(capsys.readouterr().out)
    assert "systemMessage" in out
    assert "✅" in out["systemMessage"]


def test_main_no_gate_msg_no_output(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")
    monkeypatch.setattr(stop, "build_gate_msg", lambda cwd: "")
    monkeypatch.setattr(stop, "sdd_snapshot", lambda cwd: "")
    monkeypatch.setattr(stop, "git_snapshot", lambda cwd: "")
    monkeypatch.setattr(stop, "review_snapshot", lambda cwd, gate_msg: "")
    monkeypatch.setattr(stop, "run", lambda cmd, timeout=10: (0, ""))

    stop.main()

    assert capsys.readouterr().out.strip() == ""
