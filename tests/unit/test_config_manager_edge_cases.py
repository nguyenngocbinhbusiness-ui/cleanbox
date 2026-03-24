"""Edge-case coverage tests for shared.config.manager.ConfigManager."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from shared.config import ConfigManager
import shared.config.manager as config_module


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_cleanup_stale_tmp_files_removed(fresh_config, temp_config_dir):
    stale_a = temp_config_dir / "old_a.tmp"
    stale_b = temp_config_dir / "old_b.tmp"
    stale_a.write_text("x", encoding="utf-8")
    stale_b.write_text("y", encoding="utf-8")

    fresh_config._cleanup_stale_tmp()

    assert not stale_a.exists()
    assert not stale_b.exists()


def test_load_recovers_from_backup_when_main_config_is_invalid(temp_config_dir, monkeypatch):
    config_file = temp_config_dir / "config.json"
    backup_file = temp_config_dir / "config.json.bak"
    config_file.write_text("{invalid json", encoding="utf-8")
    _write_json(
        backup_file,
        {
            "cleanup_directories": ["C:/Recovered"],
            "first_run_complete": True,
            "notified_drives": {"C:": "12.5"},
        },
    )

    monkeypatch.setattr(config_module, "CONFIG_DIR", temp_config_dir)
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)

    cfg = ConfigManager()

    assert "C:/Recovered" in cfg.cleanup_directories
    assert cfg.get_notified_drive_timestamps()["C:"] == 12.5
    assert cfg.is_first_run is False


def test_load_falls_back_to_defaults_when_main_and_backup_are_invalid(temp_config_dir, monkeypatch):
    config_file = temp_config_dir / "config.json"
    backup_file = temp_config_dir / "config.json.bak"
    config_file.write_text("{invalid json", encoding="utf-8")
    backup_file.write_text("{invalid json", encoding="utf-8")

    monkeypatch.setattr(config_module, "CONFIG_DIR", temp_config_dir)
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)

    cfg = ConfigManager()

    assert cfg.cleanup_directories == []
    assert cfg.is_first_run is True


def test_save_falls_back_to_direct_write_on_permission_error(fresh_config, monkeypatch):
    fresh_config._config["cleanup_directories"] = ["C:/One"]
    monkeypatch.setattr(config_module.os, "replace", MagicMock(side_effect=PermissionError("deny")))

    fresh_config.save()

    payload = json.loads(config_module.CONFIG_FILE.read_text(encoding="utf-8"))
    assert payload["cleanup_directories"] == ["C:/One"]


def test_filter_protected_paths_persists_when_removed(fresh_config, monkeypatch):
    fresh_config._config["cleanup_directories"] = ["C:/Temp", "C:/Windows"]

    monkeypatch.setattr(
        config_module,
        "filter_protected_cleanup_directories",
        lambda _: (["C:/Temp"], ["C:/Windows"]),
    )
    save_mock = MagicMock()
    monkeypatch.setattr(fresh_config, "save", save_mock)

    fresh_config._filter_protected_paths()

    assert fresh_config.cleanup_directories == ["C:/Temp"]
    save_mock.assert_called_once()


def test_add_directory_initializes_list_when_missing(fresh_config):
    fresh_config._config.pop("cleanup_directories", None)

    assert fresh_config.add_directory("C:/New") is True
    assert "C:/New" in fresh_config.cleanup_directories


def test_add_directory_blocks_protected_path(fresh_config, monkeypatch):
    monkeypatch.setattr(config_module, "is_protected_path", lambda _path: True)

    assert fresh_config.add_directory("C:/Windows") is False
    assert "C:/Windows" not in fresh_config.cleanup_directories


def test_notified_drive_timestamp_round_trip(fresh_config):
    fresh_config.add_notified_drive("D:", timestamp=123.45)

    timestamps = fresh_config.get_notified_drive_timestamps()
    assert timestamps["D:"] == pytest.approx(123.45)

    fresh_config.remove_notified_drive("D:")
    assert "D:" not in fresh_config.get_notified_drives()


def test_getters_fail_safe_when_config_get_raises(fresh_config):
    class BrokenConfig:
        def get(self, *_args, **_kwargs):
            raise RuntimeError("broken")

    fresh_config._config = BrokenConfig()

    assert fresh_config.threshold_gb == config_module.DEFAULT_THRESHOLD_GB
    assert fresh_config.polling_interval == config_module.DEFAULT_POLLING_INTERVAL_SECONDS
    assert fresh_config.auto_start_enabled is True
    assert fresh_config.cleanup_directories == []
    assert fresh_config.get_notified_drives() == []
    assert fresh_config.get_notified_drive_timestamps() == {}


def test_save_logs_error_when_write_fails(fresh_config):
    fresh_config._config["cleanup_directories"] = ["C:/One"]

    with patch("builtins.open", side_effect=IOError("disk error")), patch.object(
        config_module, "logger"
    ) as log_mock:
        fresh_config.save()

    assert log_mock.error.called
