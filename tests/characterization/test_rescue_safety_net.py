"""Characterization tests for rune-rescue safety net."""

from __future__ import annotations

from shared.constants import RECYCLE_BIN_MARKER
from ui.views import CleanupView
from features.folder_scanner.service import FolderScanner


def test_cleanup_view_formats_recycle_bin_marker(qapp):
    view = CleanupView()
    view.update_directories([RECYCLE_BIN_MARKER, "C:/Temp"])

    assert view._dir_list.count() == 2
    assert view._dir_list.item(0).text() == "[Recycle Bin]"
    assert view._dir_list.item(0).data(256) == RECYCLE_BIN_MARKER


def test_config_manager_normalizes_notified_drives_dict(fresh_config):
    fresh_config._config["notified_drives"] = {"C:": "123.5", "D:": "bad"}
    fresh_config._normalize_notified_drives()

    assert fresh_config._config["notified_drives"]["C:"] == 123.5
    assert fresh_config._config["notified_drives"]["D:"] == 0.0


def test_config_manager_normalizes_notified_drives_list(fresh_config):
    fresh_config._config["notified_drives"] = ["C:", "D:"]
    fresh_config._normalize_notified_drives()

    assert fresh_config._config["notified_drives"] == {"C:": 0.0, "D:": 0.0}


def test_folder_scanner_worker_env_is_clamped(monkeypatch):
    monkeypatch.setenv("CLEANBOX_SCANNER_WORKERS", "99")
    scanner = FolderScanner()
    assert scanner._parallel_workers == 8


def test_folder_scanner_skip_reason_contract():
    assert FolderScanner._skip_reason(PermissionError("x")) == "permission_denied"
    assert FolderScanner._skip_reason(OSError("x")) == "os_error"
    assert FolderScanner._skip_reason(RuntimeError("x")) == "entry_processing_error"
