"""Unit tests for storage view status helpers."""

from types import SimpleNamespace

from features.folder_scanner.service import FolderInfo
from ui.views.storage_view_status import build_scan_complete_text


def _make_result() -> FolderInfo:
    return FolderInfo(
        path="C:/x",
        name="x",
        size_bytes=1024,
        allocated_bytes=4096,
        file_count=3,
        folder_count=1,
        last_modified="",
        children=[],
    )


def test_build_scan_complete_text_without_stats():
    text = build_scan_complete_text(_make_result())
    assert text.startswith("Scan complete:")
    assert "files" in text


def test_build_scan_complete_text_with_stats():
    result = _make_result()
    result.scan_stats = SimpleNamespace(
        scanned_files=3,
        scanned_dirs=1,
        skipped_count=2,
        skipped_reasons={"permission_denied": 2},
    )
    text = build_scan_complete_text(result)
    assert "\n" in text
    assert "scanned_files=3" in text
    assert "scanned_dirs=1" in text
    assert "skipped=2" in text
