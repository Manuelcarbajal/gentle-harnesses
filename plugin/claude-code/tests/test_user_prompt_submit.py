import json
import pathlib
from unittest.mock import MagicMock, patch

import pytest

from conftest import load_script

ups = load_script("user-prompt-submit")


# ── read_skill_registry ───────────────────────────────────────────────────────

def test_read_skill_registry_present(tmp_path: pathlib.Path) -> None:
    atl = tmp_path / ".atl"
    atl.mkdir()
    (atl / "skill-registry.md").write_text("## Skills\n- sdd-explore", encoding="utf-8")
    out = ups.read_skill_registry(str(tmp_path))
    assert "sdd-explore" in out


def test_read_skill_registry_missing(tmp_path: pathlib.Path) -> None:
    out = ups.read_skill_registry(str(tmp_path))
    assert out == ""


# ── get_review_status ─────────────────────────────────────────────────────────

def test_get_review_status_pending() -> None:
    payload = json.dumps({"action": "start review", "next_transition": {"kind": "execute", "execute": {"operation": "review.start"}}})
    result = MagicMock(returncode=0, stdout=payload, stderr="")
    with patch("subprocess.run", return_value=result):
        out = ups.get_review_status("/repo")
    assert "review.start" in out


def test_get_review_status_no_pending() -> None:
    payload = json.dumps({"action": "commit", "next_transition": {"kind": "execute", "execute": {"operation": "pre-commit"}}})
    result = MagicMock(returncode=0, stdout=payload, stderr="")
    with patch("subprocess.run", return_value=result):
        out = ups.get_review_status("/repo")
    assert "pre-commit" in out


def test_get_review_status_command_fails() -> None:
    result = MagicMock(returncode=1, stdout="", stderr="error")
    with patch("subprocess.run", return_value=result):
        out = ups.get_review_status("/repo")
    assert out == ""


def test_get_review_status_not_found_failopen() -> None:
    with patch("subprocess.run", side_effect=FileNotFoundError):
        out = ups.get_review_status("/repo")
    assert out == ""


# ── main output ───────────────────────────────────────────────────────────────

def test_main_review_pending_outputs_system_message(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    import sys
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")
    monkeypatch.setattr(ups, "read_skill_registry", lambda cwd: "")
    monkeypatch.setattr(ups, "get_review_status", lambda cwd: "action=start next=review.start")

    with patch.object(sys, "exit"):
        ups.main()

    out = json.loads(capsys.readouterr().out)
    assert "systemMessage" in out
    assert "REVIEW REQUIRED" in out["systemMessage"]


def test_main_injects_skill_registry(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")
    monkeypatch.setattr(ups, "read_skill_registry", lambda cwd: "## Skills\n- sdd-apply")
    monkeypatch.setattr(ups, "get_review_status", lambda cwd: "action=commit next=pre-commit")

    ups.main()

    out = json.loads(capsys.readouterr().out)
    assert "hookSpecificOutput" in out
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "Skill Registry" in ctx
    assert "sdd-apply" in ctx


def test_main_no_context_exits_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")
    monkeypatch.setattr(ups, "read_skill_registry", lambda cwd: "")
    monkeypatch.setattr(ups, "get_review_status", lambda cwd: "")

    with patch.object(sys, "exit") as mock_exit:
        ups.main()

    mock_exit.assert_called_once_with(0)
