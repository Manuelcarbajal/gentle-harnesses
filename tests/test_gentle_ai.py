import json
from unittest.mock import MagicMock, patch

import pytest

import gentle_ai


# ── parse_review_status ───────────────────────────────────────────────────────

def test_parse_review_status_valid() -> None:
    raw = json.dumps({"action": "commit", "next_transition": {"kind": "execute"}})
    result = gentle_ai.parse_review_status(raw)
    assert result["action"] == "commit"


def test_parse_review_status_missing_action_returns_empty(capsys: pytest.CaptureFixture[str]) -> None:
    raw = json.dumps({"next_transition": {"kind": "none"}})
    result = gentle_ai.parse_review_status(raw)
    assert result == {}
    assert "unexpected response shape" in capsys.readouterr().err


def test_parse_review_status_invalid_json_returns_empty() -> None:
    result = gentle_ai.parse_review_status("not-json")
    assert result == {}


def test_parse_review_status_non_dict_returns_empty(capsys: pytest.CaptureFixture[str]) -> None:
    result = gentle_ai.parse_review_status(json.dumps([1, 2, 3]))
    assert result == {}
    assert "unexpected response shape" in capsys.readouterr().err


def test_parse_review_status_empty_string_returns_empty() -> None:
    result = gentle_ai.parse_review_status("")
    assert result == {}


# ── parse_validate_result ─────────────────────────────────────────────────────

def test_parse_validate_result_allow() -> None:
    raw = json.dumps({"allowed": True, "reason": "artifacts match"})
    result = gentle_ai.parse_validate_result(raw)
    assert result["allowed"] is True


def test_parse_validate_result_deny() -> None:
    raw = json.dumps({"allowed": False, "result": "deny", "context": {"denial": {"code": "invalidated"}}})
    result = gentle_ai.parse_validate_result(raw)
    assert result["allowed"] is False
    assert result["context"]["denial"]["code"] == "invalidated"


def test_parse_validate_result_missing_allowed_returns_empty(capsys: pytest.CaptureFixture[str]) -> None:
    raw = json.dumps({"result": "deny"})
    result = gentle_ai.parse_validate_result(raw)
    assert result == {}
    assert "unexpected response shape" in capsys.readouterr().err


def test_parse_validate_result_invalid_json_returns_empty() -> None:
    result = gentle_ai.parse_validate_result("not-json")
    assert result == {}


def test_parse_validate_result_non_dict_returns_empty(capsys: pytest.CaptureFixture[str]) -> None:
    result = gentle_ai.parse_validate_result(json.dumps("a string"))
    assert result == {}
    assert "unexpected response shape" in capsys.readouterr().err


# ── review_status uses parse_review_status ────────────────────────────────────

def test_review_status_valid_response() -> None:
    payload = json.dumps({"action": "commit", "next_transition": {"kind": "none"}})
    mock_result = MagicMock(returncode=0, stdout=payload, stderr="")
    with patch("subprocess.run", return_value=mock_result):
        result = gentle_ai.review_status("/repo")
    assert result["action"] == "commit"


def test_review_status_schema_mismatch_returns_empty(capsys: pytest.CaptureFixture[str]) -> None:
    payload = json.dumps({"unrelated": "data"})
    mock_result = MagicMock(returncode=0, stdout=payload, stderr="")
    with patch("subprocess.run", return_value=mock_result):
        result = gentle_ai.review_status("/repo")
    assert result == {}
    assert "unexpected response shape" in capsys.readouterr().err


def test_review_status_command_fails_returns_empty() -> None:
    mock_result = MagicMock(returncode=1, stdout="", stderr="error")
    with patch("subprocess.run", return_value=mock_result):
        result = gentle_ai.review_status("/repo")
    assert result == {}
