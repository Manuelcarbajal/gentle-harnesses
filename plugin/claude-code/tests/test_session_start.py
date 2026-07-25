import json
from unittest.mock import MagicMock, patch

import pytest

from conftest import load_script

ss = load_script("session-start")


# ── check_version ────────────────────────────────────────────────────────────

def test_check_version_ok() -> None:
    result = MagicMock(returncode=0, stdout="gentle-ai 2.1.11\n", stderr="")
    with patch("subprocess.run", return_value=result):
        version, err = ss.check_version()
    assert version == "2.1.11"
    assert err == ""


def test_check_version_not_found() -> None:
    with patch("subprocess.run", side_effect=FileNotFoundError):
        version, err = ss.check_version()
    assert version == ""
    assert "not found" in err


def test_check_version_timeout() -> None:
    import subprocess
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("gentle-ai", 3)):
        version, err = ss.check_version()
    assert version == ""


# ── check_doctor ─────────────────────────────────────────────────────────────

def test_check_doctor_no_failures() -> None:
    result = MagicMock(returncode=0, stdout="[pass] codegraph\n[pass] engram\n", stderr="")
    with patch("subprocess.run", return_value=result):
        failures = ss.check_doctor()
    assert failures == []


def test_check_doctor_with_failures() -> None:
    result = MagicMock(returncode=0, stdout="[pass] codegraph\n[fail] engram not found\n", stderr="")
    with patch("subprocess.run", return_value=result):
        failures = ss.check_doctor()
    assert failures == ["[fail] engram not found"]


def test_check_doctor_command_fails() -> None:
    result = MagicMock(returncode=1, stdout="", stderr="error")
    with patch("subprocess.run", return_value=result):
        failures = ss.check_doctor()
    assert failures == ["gentle-ai doctor failed"]


# ── check_codegraph_binary ───────────────────────────────────────────────────

def test_check_codegraph_binary_present() -> None:
    with patch("shutil.which", return_value="/usr/bin/codegraph"):
        err = ss.check_codegraph_binary()
    assert err == ""


def test_check_codegraph_binary_missing() -> None:
    with patch("shutil.which", return_value=None):
        err = ss.check_codegraph_binary()
    assert "codegraph" in err
    assert "not in PATH" in err


# ── main output ──────────────────────────────────────────────────────────────

def test_main_healthy_output(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "")
    monkeypatch.setattr(ss, "check_version", lambda: ("2.1.11", ""))
    monkeypatch.setattr(ss, "check_doctor", lambda: [])
    monkeypatch.setattr(ss, "check_codegraph_binary", lambda: "")

    ss.main()

    out = json.loads(capsys.readouterr().out)
    assert "hookSpecificOutput" in out
    assert "ecosystem healthy" in out["hookSpecificOutput"]["additionalContext"]


def test_main_issues_output(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "")
    monkeypatch.setattr(ss, "check_version", lambda: ("", "gentle-ai not found"))
    monkeypatch.setattr(ss, "check_doctor", lambda: [])
    monkeypatch.setattr(ss, "check_codegraph_binary", lambda: "")

    ss.main()

    out = json.loads(capsys.readouterr().out)
    assert "systemMessage" in out
    assert "gentle-ai binary" in out["systemMessage"]


