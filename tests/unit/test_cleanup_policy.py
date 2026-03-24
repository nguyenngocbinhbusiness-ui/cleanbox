"""Unit tests for cleanup policy helper functions."""

from shared.constants import RECYCLE_BIN_MARKER
from ui.views.cleanup_policy import (
    format_directory_display,
    validate_directory_addition,
)


def test_format_directory_display_recycle_bin():
    assert format_directory_display(RECYCLE_BIN_MARKER) == "[Recycle Bin]"


def test_format_directory_display_regular_path():
    assert format_directory_display("C:/Temp") == "C:/Temp"


def test_validate_directory_addition_duplicate():
    ok, reason = validate_directory_addition("C:/Temp", ["C:/Temp"])
    assert ok is False
    assert reason == "duplicate"


def test_validate_directory_addition_empty():
    ok, reason = validate_directory_addition("", [])
    assert ok is False
    assert reason == "empty"


def test_validate_directory_addition_protected(monkeypatch):
    monkeypatch.setattr("ui.views.cleanup_policy.is_protected_path", lambda _: True)
    ok, reason = validate_directory_addition("C:/Windows", [])
    assert ok is False
    assert reason == "protected"
