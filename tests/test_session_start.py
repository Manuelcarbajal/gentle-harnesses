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


# ── load_session_snapshot ────────────────────────────────────────────────────

def test_load_session_snapshot_no_engram() -> None:
    with patch("shutil.which", return_value=None):
        result = ss.load_session_snapshot("/some/project")
    assert result == ""


def test_load_session_snapshot_empty_cwd() -> None:
    result = ss.load_session_snapshot("")
    assert result == ""


def test_load_session_snapshot_json_list() -> None:
    payload = json.dumps([{"content": "last session summary"}])
    result = MagicMock(returncode=0, stdout=payload, stderr="")
    with patch("shutil.which", return_value="/usr/bin/engram"), \
         patch("subprocess.run", return_value=result):
        out = ss.load_session_snapshot("/home/user/myproject")
    assert out == "last session summary"


def test_load_session_snapshot_json_dict_results() -> None:
    payload = json.dumps({"results": [{"content": "summary text"}]})
    result = MagicMock(returncode=0, stdout=payload, stderr="")
    with patch("shutil.which", return_value="/usr/bin/engram"), \
         patch("subprocess.run", return_value=result):
        out = ss.load_session_snapshot("/home/user/myproject")
    assert out == "summary text"


def test_load_session_snapshot_plain_text_fallback() -> None:
    result = MagicMock(returncode=0, stdout="plain text snapshot", stderr="")
    with patch("shutil.which", return_value="/usr/bin/engram"), \
         patch("subprocess.run", return_value=result):
        out = ss.load_session_snapshot("/home/user/myproject")
    assert out == "plain text snapshot"


def test_load_session_snapshot_caps_at_2000() -> None:
    long_content = "x" * 3000
    payload = json.dumps([{"content": long_content}])
    result = MagicMock(returncode=0, stdout=payload, stderr="")
    with patch("shutil.which", return_value="/usr/bin/engram"), \
         patch("subprocess.run", return_value=result):
        out = ss.load_session_snapshot("/home/user/myproject")
    assert len(out) == 2000


def test_load_session_snapshot_timeout_failopen() -> None:
    import subprocess
    with patch("shutil.which", return_value="/usr/bin/engram"), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired("engram", 2)):
        out = ss.load_session_snapshot("/home/user/myproject")
    assert out == ""


def test_load_session_snapshot_not_found_failopen() -> None:
    with patch("shutil.which", return_value="/usr/bin/engram"), \
         patch("subprocess.run", side_effect=FileNotFoundError):
        out = ss.load_session_snapshot("/home/user/myproject")
    assert out == ""


# ── main output ──────────────────────────────────────────────────────────────

def test_main_healthy_output(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "")
    monkeypatch.setattr(ss, "check_version", lambda: ("2.1.11", ""))
    monkeypatch.setattr(ss, "check_doctor", lambda: [])
    monkeypatch.setattr(ss, "check_codegraph_binary", lambda: "")
    monkeypatch.setattr(ss, "check_codegraph_mcp", lambda: "")
    monkeypatch.setattr(ss, "ensure_gga", lambda cwd: "")
    monkeypatch.setattr(ss, "load_session_snapshot", lambda cwd: "")

    ss.main()

    out = json.loads(capsys.readouterr().out)
    assert "hookSpecificOutput" in out
    assert "ecosystem healthy" in out["hookSpecificOutput"]["additionalContext"]


def test_main_issues_output(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "")
    monkeypatch.setattr(ss, "check_version", lambda: ("", "gentle-ai not found"))
    monkeypatch.setattr(ss, "check_doctor", lambda: [])
    monkeypatch.setattr(ss, "check_codegraph_binary", lambda: "")
    monkeypatch.setattr(ss, "check_codegraph_mcp", lambda: "")
    monkeypatch.setattr(ss, "ensure_gga", lambda cwd: "")
    monkeypatch.setattr(ss, "load_session_snapshot", lambda cwd: "")

    ss.main()

    out = json.loads(capsys.readouterr().out)
    assert "systemMessage" in out
    assert "gentle-ai binary" in out["systemMessage"]


def test_main_injects_snapshot(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/home/user/myproject")
    monkeypatch.setattr(ss, "check_version", lambda: ("2.1.11", ""))
    monkeypatch.setattr(ss, "check_doctor", lambda: [])
    monkeypatch.setattr(ss, "check_codegraph_binary", lambda: "")
    monkeypatch.setattr(ss, "check_codegraph_mcp", lambda: "")
    monkeypatch.setattr(ss, "ensure_gga", lambda cwd: "")
    monkeypatch.setattr(ss, "load_session_snapshot", lambda cwd: "previous session context")

    ss.main()

    out = json.loads(capsys.readouterr().out)
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "Last session" in ctx
    assert "previous session context" in ctx
