"""Interaction handlers extracted from StorageView."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QProgressBar,
    QTreeWidgetItem,
    QWidget,
)

from shared.utils import is_protected_path
from ui.views.storage_view_actions import open_file_location, recycle_path
from ui.views.storage_view_navigation import (
    navigate_back_state,
    navigate_forward_state,
    resolve_cached_node,
)
from ui.views.storage_view_tree import COL_NAME

logger = logging.getLogger(__name__)


class StorageInteractionController:
    """Owns storage interaction flows while preserving legacy wrappers."""

    def __init__(self, view):
        self.view = view

    def on_tree_context_menu(self, position) -> None:
        """Show context menu for the selected file system item."""
        try:
            item = self.view._tree.itemAt(position)
            if item is None:
                return

            path = item.data(COL_NAME, Qt.ItemDataRole.UserRole)
            if not path or path in ("__placeholder__", "__other_files__", "__files_group__"):
                return

            menu = QMenu(self.view)
            add_action = QAction("Add to Cleanup", self.view)
            add_action.triggered.connect(lambda: self.view._on_add_to_cleanup(path))
            menu.addAction(add_action)

            delete_action = QAction("Delete", self.view)
            delete_action.triggered.connect(lambda: self.view._on_delete_item(path, item))
            menu.addAction(delete_action)

            open_location_action = QAction("Open file location", self.view)
            open_location_action.triggered.connect(lambda: self.view._on_open_file_location(path))
            menu.addAction(open_location_action)

            menu.exec(self.view._tree.viewport().mapToGlobal(position))
        except Exception as exc:
            logger.error("Failed to show context menu: %s", exc)

    def on_add_to_cleanup(self, path: str) -> None:
        """Handle 'Add to Cleanup' action from context menu."""
        try:
            if is_protected_path(path):
                QMessageBox.warning(
                    self.view,
                    "Protected Directory",
                    f"'{path}' is a protected system directory and cannot be added to cleanup.",
                )
                return

            if not Path(path).is_dir():
                QMessageBox.warning(
                    self.view,
                    "Not a Directory",
                    f"'{path}' is not a valid directory.",
                )
                return

            self.view.add_to_cleanup_requested.emit(path)
            self.view._status_label.setText(f"Added to cleanup: {path}")
        except Exception as exc:
            logger.error("Failed to add to cleanup: %s", exc)

    def on_delete_item(self, path: str, item: Optional[QTreeWidgetItem] = None) -> None:
        """Move the selected file or folder to the Recycle Bin."""
        try:
            if is_protected_path(path):
                QMessageBox.warning(
                    self.view,
                    "Protected Path",
                    f"'{path}' is a protected system path and cannot be deleted.",
                )
                return

            target = Path(path)
            if not target.exists():
                QMessageBox.information(
                    self.view,
                    "Item Not Found",
                    f"'{path}' no longer exists.",
                )
                return

            result = QMessageBox.warning(
                self.view,
                "Confirm Delete",
                f"Move '{path}' to the Recycle Bin?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if result != QMessageBox.StandardButton.Yes:
                return

            recycle_path(path)

            if item is not None:
                parent = item.parent()
                if parent is not None:
                    parent.removeChild(item)
                else:
                    index = self.view._tree.indexOfTopLevelItem(item)
                    if index >= 0:
                        self.view._tree.takeTopLevelItem(index)

            self.view._status_label.setText(f"Deleted: {path}")
        except Exception as exc:
            logger.error("Failed to delete item: %s", exc)
            QMessageBox.warning(self.view, "Delete Failed", f"Failed to delete '{path}': {exc}")

    def on_open_file_location(self, path: str) -> None:
        """Open Explorer and select the file or folder."""
        try:
            open_file_location(path)
            self.view._status_label.setText(f"Opened file location: {path}")
        except FileNotFoundError:
            QMessageBox.information(
                self.view,
                "Item Not Found",
                f"'{path}' no longer exists.",
            )
        except Exception as exc:
            logger.error("Failed to open file location: %s", exc)
            QMessageBox.warning(
                self.view,
                "Open Location Failed",
                f"Failed to open file location for '{path}': {exc}",
            )

    def update_drive_summary(self) -> None:
        """Update the drive summary display with capacity bars."""
        try:
            while self.view._drive_bars_layout.count():
                item = self.view._drive_bars_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            if not self.view._drives:
                no_drives_label = QLabel("No drives detected. Click Refresh Drives.")
                no_drives_label.setStyleSheet("color: #666666;")
                self.view._drive_bars_layout.addWidget(no_drives_label)
                return

            sorted_drives = sorted(
                self.view._drives,
                key=lambda drive: drive.total_gb - drive.free_gb,
                reverse=True,
            )

            for drive in sorted_drives:
                used_gb = drive.total_gb - drive.free_gb
                used_percent = int((used_gb / drive.total_gb * 100)) if drive.total_gb > 0 else 0

                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(8)

                drive_label = QLabel(f"{drive.letter}")
                drive_label.setFixedWidth(30)
                drive_label.setStyleSheet("font-weight: bold; color: #333333;")
                row_layout.addWidget(drive_label)

                progress = QProgressBar()
                progress.setValue(used_percent)
                progress.setTextVisible(True)
                progress.setFormat(
                    f"Free: {drive.free_gb:.1f} GB | "
                    f"Used: {used_gb:.1f} GB | "
                    f"Total: {drive.total_gb:.1f} GB"
                )
                progress.setMinimumHeight(24)

                if used_percent > 90:
                    color = "#DC3545"
                elif used_percent > 75:
                    color = "#FFC107"
                else:
                    color = "#0078D4"

                progress.setStyleSheet(
                    f"""
                        QProgressBar {{
                            border: 1px solid #E0E0E0;
                            border-radius: 4px;
                            background-color: #F0F0F0;
                            text-align: center;
                            color: #333333;
                        }}
                        QProgressBar::chunk {{
                            background-color: {color};
                            border-radius: 3px;
                        }}
                    """
                )
                row_layout.addWidget(progress)
                self.view._drive_bars_layout.addWidget(row_widget)
        except Exception as exc:
            logger.error("Failed to update drive summary: %s", exc)

    def on_refresh(self) -> None:
        """Handle refresh button click."""
        try:
            self.view.refresh_requested.emit()
        except Exception as exc:
            logger.error("Failed to handle refresh: %s", exc)

    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click to navigate into subfolder."""
        del column
        try:
            path = item.data(COL_NAME, Qt.ItemDataRole.UserRole)
            if path and path not in ("__placeholder__", "__other_files__", "__files_group__"):
                if Path(path).is_dir():
                    if self.view._current_scan_path:
                        self.view._nav_history.append(self.view._current_scan_path)
                        self.view._nav_forward.clear()
                    self.view._current_scan_path = path
                    update_nav_buttons(self.view)

                    cached = self.view._path_index.get(path)
                    if cached:
                        self.view._populate_tree(cached)
                        self.view._status_label.setText(
                            f"Navigated: {cached.size_formatted()} in "
                            f"{cached.file_count:,} files, "
                            f"{cached.folder_count:,} folders"
                        )
                    else:
                        self.view._start_realtime_scan(path)
        except Exception as exc:
            logger.error("Failed to handle double-click: %s", exc)

    def on_navigate_back(self) -> None:
        """Navigate back to the previous folder (cached if available)."""
        try:
            next_path, new_history, new_forward = navigate_back_state(
                self.view._current_scan_path,
                self.view._nav_history,
                self.view._nav_forward,
            )
            if not next_path:
                return

            self.view._current_scan_path = next_path
            self.view._nav_history = new_history
            self.view._nav_forward = new_forward
            update_nav_buttons(self.view)

            cached = resolve_cached_node(next_path, self.view._path_index, self.view._scan_cache)
            if cached:
                self.view._populate_tree(cached)
                self.view._status_label.setText(
                    f"Navigated back: {cached.size_formatted()} in "
                    f"{cached.file_count:,} files, "
                    f"{cached.folder_count:,} folders"
                )
            else:
                self.view._start_realtime_scan(next_path)
        except Exception as exc:
            logger.error("Failed to navigate back: %s", exc)

    def on_navigate_forward(self) -> None:
        """Navigate forward to the next folder (cached if available)."""
        try:
            next_path, new_history, new_forward = navigate_forward_state(
                self.view._current_scan_path,
                self.view._nav_history,
                self.view._nav_forward,
            )
            if not next_path:
                return

            self.view._current_scan_path = next_path
            self.view._nav_history = new_history
            self.view._nav_forward = new_forward
            update_nav_buttons(self.view)

            cached = resolve_cached_node(next_path, self.view._path_index, self.view._scan_cache)
            if cached:
                self.view._populate_tree(cached)
                self.view._status_label.setText(
                    f"Navigated forward: {cached.size_formatted()} in "
                    f"{cached.file_count:,} files, "
                    f"{cached.folder_count:,} folders"
                )
            else:
                self.view._start_realtime_scan(next_path)
        except Exception as exc:
            logger.error("Failed to navigate forward: %s", exc)

    def update_nav_buttons(self) -> None:
        """Update enabled state of back/forward buttons."""
        try:
            self.view._back_btn.setEnabled(len(self.view._nav_history) > 0)
            self.view._forward_btn.setEnabled(len(self.view._nav_forward) > 0)
        except Exception as exc:
            logger.error("Failed to update nav buttons: %s", exc)


