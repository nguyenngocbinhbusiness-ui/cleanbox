"""Tree item construction helpers for StorageView."""
import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QBrush, QIcon
from PyQt6.QtWidgets import QFileIconProvider, QTreeWidgetItem

from features.folder_scanner import FolderInfo, format_size

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


class NumericSortItem(QTreeWidgetItem):
    """QTreeWidgetItem with numeric sorting for size/percent columns."""

    def __lt__(self, other: QTreeWidgetItem) -> bool:
        tw = self.treeWidget()
        column = tw.sortColumn() if tw else 0
        if column == COL_PERCENT:
            self_val = self.data(COL_PERCENT, Qt.ItemDataRole.UserRole) or 0.0
            other_val = other.data(COL_PERCENT, Qt.ItemDataRole.UserRole) or 0.0
            return float(self_val) < float(other_val)
        if column in (COL_SIZE, COL_ALLOCATED):
            self_val = self.data(column, Qt.ItemDataRole.UserRole) or 0
            other_val = other.data(column, Qt.ItemDataRole.UserRole) or 0
            return int(self_val) < int(other_val)
        if column in (COL_FILES, COL_FOLDERS):
            try:
                s_text = self.text(column).replace(",", "")
                o_text = other.text(column).replace(",", "")
                s_val = int(s_text) if s_text != "-" else 0
                o_val = int(o_text) if o_text != "-" else 0
                return s_val < o_val
            except ValueError:
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
        display_name = folder_info.name or folder_info.path
        size_prefix = folder_info.size_formatted()
        item.setText(COL_NAME, f"{size_prefix}   {display_name}")
        item.setText(COL_SIZE, folder_info.size_formatted())
        item.setText(COL_ALLOCATED, folder_info.allocated_formatted())
        item.setText(COL_FILES, f"{folder_info.file_count:,}" if folder_info.file_count else "-")
        item.setText(COL_FOLDERS, f"{folder_info.folder_count:,}" if folder_info.folder_count else "-")

        percent = 0.0
        if reference_size > 0:
            percent = (folder_info.size_bytes / reference_size) * 100
            item.setText(COL_PERCENT, f"{percent:.1f} %")
        else:
            item.setText(COL_PERCENT, "-")

        item.setData(COL_NAME, ROLE_PATH, folder_info.path)
        item.setData(COL_NAME, ROLE_PERCENT_BAR, percent)
        item.setData(COL_NAME, ROLE_IS_ROOT, is_root)
        item.setData(COL_SIZE, Qt.ItemDataRole.UserRole, folder_info.size_bytes)
        item.setData(COL_ALLOCATED, Qt.ItemDataRole.UserRole, folder_info.allocated_bytes)
        item.setData(COL_PERCENT, Qt.ItemDataRole.UserRole, percent)
        item.setIcon(COL_NAME, _get_generic_folder_icon())
        _align_numeric_columns(item)

        if is_root:
            for col in range(NUM_COLUMNS):
                item.setFont(col, _BOLD_FONT)
            for col in (COL_SIZE, COL_ALLOCATED, COL_FILES, COL_FOLDERS):
                item.setBackground(col, _ROOT_BG_BRUSH)

        child_reference = folder_info.size_bytes if folder_info.size_bytes > 0 else 1
        for child in folder_info.children:
            item.addChild(build_tree_item(child, child_reference))

        if folder_info.children or folder_info.direct_files:
            add_file_entries(item, folder_info, child_reference)

        if folder_info.has_unscanned_children and not folder_info.children:
            placeholder = NumericSortItem()
            placeholder.setText(COL_NAME, "Loading...")
            placeholder.setData(COL_NAME, ROLE_PATH, "__placeholder__")
            item.addChild(placeholder)

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

        file_count = len(folder_info.direct_files)
        total_size = sum(f.size_bytes for f in folder_info.direct_files)
        total_alloc = sum(f.allocated_bytes for f in folder_info.direct_files)

        group_item = NumericSortItem()
        group_label = f"[{file_count:,} Files]"
        group_item.setText(COL_NAME, f"{format_size(total_size)}   {group_label}")
        group_item.setText(COL_SIZE, format_size(total_size))
        group_item.setText(COL_ALLOCATED, format_size(total_alloc))
        group_item.setText(COL_FILES, f"{file_count:,}")
        group_item.setText(COL_FOLDERS, "-")

        percent = 0.0
        if reference_size > 0:
            percent = (total_size / reference_size) * 100
            group_item.setText(COL_PERCENT, f"{percent:.1f} %")
        else:
            group_item.setText(COL_PERCENT, "-")

        group_item.setData(COL_NAME, ROLE_PATH, "__files_group__")
        group_item.setData(COL_NAME, ROLE_PERCENT_BAR, percent)
        group_item.setData(COL_SIZE, Qt.ItemDataRole.UserRole, total_size)
        group_item.setData(COL_ALLOCATED, Qt.ItemDataRole.UserRole, total_alloc)
        group_item.setData(COL_PERCENT, Qt.ItemDataRole.UserRole, percent)
        group_item.setIcon(COL_NAME, _get_generic_file_icon())
        _align_numeric_columns(group_item)

        shown_files = folder_info.direct_files[:_MAX_FILE_ENTRIES]
        omitted = file_count - len(shown_files)

        for fentry in shown_files:
            file_item = NumericSortItem()
            file_item.setText(COL_NAME, f"{format_size(fentry.size_bytes)}   {fentry.name}")
            file_item.setText(COL_SIZE, format_size(fentry.size_bytes))
            file_item.setText(COL_ALLOCATED, format_size(fentry.allocated_bytes))
            file_item.setText(COL_FILES, "1")
            file_item.setText(COL_FOLDERS, "-")

            file_percent = 0.0
            if reference_size > 0:
                file_percent = (fentry.size_bytes / reference_size) * 100
                file_item.setText(COL_PERCENT, f"{file_percent:.1f} %")
            else:
                file_item.setText(COL_PERCENT, "-")

            file_item.setData(COL_NAME, ROLE_PATH, fentry.path)
            file_item.setData(COL_NAME, ROLE_PERCENT_BAR, file_percent)
            file_item.setData(COL_SIZE, Qt.ItemDataRole.UserRole, fentry.size_bytes)
            file_item.setData(COL_ALLOCATED, Qt.ItemDataRole.UserRole, fentry.allocated_bytes)
            file_item.setData(COL_PERCENT, Qt.ItemDataRole.UserRole, file_percent)
            file_item.setIcon(COL_NAME, _get_generic_file_icon())
            _align_numeric_columns(file_item)
            group_item.addChild(file_item)

        if omitted > 0:
            omitted_size = sum(
                f.size_bytes for f in folder_info.direct_files[_MAX_FILE_ENTRIES:]
            )
            more_item = NumericSortItem()
            more_item.setText(
                COL_NAME,
                f"{format_size(omitted_size)}   [{omitted:,} more files...]",
            )
            more_item.setText(COL_SIZE, format_size(omitted_size))
            more_item.setText(COL_FILES, f"{omitted:,}")
            more_item.setData(COL_NAME, ROLE_PATH, "__files_group__")
            more_item.setData(COL_SIZE, Qt.ItemDataRole.UserRole, omitted_size)
            more_item.setData(COL_ALLOCATED, Qt.ItemDataRole.UserRole, omitted_size)
            more_item.setIcon(COL_NAME, _get_generic_file_icon())
            _align_numeric_columns(more_item)
            group_item.addChild(more_item)

        parent_item.addChild(group_item)
    except Exception as e:
        logger.error("Failed to add file entries: %s", e)
