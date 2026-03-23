"""Tree item construction helpers for StorageView."""
import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QBrush, QIcon
from PyQt6.QtWidgets import QFileIconProvider, QTreeWidgetItem

from features.folder_scanner import FolderInfo, format_size
from ui.views.storage_view_tree_helpers import (
    build_folder_row_values,
    calculate_percent,
    compare_sort_values,
    format_count,
    summarize_direct_files,
)

logger = logging.getLogger(__name__)

COL_NAME = 0
COL_SIZE = 1
COL_ALLOCATED = 2
COL_FILES = 3
COL_FOLDERS = 4
COL_PERCENT = 5
NUM_COLUMNS = 6

ROLE_PATH = Qt.ItemDataRole.UserRole
ROLE_PERCENT_BAR = Qt.ItemDataRole.UserRole + 1
ROLE_IS_ROOT = Qt.ItemDataRole.UserRole + 2

_MAX_FILE_ENTRIES = 100
_icon_provider = QFileIconProvider()
_BOLD_FONT = QFont()
_BOLD_FONT.setBold(True)
_ROOT_BG_BRUSH = QBrush(QColor("#E8F0FE"))
_GENERIC_FOLDER_ICON: QIcon | None = None
_GENERIC_FILE_ICON: QIcon | None = None


def _get_generic_folder_icon() -> QIcon:
    """Return cached generic folder icon."""
    global _GENERIC_FOLDER_ICON
    if _GENERIC_FOLDER_ICON is None:
        _GENERIC_FOLDER_ICON = _icon_provider.icon(
            QFileIconProvider.IconType.Folder)
    return _GENERIC_FOLDER_ICON


def _get_generic_file_icon() -> QIcon:
    """Return cached generic file icon."""
    global _GENERIC_FILE_ICON
    if _GENERIC_FILE_ICON is None:
        _GENERIC_FILE_ICON = _icon_provider.icon(
            QFileIconProvider.IconType.File)
    return _GENERIC_FILE_ICON


def _align_numeric_columns(item: QTreeWidgetItem) -> None:
    for col in (COL_SIZE, COL_ALLOCATED, COL_FILES, COL_FOLDERS, COL_PERCENT):
        item.setTextAlignment(
            col,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )


def _apply_root_styles(item: QTreeWidgetItem) -> None:
    for col in range(NUM_COLUMNS):
        item.setFont(col, _BOLD_FONT)
    for col in (COL_SIZE, COL_ALLOCATED, COL_FILES, COL_FOLDERS):
        item.setBackground(col, _ROOT_BG_BRUSH)


def _add_child_tree_items(
    item: QTreeWidgetItem,
    children: list[FolderInfo],
    child_reference: int,
) -> None:
    for child in children:
        item.addChild(build_tree_item(child, child_reference))


def _add_loading_placeholder(item: QTreeWidgetItem) -> None:
    placeholder = NumericSortItem()
    placeholder.setText(COL_NAME, "Loading...")
    placeholder.setData(COL_NAME, ROLE_PATH, "__placeholder__")
    item.addChild(placeholder)


class NumericSortItem(QTreeWidgetItem):
    """QTreeWidgetItem with numeric sorting for size/percent columns."""

    def __lt__(self, other: QTreeWidgetItem) -> bool:
        tw = self.treeWidget()
        column = tw.sortColumn() if tw else 0
        try:
            result = compare_sort_values(
                column=column,
                percent_column=COL_PERCENT,
                size_columns=(COL_SIZE, COL_ALLOCATED),
                count_columns=(COL_FILES, COL_FOLDERS),
                self_text=self.text(column),
                other_text=other.text(column),
                self_user_value=self.data(column, Qt.ItemDataRole.UserRole),
                other_user_value=other.data(column, Qt.ItemDataRole.UserRole),
            )
            if result is not None:
                return result
        except (TypeError, ValueError):
            pass
        return super().__lt__(other)


