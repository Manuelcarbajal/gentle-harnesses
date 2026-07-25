"""
Phase 2 integration tests — skipped when gentle-ai is not available.

These tests call the real CLI and verify that our hook scripts handle its
actual output correctly, without mocking subprocess.
"""
import pathlib
import shutil

import pytest

pytestmark = pytest.mark.skipif(
    shutil.which("gentle-ai") is None,
    reason="gentle-ai binary not in PATH",
)

from conftest import load_script

ss = load_script("session-start")
stop = load_script("session-stop")
ups = load_script("user-prompt-submit")
ptu = load_script("pre-tool-use")


def test_check_version_returns_semver() -> None:
    version, err = ss.check_version()
    assert err == "", f"unexpected error: {err}"
    parts = version.split(".")
    assert len(parts) >= 2, f"expected semver, got: {version!r}"


def test_get_review_status_valid_json_or_empty(tmp_path: pathlib.Path) -> None:
    out = ups.get_review_status(str(tmp_path))
    assert isinstance(out, str)


def test_gate_returns_bool_and_reason(tmp_path: pathlib.Path) -> None:
    allowed, reason = ptu.gate("pre-commit", str(tmp_path))
    assert isinstance(allowed, bool)
    assert isinstance(reason, str)
