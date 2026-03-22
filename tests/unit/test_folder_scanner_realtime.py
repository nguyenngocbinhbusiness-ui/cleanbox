from unittest.mock import MagicMock, patch

from features.folder_scanner.scan_helpers import parse_last_modified
from features.folder_scanner.service import FolderInfo, FolderScanner, ScanStats


class TestFolderScannerRealtime:
    def test_parse_last_modified_returns_none_for_invalid_value(self):
        assert parse_last_modified("") is None
        assert parse_last_modified("not-a-date") is None

    def test_parse_last_modified_returns_none_when_timestamp_conversion_fails(self):
        fake_datetime = MagicMock()
        fake_datetime.timestamp.side_effect = OSError("Invalid argument")

        with patch("features.folder_scanner.scan_helpers.datetime.datetime") as mock_datetime:
            mock_datetime.strptime.return_value = fake_datetime
            assert parse_last_modified("01/01/1970") is None

    def test_realtime_scan_records_mtime_parse_error(self):
        scanner = FolderScanner()

        dir_entry = MagicMock()
        dir_entry.is_file.return_value = False
        dir_entry.is_dir.return_value = True
        dir_entry.path = "C:/Root/Child"

        child = FolderInfo(
            path="C:/Root/Child",
            name="Child",
            size_bytes=10,
            allocated_bytes=16,
            file_count=1,
            folder_count=0,
            last_modified="bad-date",
            children=[],
            scan_stats=ScanStats(scanned_entries=1),
        )

        with patch.object(scanner, "_iter_dir_entries", return_value=iter([dir_entry])), \
             patch.object(scanner, "_scan_subtree", return_value=child), \
             patch("features.folder_scanner.service._get_cluster_size", return_value=4096):
            callback_results = []
            result = scanner.scan_children_realtime("C:/Root", callback_results.append)

        assert result is not None
        assert result.scan_stats.skipped_reasons["mtime_parse_error"] == 1
        assert callback_results == [child]

    def test_scan_subtree_does_not_double_merge_parent_stats(self):
        scanner = FolderScanner()
        parent_stats = ScanStats()
        child = FolderInfo(
            path="C:/Root/Child",
            name="Child",
            size_bytes=10,
            allocated_bytes=16,
            file_count=1,
            folder_count=0,
            last_modified="01/01/2026",
            children=[],
            scan_stats=ScanStats(scanned_entries=3, skipped_count=1, skipped_reasons={"os_error": 1}),
        )

        with patch.object(scanner, "_scan_recursive", return_value=child):
            result = scanner._scan_subtree("C:/Root/Child", parent_stats=parent_stats)

        assert result is child
        assert parent_stats.scanned_entries == 0
        assert parent_stats.skipped_count == 0
