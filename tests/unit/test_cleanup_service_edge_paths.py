"""Edge-path tests for features.cleanup.service."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from features.cleanup.service import CleanupResult, CleanupService
from shared.utils import ProtectedPathError


def test_total_size_mb_exception_path():
    class BrokenSize:
        def __truediv__(self, _other):
            raise RuntimeError("boom")

    result = CleanupResult(total_size_bytes=BrokenSize())
    assert result.total_size_mb == 0.0


def test_cleanup_directory_protected_path_raises():
    service = CleanupService()
    with patch("features.cleanup.service.is_protected_path", return_value=True):
        with pytest.raises(ProtectedPathError):
            service.cleanup_directory("C:/Windows")


def test_cleanup_directory_permission_error_branch(tmp_path):
    service = CleanupService()
    item = MagicMock()
    item.is_file.return_value = True
    item.stat.return_value.st_size = 10
    item.exists.return_value = True
    item.unlink.side_effect = PermissionError("denied")

    fake_dir = MagicMock()
    fake_dir.exists.return_value = True
    fake_dir.is_dir.return_value = True
    fake_dir.iterdir.return_value = [item]

    with (
        patch("features.cleanup.service.Path", return_value=fake_dir),
        patch.object(service, "_recycle_item", return_value=False),
    ):
        result = service.cleanup_directory(str(tmp_path))

    assert any("Permission denied" in err for err in result.errors)


def test_cleanup_directory_generic_exception_branch(tmp_path):
    service = CleanupService()
    item = MagicMock()
    item.is_file.return_value = True
    item.stat.side_effect = RuntimeError("stat failed")

    fake_dir = MagicMock()
    fake_dir.exists.return_value = True
    fake_dir.is_dir.return_value = True
    fake_dir.iterdir.return_value = [item]

    with patch("features.cleanup.service.Path", return_value=fake_dir):
        result = service.cleanup_directory(str(tmp_path))

    assert any("Error:" in err for err in result.errors)


def test_empty_recycle_bin_ctypes_fallback_success():
    service = CleanupService()
    fake_bin = MagicMock()
    fake_bin.empty.side_effect = RuntimeError("winshell fail")
    fake_ctypes = MagicMock()

    with (
        patch("features.cleanup.service.winshell.recycle_bin", return_value=fake_bin),
        patch.dict(sys.modules, {"ctypes": fake_ctypes}),
    ):
        result = service.empty_recycle_bin()

    assert result.total_folders == 1
    assert result.errors == []


def test_empty_recycle_bin_ctypes_fallback_failure():
    service = CleanupService()
    fake_bin = MagicMock()
    fake_bin.empty.side_effect = RuntimeError("winshell fail")

    class BrokenCtypes:
        class windll:
            class shell32:
                @staticmethod
                def SHEmptyRecycleBinW(*_args, **_kwargs):
                    raise RuntimeError("ctypes fail")

    with (
        patch("features.cleanup.service.winshell.recycle_bin", return_value=fake_bin),
        patch.dict(sys.modules, {"ctypes": BrokenCtypes}),
    ):
        result = service.empty_recycle_bin()

    assert result.total_folders == 0
    assert result.errors


def test_cleanup_all_outer_exception_path():
    service = CleanupService()
    with (
        patch("features.cleanup.service.Path.exists", return_value=True),
        patch.object(service, "cleanup_directory", side_effect=RuntimeError("boom")),
    ):
        result = service.cleanup_all(["C:/tmp"])
    assert any("Cleanup failed" in err for err in result.errors)


def test_get_dir_size_walk_and_stat_error_paths(tmp_path):
    service = CleanupService()
    target = Path(tmp_path)

    with patch.object(Path, "rglob", side_effect=PermissionError("walk denied")):
        assert service._get_dir_size(target) == 0

    good_file = MagicMock()
    good_file.is_file.return_value = True
    good_file.stat.side_effect = OSError("stat denied")
    with patch.object(Path, "rglob", return_value=[good_file]):
        assert service._get_dir_size(target) == 0