def _controller_for(view) -> StorageInteractionController:
    controller = getattr(view, "_interaction_controller", None)
    if controller is None:
        controller = StorageInteractionController(view)
    return controller


def on_tree_context_menu(view, position) -> None:
    """Show context menu for the selected file system item."""
    _controller_for(view).on_tree_context_menu(position)


def on_add_to_cleanup(view, path: str) -> None:
    """Handle 'Add to Cleanup' action from context menu."""
    _controller_for(view).on_add_to_cleanup(path)


def on_delete_item(view, path: str, item: Optional[QTreeWidgetItem] = None) -> None:
    """Move the selected file or folder to the Recycle Bin."""
    _controller_for(view).on_delete_item(path, item)


def on_open_file_location(view, path: str) -> None:
    """Open Explorer and select the file or folder."""
    _controller_for(view).on_open_file_location(path)


def update_drive_summary(view) -> None:
    """Update the drive summary display with capacity bars."""
    _controller_for(view).update_drive_summary()


def on_refresh(view) -> None:
    """Handle refresh button click."""
    _controller_for(view).on_refresh()


def on_item_double_clicked(view, item: QTreeWidgetItem, column: int) -> None:
    """Handle double-click to navigate into subfolder."""
    _controller_for(view).on_item_double_clicked(item, column)


def on_navigate_back(view) -> None:
    """Navigate back to the previous folder (cached if available)."""
    _controller_for(view).on_navigate_back()


def on_navigate_forward(view) -> None:
    """Navigate forward to the next folder (cached if available)."""
    _controller_for(view).on_navigate_forward()


def update_nav_buttons(view) -> None:
    """Update enabled state of back/forward buttons."""
    _controller_for(view).update_nav_buttons()
