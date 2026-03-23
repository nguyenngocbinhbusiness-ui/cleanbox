"""Tests for storage_view_realtime_finish helpers."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTreeWidgetItem

from features.folder_scanner.service import FileEntry, FolderInfo
from ui.views.storage_view_realtime_finish import (
    cache_scan_result,
    update_child_percentages,
    update_root_item_from_result,
)
from ui.views.storage_view_tree import (
    COL_FILES,
    COL_FOLDERS,
    COL_NAME,
    COL_PERCENT,
    COL_SIZE,
    ROLE_PERCENT_BAR,
)


def _make_result() -> FolderInfo:
    return FolderInfo(
        path="C:/demo",
        name="demo",
        size_bytes=200,
        allocated_bytes=256,
        file_count=2,
        folder_count=1,
        last_modified="",
        children=[],
        direct_files=[
            FileEntry("a.txt", "C:/demo/a.txt", 120, 128),
            FileEntry("b.txt", "C:/demo/b.txt", 80, 128),
        ],
    )


def test_update_root_item_from_result_sets_expected_fields(qtbot):
    result = _make_result()
    root = QTreeWidgetItem()
    root.setData(COL_NAME, Qt.ItemDataRole.UserRole, "C:/demo")

    update_root_item_from_result(root, result)

    assert root.text(COL_NAME) == "200 Bytes   C:/demo"
    assert root.text(COL_SIZE) == "200 Bytes"
    assert root.text(COL_FILES) == "2"
    assert root.text(COL_FOLDERS) == "1"
    assert root.text(COL_PERCENT) == "100.0 %"
    assert root.data(COL_SIZE, Qt.ItemDataRole.UserRole) == 200


def test_update_child_percentages_applies_percent_data(qtbot):
    root = QTreeWidgetItem()
    child = QTreeWidgetItem()
    child.setData(COL_SIZE, Qt.ItemDataRole.UserRole, 50)
    root.addChild(child)

    update_child_percentages(root, parent_size=200)

    assert child.text(COL_PERCENT) == "25.0 %"
    assert child.data(COL_PERCENT, Qt.ItemDataRole.UserRole) == 25.0
    assert child.data(COL_NAME, ROLE_PERCENT_BAR) == 25.0


def test_cache_scan_result_bounds_size_and_writes_current_path():
    result = _make_result()
    scan_cache = {f"path-{i}": result for i in range(20)}

    cache_scan_result(scan_cache, "new-path", result, max_entries=20)

    assert len(scan_cache) == 20
    assert "path-0" not in scan_cache
    assert "new-path" in scan_cache


def test_cache_scan_result_ignores_empty_path():
    result = _make_result()
    scan_cache = {"path-1": result}

    cache_scan_result(scan_cache, None, result, max_entries=20)

    assert list(scan_cache.keys()) == ["path-1"]