def build_tree_item(
    folder_info: FolderInfo,
    reference_size: int,
    is_root: bool = False,
) -> QTreeWidgetItem:
    """Create a tree item from FolderInfo."""
    try:
        item = NumericSortItem()
        row = build_folder_row_values(folder_info, reference_size)
        item.setText(COL_NAME, row["name_text"])
        item.setText(COL_SIZE, row["size_text"])
        item.setText(COL_ALLOCATED, row["allocated_text"])
        item.setText(COL_FILES, row["files_text"])
        item.setText(COL_FOLDERS, row["folders_text"])
        item.setText(COL_PERCENT, row["percent_text"])

        percent = row["percent"]
        item.setData(COL_NAME, ROLE_PATH, row["path"])
        item.setData(COL_NAME, ROLE_PERCENT_BAR, percent)
        item.setData(COL_NAME, ROLE_IS_ROOT, is_root)
        item.setData(COL_SIZE, Qt.ItemDataRole.UserRole, row["size_bytes"])
        item.setData(COL_ALLOCATED, Qt.ItemDataRole.UserRole, row["allocated_bytes"])
        item.setData(COL_PERCENT, Qt.ItemDataRole.UserRole, percent)
        item.setIcon(COL_NAME, _get_generic_folder_icon())
        _align_numeric_columns(item)

        if is_root:
            _apply_root_styles(item)

        child_reference = folder_info.size_bytes if folder_info.size_bytes > 0 else 1
        _add_child_tree_items(item, folder_info.children, child_reference)

        if folder_info.children or folder_info.direct_files:
            add_file_entries(item, folder_info, child_reference)

        if folder_info.has_unscanned_children and not folder_info.children:
            _add_loading_placeholder(item)

        return item
    except Exception as e:
        logger.error("Failed to build tree item: %s", e)
        return NumericSortItem()


def add_file_entries(
    parent_item: QTreeWidgetItem,
    folder_info: FolderInfo,
    reference_size: int,
) -> None:
    """Add grouped file entries under a folder tree item."""
    try:
        if not folder_info.direct_files:
            return

        summary = summarize_direct_files(folder_info.direct_files, _MAX_FILE_ENTRIES)
        file_count = summary.file_count
        total_size = summary.total_size
        total_alloc = summary.total_allocated

        group_item = NumericSortItem()
        group_label = f"[{file_count:,} Files]"
        group_item.setText(COL_NAME, f"{format_size(total_size)}   {group_label}")
        group_item.setText(COL_SIZE, format_size(total_size))
        group_item.setText(COL_ALLOCATED, format_size(total_alloc))
        group_item.setText(COL_FILES, format_count(file_count))
        group_item.setText(COL_FOLDERS, format_count(0))

        percent = calculate_percent(total_size, reference_size)
        group_item.setText(COL_PERCENT, f"{percent:.1f} %" if reference_size > 0 else "-")

        group_item.setData(COL_NAME, ROLE_PATH, "__files_group__")
        group_item.setData(COL_NAME, ROLE_PERCENT_BAR, percent)
        group_item.setData(COL_SIZE, Qt.ItemDataRole.UserRole, total_size)
        group_item.setData(COL_ALLOCATED, Qt.ItemDataRole.UserRole, total_alloc)
        group_item.setData(COL_PERCENT, Qt.ItemDataRole.UserRole, percent)
        group_item.setIcon(COL_NAME, _get_generic_file_icon())
        _align_numeric_columns(group_item)

        for fentry in summary.shown_files:
            file_item = NumericSortItem()
            file_item.setText(COL_NAME, f"{format_size(fentry.size_bytes)}   {fentry.name}")
            file_item.setText(COL_SIZE, format_size(fentry.size_bytes))
            file_item.setText(COL_ALLOCATED, format_size(fentry.allocated_bytes))
            file_item.setText(COL_FILES, format_count(1))
            file_item.setText(COL_FOLDERS, format_count(0))

            file_percent = calculate_percent(fentry.size_bytes, reference_size)
            file_item.setText(COL_PERCENT, f"{file_percent:.1f} %" if reference_size > 0 else "-")

            file_item.setData(COL_NAME, ROLE_PATH, fentry.path)
            file_item.setData(COL_NAME, ROLE_PERCENT_BAR, file_percent)
            file_item.setData(COL_SIZE, Qt.ItemDataRole.UserRole, fentry.size_bytes)
            file_item.setData(COL_ALLOCATED, Qt.ItemDataRole.UserRole, fentry.allocated_bytes)
            file_item.setData(COL_PERCENT, Qt.ItemDataRole.UserRole, file_percent)
            file_item.setIcon(COL_NAME, _get_generic_file_icon())
            _align_numeric_columns(file_item)
            group_item.addChild(file_item)

        if summary.omitted_count > 0:
            more_item = NumericSortItem()
            more_item.setText(
                COL_NAME,
                f"{format_size(summary.omitted_size)}   "
                f"[{summary.omitted_count:,} more files...]",
            )
            more_item.setText(COL_SIZE, format_size(summary.omitted_size))
            more_item.setText(COL_FILES, f"{summary.omitted_count:,}")
            more_item.setData(COL_NAME, ROLE_PATH, "__files_group__")
            more_item.setData(COL_SIZE, Qt.ItemDataRole.UserRole, summary.omitted_size)
            more_item.setData(COL_ALLOCATED, Qt.ItemDataRole.UserRole, summary.omitted_size)
            more_item.setIcon(COL_NAME, _get_generic_file_icon())
            _align_numeric_columns(more_item)
            group_item.addChild(more_item)

        parent_item.addChild(group_item)
    except Exception as e:
        logger.error("Failed to add file entries: %s", e)
