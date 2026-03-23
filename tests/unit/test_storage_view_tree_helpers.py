"""Tests for storage_view_tree pure helpers and regression-safe output."""

from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem

from features.folder_scanner.service import FileEntry, FolderInfo
from ui.views.storage_view_tree import (
    COL_ALLOCATED,
    COL_FILES,
    COL_FOLDERS,
    COL_NAME,
    COL_PERCENT,
    COL_SIZE,
    NumericSortItem,
    add_file_entries,
    build_tree_item,
)
from ui.views.storage_view_tree_helpers import (
    calculate_percent,
    parse_display_int,
    summarize_direct_files,
)


def _make_folder() -> FolderInfo:
    return FolderInfo(
        path="C:/demo",
        name="demo",
        size_bytes=300,
        allocated_bytes=512,
        file_count=3,
        folder_count=1,
        last_modified="",
        children=[],
        direct_files=[
            FileEntry("a.txt", "C:/demo/a.txt", 120, 128),
            FileEntry("b.txt", "C:/demo/b.txt", 80, 128),
            FileEntry("c.txt", "C:/demo/c.txt", 100, 256),
        ],
    )


def test_parse_display_int_handles_commas_and_dash():
    assert parse_display_int("1,234") == 1234
    assert parse_display_int("-") == 0
    assert parse_display_int(" 42 ") == 42


def test_calculate_percent_matches_ui_guard():
    assert calculate_percent(25, 100) == 25.0
    assert calculate_percent(25, 0) == 0.0


def test_summarize_direct_files_preserves_counts_and_omits_tail():
    folder = _make_folder()
    summary = summarize_direct_files(folder.direct_files, 2)

    assert summary.file_count == 3
    assert summary.total_size == 300
    assert summary.total_allocated == 512
    assert [entry.name for entry in summary.shown_files] == ["a.txt", "b.txt"]
    assert summary.omitted_count == 1
    assert summary.omitted_size == 100


def test_build_tree_item_and_add_file_entries_regression_safe(qtbot):
    folder = _make_folder()
    tree = QTreeWidget()
    qtbot.addWidget(tree)
    item = build_tree_item(folder, folder.size_bytes, is_root=True)

    assert item.text(COL_NAME) == "300 Bytes   demo"
    assert item.text(COL_SIZE) == "300 Bytes"
    assert item.text(COL_ALLOCATED) == "512 Bytes"
    assert item.text(COL_FILES) == "3"
    assert item.text(COL_FOLDERS) == "1"
    assert item.text(COL_PERCENT) == "100.0 %"

    tree.addTopLevelItem(item)
    assert tree.topLevelItemCount() == 1
    assert item.childCount() == 1

    group = item.child(0)
    assert group.text(COL_NAME) == "300 Bytes   [3 Files]"
    assert group.text(COL_FILES) == "3"
    assert group.childCount() == 3


def test_add_file_entries_adds_group_to_parent_item(qtbot):
    folder = _make_folder()
    parent = QTreeWidgetItem()

    add_file_entries(parent, folder, folder.size_bytes)

    assert parent.childCount() == 1
    group = parent.child(0)
    assert group.text(COL_NAME) == "300 Bytes   [3 Files]"
    assert group.text(COL_PERCENT) == "100.0 %"


def test_numeric_sort_item_uses_display_parser_for_file_counts(qtbot):
    left = NumericSortItem()
    right = NumericSortItem()
    left.setText(COL_FILES, "1,200")
    right.setText(COL_FILES, "900")
    assert parse_display_int(left.text(COL_FILES)) > parse_display_int(right.text(COL_FILES))
