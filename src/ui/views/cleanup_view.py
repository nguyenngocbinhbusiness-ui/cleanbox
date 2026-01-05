"""Cleanup View - Manage cleanup directories and actions."""
import logging
from pathlib import Path
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QFrame, QFileDialog, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from shared.constants import RECYCLE_BIN_MARKER

logger = logging.getLogger(__name__)


class CleanupView(QWidget):
    """View for managing cleanup directories and triggering cleanup."""

    directory_added = pyqtSignal(str)
    directory_removed = pyqtSignal(str)
    cleanup_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the cleanup view."""
        try:
            super().__init__(parent)
            self._directories: List[str] = []
            self._setup_ui()
        except Exception as e:
            logger.error("Failed to init CleanupView: %s", e)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(16)

            # Header
            title = QLabel("Cleanup Directories")
            title_font = QFont()
            title_font.setPointSize(18)
            title_font.setBold(True)
            title.setFont(title_font)
            layout.addWidget(title)

            # Description
            desc = QLabel(
                "Manage folders that will be emptied during cleanup.")
            desc.setStyleSheet("color: #666666;")
            layout.addWidget(desc)

            # Separator
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setStyleSheet("background-color: #E0E0E0;")
            layout.addWidget(separator)

            # Directory list
            self._dir_list = QListWidget()
            self._dir_list.setMinimumHeight(200)
            self._dir_list.setStyleSheet("""
                QListWidget {
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                    background-color: white;
                }
                QListWidget::item {
                    padding: 10px;
                    border-bottom: 1px solid #F0F0F0;
                }
                QListWidget::item:selected {
                    background-color: #E6F2FF;
                    color: #000000;
                }
                QListWidget::item:hover {
                    background-color: #F5F5F5;
                }
            """)
            layout.addWidget(self._dir_list)

            # Button row
            btn_layout = QHBoxLayout()

            self._add_btn = QPushButton("Add Directory")
            self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._add_btn.clicked.connect(self._on_add_directory)
            btn_layout.addWidget(self._add_btn)

            self._remove_btn = QPushButton("Remove Selected")
            self._remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._remove_btn.clicked.connect(self._on_remove_directory)
            btn_layout.addWidget(self._remove_btn)

            btn_layout.addStretch()
            layout.addLayout(btn_layout)

            layout.addStretch()

            # Cleanup button (prominent) - text only, no icon
            self._cleanup_btn = QPushButton("Clean Now")
            self._cleanup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._cleanup_btn.setMinimumHeight(50)
            cleanup_font = QFont()
            cleanup_font.setPointSize(12)
            cleanup_font.setBold(True)
            self._cleanup_btn.setFont(cleanup_font)
            self._cleanup_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0078D4;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 12px 24px;
                }
                QPushButton:hover {
                    background-color: #005A9E;
                }
                QPushButton:pressed {
                    background-color: #004578;
                }
            """)
            self._cleanup_btn.clicked.connect(self._on_cleanup)
            layout.addWidget(self._cleanup_btn)

            # Progress bar (hidden by default)
            self._progress_bar = QProgressBar()
            self._progress_bar.setVisible(False)
            self._progress_bar.setMinimum(0)
            self._progress_bar.setTextVisible(True)
            self._progress_bar.setFormat("Cleaning... %v/%m directories")
            self._progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                    background-color: #F5F5F5;
                    height: 24px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #FFC107;
                    border-radius: 3px;
                }
            """)
            layout.addWidget(self._progress_bar)
        except Exception as e:
            logger.error("Failed to setup cleanup view UI: %s", e)

    def update_directories(self, directories: List[str]) -> None:
        """Update the directory list."""
        try:
            self._directories = directories.copy()
            self._dir_list.clear()

            for directory in directories:
                if directory == RECYCLE_BIN_MARKER:
                    display_text = "[Recycle Bin]"
                else:
                    display_text = directory

                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, directory)
                self._dir_list.addItem(item)
        except Exception as e:
            logger.error("Failed to update directory list: %s", e)

    def _on_add_directory(self) -> None:
        """Handle add directory button click."""
        try:
            directory = QFileDialog.getExistingDirectory(
                self,
                "Select Directory to Clean",
                str(Path.home()),
            )
            if directory:
                if directory not in self._directories:
                    self._directories.append(directory)
                    self.update_directories(self._directories)
                    self.directory_added.emit(directory)
                    logger.info("Directory added: %s", directory)
                else:
                    QMessageBox.information(
                        self, "Already Added", "This directory is already in the list.")
        except Exception as e:
            logger.error("Failed to add directory: %s", e)
            QMessageBox.warning(self, "Error", f"Failed to add directory: {e}")

    def _on_remove_directory(self) -> None:
        """Handle remove directory button click."""
        try:
            current = self._dir_list.currentItem()
            if current:
                directory = current.data(Qt.ItemDataRole.UserRole)
                self._directories.remove(directory)
                self.update_directories(self._directories)
                self.directory_removed.emit(directory)
                logger.info("Directory removed: %s", directory)
            else:
                QMessageBox.information(
                    self, "No Selection", "Please select a directory to remove.")
        except Exception as e:
            logger.error("Failed to remove directory: %s", e)
            QMessageBox.warning(
                self, "Error", f"Failed to remove directory: {e}")

    def _on_cleanup(self) -> None:
        """Handle cleanup button click."""
        try:
            self.cleanup_requested.emit()
        except Exception as e:
            logger.error("Failed to request cleanup: %s", e)

    def show_progress_bar(self, visible: bool) -> None:
        """Show or hide the progress bar and toggle button state.
        
        Args:
            visible: True to show progress bar and disable button.
        """
        try:
            self._progress_bar.setVisible(visible)
            self._cleanup_btn.setEnabled(not visible)
            if not visible:
                self._progress_bar.setValue(0)
        except Exception as e:
            logger.error("Failed to toggle progress bar: %s", e)

    def set_progress(self, current: int, total: int) -> None:
        """Update the progress bar value.
        
        Args:
            current: Current progress (0 to total).
            total: Total number of items.
        """
        try:
            self._progress_bar.setMaximum(total)
            self._progress_bar.setValue(current)
        except Exception as e:
            logger.error("Failed to set progress: %s", e)
