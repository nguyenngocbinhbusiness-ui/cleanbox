"""Tests for shared config IO/default helper modules."""
from __future__ import annotations

import json
from pathlib import Path

from shared.config_defaults import build_default_config
from shared.config_io import cleanup_stale_tmp_files, load_json_config, save_json_config


def test_build_default_config_shape():
    cfg = build_default_config(10, 60)
    assert cfg["low_space_threshold_gb"] == 10
    assert cfg["polling_interval_seconds"] == 60
    assert cfg["cleanup_directories"] == []


def test_cleanup_stale_tmp_files_removes_tmp(tmp_path):
    stale = tmp_path / "a.tmp"
    keep = tmp_path / "b.json"
    stale.write_text("x", encoding="utf-8")
    keep.write_text("y", encoding="utf-8")

    class _Logger:
        def info(self, *_args, **_kwargs):
            return None

        def warning(self, *_args, **_kwargs):
            return None

    cleanup_stale_tmp_files(tmp_path, _Logger())
    assert not stale.exists()
    assert keep.exists()


def test_load_json_config_reads_primary_and_backup(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text('{"x": 1}', encoding="utf-8")

    class _Logger:
        def warning(self, *_args, **_kwargs):
            return None

    payload, from_backup = load_json_config(config_file, _Logger())
    assert payload == {"x": 1}
    assert from_backup is False

    config_file.write_text("{bad", encoding="utf-8")
    bak_file = config_file.with_suffix(".json.bak")
    bak_file.write_text('{"y": 2}', encoding="utf-8")
    payload, from_backup = load_json_config(config_file, _Logger())
    assert payload == {"y": 2}
    assert from_backup is True


def test_save_json_config_writes_file(tmp_path):
    config_file = tmp_path / "config.json"
    payload = {"cleanup_directories": ["D:/tmp"]}

    class _Logger:
        def info(self, *_args, **_kwargs):
            return None

        def warning(self, *_args, **_kwargs):
            return None

        def error(self, *_args, **_kwargs):
            return None

    assert save_json_config(config_file, payload, _Logger()) is True
    assert json.loads(Path(config_file).read_text(encoding="utf-8")) == payload
