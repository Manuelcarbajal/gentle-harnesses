import json
from unittest.mock import MagicMock, patch

import pytest

from conftest import load_script

ptu = load_script("pre-tool-use")


# ── gate() ───────────────────────────────────────────────────────────────────

def test_gate_allow() -> None:
    result = MagicMock(returncode=0, stdout="", stderr="")
    with patch("subprocess.run", return_value=result):
        allowed, reason = ptu.gate("pre-commit", "/some/repo")
    assert allowed is True
    assert reason == ""


def test_gate_deny_with_reason() -> None:
    payload = json.dumps({"reason": "scope changed"})
    result = MagicMock(returncode=1, stdout=payload, stderr="")
    with patch("subprocess.run", return_value=result):
        allowed, reason = ptu.gate("pre-commit", "/some/repo")
    assert allowed is False
    assert "scope changed" in reason


def test_gate_deny_empty_stdout() -> None:
    result = MagicMock(returncode=1, stdout="", stderr="")
    with patch("subprocess.run", return_value=result):
        allowed, reason = ptu.gate("pre-commit", "/some/repo")
    assert allowed is False
    assert reason == "receipt missing or invalidated"


def test_gate_timeout_failopen() -> None:
    import subprocess
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("gentle-ai", 4)):
        allowed, reason = ptu.gate("pre-commit", "/some/repo")
    assert allowed is True


def test_gate_not_found_failopen() -> None:
    with patch("subprocess.run", side_effect=FileNotFoundError):
        allowed, reason = ptu.gate("pre-commit", "/some/repo")
    assert allowed is True


# ── command regex matching ────────────────────────────────────────────────────

def test_main_non_bash_tool_exits_0(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "Read")
    monkeypatch.setenv("CLAUDE_TOOL_INPUT", "{}")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")
    with patch.object(sys, "exit") as mock_exit:
        ptu.main()
    mock_exit.assert_called_once_with(0)


def test_main_git_commit_blocked(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import sys
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "Bash")
    monkeypatch.setenv("CLAUDE_TOOL_INPUT", json.dumps({"command": "git commit -m test"}))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")
    monkeypatch.setattr(ptu, "gate", lambda name, cwd: (False, "receipt missing"))

    with patch.object(sys, "exit") as mock_exit:
        ptu.main()

    captured = capsys.readouterr().out.strip()
    output = json.loads(captured)
    assert output["decision"] == "block"
    assert "review gate denied" in output["reason"]
    mock_exit.assert_called_once_with(2)


def test_main_git_push_blocked(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import sys
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "Bash")
    monkeypatch.setenv("CLAUDE_TOOL_INPUT", json.dumps({"command": "git push origin main"}))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")
    monkeypatch.setattr(ptu, "gate", lambda name, cwd: (False, "no receipt"))

    with patch.object(sys, "exit") as mock_exit:
        ptu.main()

    captured = capsys.readouterr().out.strip()
    output = json.loads(captured)
    assert output["decision"] == "block"
    mock_exit.assert_called_once_with(2)


def test_main_git_commit_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "Bash")
    monkeypatch.setenv("CLAUDE_TOOL_INPUT", json.dumps({"command": "git commit -m test"}))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")
    monkeypatch.setattr(ptu, "gate", lambda name, cwd: (True, ""))

    with patch.object(sys, "exit") as mock_exit:
        ptu.main()

    mock_exit.assert_called_once_with(0)


def test_main_other_bash_command_exits_0(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "Bash")
    monkeypatch.setenv("CLAUDE_TOOL_INPUT", json.dumps({"command": "npm install"}))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")

    with patch.object(sys, "exit") as mock_exit:
        ptu.main()

    mock_exit.assert_called_once_with(0)


def test_main_chained_commit_blocked(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import sys
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "Bash")
    monkeypatch.setenv("CLAUDE_TOOL_INPUT", json.dumps({"command": "npm test && git commit -m ok"}))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")
    monkeypatch.setattr(ptu, "gate", lambda name, cwd: (False, "no receipt"))

    with patch.object(sys, "exit") as mock_exit:
        ptu.main()

    mock_exit.assert_called_once_with(2)


def test_main_invalid_tool_input_exits_0(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    monkeypatch.setenv("CLAUDE_TOOL_NAME", "Bash")
    monkeypatch.setenv("CLAUDE_TOOL_INPUT", "not-json")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")

    with patch.object(sys, "exit") as mock_exit:
        ptu.main()

    mock_exit.assert_called_once_with(0)
