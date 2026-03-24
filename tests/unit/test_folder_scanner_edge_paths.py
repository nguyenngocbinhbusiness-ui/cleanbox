"""Extra edge-path coverage for features.folder_scanner.service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from features.folder_scanner.service import FolderScanner, FolderInfo, ScanStats


def _folder(path: str = "C:/root") -> FolderInfo:
    return FolderInfo(
        path=path,
        name="root",
        size_bytes=1,
        allocated_bytes=4096,
        file_count=1,
        folder_count=0,
        last_modified="",
        children=[],
    )


def test_scan_folder_and_single_level_exception_paths():
    scanner = FolderScanner()
    with patch.object(scanner, "_scan_recursive", side_effect=RuntimeError("boom")):
        assert scanner.scan_folder("C:/x") is None
        assert scanner.scan_single_level("C:/x") is None


def test_scan_children_realtime_iter_access_error_returns_empty():
    scanner = FolderScanner()
    with patch.object(scanner, "_iter_dir_entries", side_effect=PermissionError("denied")):
        result = scanner.scan_children_realtime("C:/x", lambda _child: None)

    assert result is not None
    assert result.size_bytes == 0
    assert result.children == []


def test_scan_children_realtime_runtime_error_during_entry_scan_returns_none():
    scanner = FolderScanner()
    with (
        patch.object(scanner, "_iter_dir_entries", return_value=iter(())),
        patch.object(scanner, "_scan_realtime_entries", side_effect=RuntimeError("cancelled")),
    ):
        result = scanner.scan_children_realtime("C:/x", lambda _child: None)
    assert result is None


def test_scan_children_realtime_non_runtime_entry_error_returns_empty():
    scanner = FolderScanner()
    with (
        patch.object(scanner, "_iter_dir_entries", return_value=iter(())),
        patch.object(scanner, "_scan_realtime_entries", side_effect=ValueError("bad")),
    ):
        result = scanner.scan_children_realtime("C:/x", lambda _child: None)
    assert result is not None
    assert result.size_bytes == 0


def test_scan_children_realtime_runtime_error_during_directory_scan_returns_none():
    scanner = FolderScanner()
    fake_dir = MagicMock()
    with (
        patch.object(scanner, "_iter_dir_entries", return_value=iter(())),
        patch.object(scanner, "_scan_realtime_entries") as realtime_entries,
        patch.object(scanner, "_scan_realtime_directories", side_effect=RuntimeError("cancelled")),
    ):
        realtime_entries.side_effect = lambda _iter, dirs, *_args: dirs.append(fake_dir)
        result = scanner.scan_children_realtime("C:/x", lambda _child: None)
    assert result is None


def test_scan_realtime_entries_raises_when_cancelled():
    scanner = FolderScanner()
    with patch.object(scanner, "_cancel_flag") as cancel_flag:
        cancel_flag.is_set.return_value = True
        try:
            scanner._scan_realtime_entries(
                iter([MagicMock()]), [], [], [0], ScanStats(), MagicMock()
            )
            assert False, "Expected RuntimeError"
        except RuntimeError:
            pass


def test_scan_subtree_records_parent_skip_on_exception():
    scanner = FolderScanner()
    parent_stats = ScanStats()
    with patch.object(scanner, "_scan_recursive", side_effect=RuntimeError("boom")):
        result = scanner._scan_subtree("C:/x", parent_stats=parent_stats)
    assert result is None
    assert parent_stats.skipped_count >= 1


def test_cancel_and_is_cancelled_exception_paths():
    scanner = FolderScanner()
    scanner._cancel_flag = MagicMock()
    scanner._cancel_flag.set.side_effect = RuntimeError("boom")
    scanner.cancel()  # should not raise

    scanner._cancel_flag.is_set.side_effect = RuntimeError("boom")
    assert scanner.is_cancelled() is False


def test_scan_realtime_entries_process_exception_records_skip():
    scanner = FolderScanner()
    stats = ScanStats()
    aggregate = MagicMock()
    entry = MagicMock()
    entry.is_file.side_effect = RuntimeError("entry boom")

    scanner._scan_realtime_entries(iter([entry]), [], [], [0], stats, aggregate)
    assert stats.skipped_count >= 1
