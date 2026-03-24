"""Helpers for StorageView realtime scan completion updates."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTreeWidgetItem

from features.folder_scanner import FolderInfo
from ui.views.storage_view_tree import (
    COL_ALLOCATED,
    COL_FILES,
    COL_FOLDERS,
    COL_NAME,
    COL_PERCENT,
    COL_SIZE,
    ROLE_PERCENT_BAR,
)
from features.folder_scanner import format_size


def update_root_item_from_result(
    root_item: QTreeWidgetItem,
    result: FolderInfo,
) -> None:
    """Apply final scan totals to root item fields."""
    root_path = root_item.data(COL_NAME, Qt.ItemDataRole.UserRole) or ""
    root_item.setText(COL_NAME, f"{result.size_formatted()}   {root_path}")
    root_item.setText(COL_SIZE, result.size_formatted())
    root_item.setText(COL_ALLOCATED, result.allocated_formatted())
    root_item.setText(
        COL_FILES,
        f"{result.file_count:,}" if result.file_count else "-",
    )
    root_item.setText(
        COL_FOLDERS,
        f"{result.folder_count:,}" if result.folder_count else "-",
    )
    root_item.setText(COL_PERCENT, "100.0 %")
    root_item.setData(COL_SIZE, Qt.ItemDataRole.UserRole, result.size_bytes)


def update_child_percentages(
    root_item: QTreeWidgetItem,
    parent_size: int,
) -> None:
    """Recalculate child percentages based on scanned parent size."""
    for i in range(root_item.childCount()):
        child_item = root_item.child(i)
        if child_item is None:
            continue
        child_size = child_item.data(COL_SIZE, Qt.ItemDataRole.UserRole)
        if child_size is None or parent_size <= 0:
            continue
        percent = (child_size / parent_size) * 100
        child_item.setText(COL_PERCENT, f"{percent:.1f} %")
        child_item.setData(COL_PERCENT, Qt.ItemDataRole.UserRole, percent)
        child_item.setData(COL_NAME, ROLE_PERCENT_BAR, percent)


def cache_scan_result(
    scan_cache: dict[str, FolderInfo],
    current_scan_path: Optional[str],
    result: FolderInfo,
    max_entries: int = 20,
) -> None:
    """Store completed scan result with bounded cache size."""
    if not current_scan_path:
        return
    if len(scan_cache) >= max_entries:
        oldest_key = next(iter(scan_cache))
        del scan_cache[oldest_key]
    scan_cache[current_scan_path] = result


def update_root_item_from_accumulators(
    root_item: QTreeWidgetItem,
    size_bytes: int,
    allocated_bytes: int,
    file_count: int,
    folder_count: int,
) -> None:
    """Apply in-progress accumulated values to the root item row."""
    root_path = root_item.data(COL_NAME, Qt.ItemDataRole.UserRole) or ""
    root_size_str = format_size(size_bytes)
    root_item.setText(COL_NAME, f"{root_size_str}   {root_path}")
    root_item.setText(COL_SIZE, root_size_str)
    root_item.setText(COL_ALLOCATED, format_size(allocated_bytes))
    root_item.setText(COL_FILES, f"{file_count:,}")
    root_item.setText(COL_FOLDERS, f"{folder_count:,}")
    root_item.setData(COL_SIZE, Qt.ItemDataRole.UserRole, size_bytes)


def build_scanned_status_text(name: str, size_formatted: str) -> str:
    """Build the scan progress text for the latest buffered child."""
    return f"Scanned: {name} ({size_formatted})"
