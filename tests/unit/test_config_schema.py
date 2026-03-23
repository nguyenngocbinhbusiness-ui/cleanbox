"""Unit tests for shared.config.schema helpers."""

from shared.config.schema import (
    filter_protected_cleanup_directories,
    normalize_notified_drives,
)


def test_normalize_notified_drives_dict_with_bad_values():
    normalized = normalize_notified_drives({"C:": "12.5", "D:": "bad", 1: 4})
    assert normalized == {"C:": 12.5, "D:": 0.0}


def test_normalize_notified_drives_list():
    normalized = normalize_notified_drives(["C:", "D:", 1])
    assert normalized == {"C:": 0.0, "D:": 0.0}


def test_filter_protected_cleanup_directories(monkeypatch):
    monkeypatch.setattr("shared.config.schema.is_protected_path", lambda p: p == "C:/Windows")
    filtered, removed = filter_protected_cleanup_directories(
        ["C:/Temp", "C:/Windows", "D:/Downloads"]
    )
    assert filtered == ["C:/Temp", "D:/Downloads"]
    assert removed == ["C:/Windows"]


def test_filter_protected_cleanup_directories_non_list():
    filtered, removed = filter_protected_cleanup_directories("not-a-list")
    assert filtered == []
    assert removed == []
