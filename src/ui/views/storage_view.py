"""Storage View - Displays drive information and folder sizes (TreeSize-like)."""
import logging
from typing import Optional, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QProgressBar, QLabel, QFrame, QPushButton, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont

from features.storage_monitor import DriveInfo
from features.folder_scanner import FolderScanner, FolderInfo

logger = logging.getLogger(__name__)


class ScanWorker(QThread):
    """Worker thread for folder scanning."""

    progress = pyqtSignal(str, int)  # current_path, items_scanned
    finished = pyqtSignal(object)  # FolderInfo or None

    def __init__(self, scanner: FolderScanner, path: str, max_depth: int = 1):
        """Initialize worker with scanner and parameters."""
        try:
            super().__init__()
            self.scanner = scanner
            self.path = path
            self.max_depth = max_depth
        except Exception as e:
            logger.error("Failed to init ScanWorker: %s", e)

    def run(self):
        """Execute the folder scan in a separate thread."""
        try:
            result = self.scanner.scan_folder(
                self.path,
                max_depth=self.max_depth,
                progress_callback=self._on_progress,
            )
            self.finished.emit(result)
        except Exception as e:
            logger.error("Scan worker failed: %s", e)
            self.finished.emit(None)

    def _on_progress(self, current_path: str, items_scanned: int):
        """Emit progress signal with scan updates."""
        try:
            self.progress.emit(current_path, items_scanned)
        except Exception as e:
            logger.error("Failed to emit progress: %s", e)


class StorageView(QWidget):
    """View displaying drives and folder sizes with TreeSize-like interface."""

    refresh_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the storage view."""
        try:
            super().__init__(parent)
            self._drives: List[DriveInfo] = []
            self._scanner = FolderScanner()
            self._worker: Optional[ScanWorker] = None
            self._setup_ui()
        except Exception as e:
            logger.error("Failed to init StorageView: %s", e)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(16)

            # Header
            header_layout = QHBoxLayout()

            title = QLabel("Storage Analyzer")
            title_font = QFont()
            title_font.setPointSize(18)
            title_font.setBold(True)
            title.setFont(title_font)
            header_layout.addWidget(title)

            header_layout.addStretch()
            layout.addLayout(header_layout)

            # Description
            desc = QLabel(
                "Analyze disk space usage by folder. Select a drive and click Scan.")
            desc.setStyleSheet("color: #666666;")
            layout.addWidget(desc)

            # Separator
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setStyleSheet("background-color: #E0E0E0;")
            layout.addWidget(separator)

            # Drive selection row
            drive_layout = QHBoxLayout()

            drive_label = QLabel("Drive:")
            drive_layout.addWidget(drive_label)

            self._drive_combo = QComboBox()
            self._drive_combo.setMinimumWidth(150)
            self._drive_combo.setCursor(Qt.CursorShape.PointingHandCursor)
            drive_layout.addWidget(self._drive_combo)

            self._scan_btn = QPushButton("Scan")
            self._scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._scan_btn.clicked.connect(self._on_scan)
            self._scan_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0078D4;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #005A9E;
                }
                QPushButton:disabled {
                    background-color: #CCCCCC;
                }
            """)
            drive_layout.addWidget(self._scan_btn)

            self._cancel_btn = QPushButton("Cancel")
            self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._cancel_btn.clicked.connect(self._on_cancel)
            self._cancel_btn.setEnabled(False)
            drive_layout.addWidget(self._cancel_btn)

            self._refresh_btn = QPushButton("Refresh Drives")
            self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._refresh_btn.clicked.connect(self._on_refresh)
            drive_layout.addWidget(self._refresh_btn)

            drive_layout.addStretch()
            layout.addLayout(drive_layout)

            # Progress bar (hidden by default)
            self._progress_bar = QProgressBar()
            self._progress_bar.setTextVisible(True)
            self._progress_bar.setFormat("Scanning... %v items")
            self._progress_bar.setMaximum(0)  # Indeterminate
            self._progress_bar.hide()
            layout.addWidget(self._progress_bar)

            # Status label
            self._status_label = QLabel("")
            self._status_label.setStyleSheet("color: #666666; font-size: 11px;")
            layout.addWidget(self._status_label)

            # Drive summary section with capacity bars
            self._summary_frame = QFrame()
            self._summary_frame.setStyleSheet("""
                QFrame#SummaryFrame {
                    background-color: #F8F9FA;
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                }
            """)
            self._summary_frame.setObjectName("SummaryFrame")
            self._summary_layout = QVBoxLayout(self._summary_frame)
            self._summary_layout.setContentsMargins(12, 12, 12, 12)
            self._summary_layout.setSpacing(8)

            summary_title = QLabel("Drive Summary")
            summary_title.setStyleSheet("font-weight: bold; color: #333333;")
            self._summary_layout.addWidget(summary_title)

            # Container for drive bars (will be populated dynamically)
            self._drive_bars_widget = QWidget()
            self._drive_bars_layout = QVBoxLayout(self._drive_bars_widget)
            self._drive_bars_layout.setContentsMargins(0, 0, 0, 0)
            self._drive_bars_layout.setSpacing(8)
            self._summary_layout.addWidget(self._drive_bars_widget)

            layout.addWidget(self._summary_frame)

            # Tree widget for folder sizes
            self._tree = QTreeWidget()
            self._tree.setHeaderLabels(
                ["Name", "Size", "Files", "Folders", "% of Parent"])
            self._tree.setAlternatingRowColors(True)
            self._tree.setRootIsDecorated(True)
            self._tree.setSortingEnabled(True)
            self._tree.sortByColumn(1, Qt.SortOrder.DescendingOrder)

            # Column widths
            header = self._tree.header()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(4, 100)

            self._tree.setStyleSheet("""
                QTreeWidget {
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                    background-color: white;
                }
                QTreeWidget::item {
                    padding: 4px;
                }
                QHeaderView::section {
                    background-color: #F5F5F5;
                    padding: 8px;
                    border: none;
                    border-bottom: 1px solid #E0E0E0;
                    font-weight: bold;
                }
            """)

            # Double-click to expand/scan deeper
            self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)

            layout.addWidget(self._tree)
        except Exception as e:
            logger.error("Failed to setup StorageView UI: %s", e)

    def update_drives(self, drives: List[DriveInfo]) -> None:
        """Update the drive combo box and summary."""
        try:
            self._drives = drives
            current_selection = self._drive_combo.currentText()

            self._drive_combo.clear()
            for drive in drives:
                label = f"{
                    drive.letter} ({
                    drive.free_gb:.1f} GB free of {
                    drive.total_gb:.1f} GB)"
                self._drive_combo.addItem(label, drive.letter)

            # Restore selection if possible
            for i in range(self._drive_combo.count()):
                if current_selection and current_selection.startswith(
                        self._drive_combo.itemData(i)):
                    self._drive_combo.setCurrentIndex(i)
                    break

            # Update summary display
            self._update_drive_summary()
        except Exception as e:
            logger.error("Failed to update drives: %s", e)

    def _on_scan(self) -> None:
        """Start scanning the selected drive."""
        try:
            if self._drive_combo.currentIndex() < 0:
                return

            drive_letter = self._drive_combo.currentData()
            if not drive_letter:
                return

            path = f"{drive_letter}\\"
            self._start_scan(path)
        except Exception as e:
            logger.error("Failed to start scan: %s", e)

    def _start_scan(self, path: str, max_depth: int = 1) -> None:
        """Start scanning a path."""
        try:
            self._tree.clear()
            self._scan_btn.setEnabled(False)
            self._cancel_btn.setEnabled(True)
            self._progress_bar.show()
            self._progress_bar.setValue(0)
            self._status_label.setText(f"Scanning {path}...")

            self._worker = ScanWorker(self._scanner, path, max_depth)
            self._worker.progress.connect(self._on_scan_progress)
            self._worker.finished.connect(self._on_scan_finished)
            self._worker.start()
        except Exception as e:
            logger.error("Failed to start scan: %s", e)
            self._scan_btn.setEnabled(True)

    def _on_cancel(self) -> None:
        """Cancel ongoing scan."""
        try:
            self._scanner.cancel()
            self._cancel_btn.setEnabled(False)
            self._status_label.setText("Cancelling...")
        except Exception as e:
            logger.error("Failed to cancel scan: %s", e)

    @pyqtSlot(str, int)
    def _on_scan_progress(self, current_path: str, items_scanned: int) -> None:
        """Update progress display."""
        try:
            self._progress_bar.setValue(items_scanned)
            # Show abbreviated path
            if len(current_path) > 50:
                display_path = "..." + current_path[-47:]
            else:
                display_path = current_path
            self._status_label.setText(f"Scanning: {display_path}")
        except Exception as e:
            logger.error("Failed to update scan progress: %s", e)

    @pyqtSlot(object)
    def _on_scan_finished(self, result: Optional[FolderInfo]) -> None:
        """Handle scan completion."""
        try:
            self._scan_btn.setEnabled(True)
            self._cancel_btn.setEnabled(False)
            self._progress_bar.hide()

            if result is None:
                self._status_label.setText("Scan cancelled or failed.")
                return

            self._status_label.setText(
                f"Scan complete: {
                    result.size_formatted()} in {
                    result.file_count:,} files")

            # Populate tree
            self._populate_tree(result)
        except Exception as e:
            logger.error("Failed to handle scan completion: %s", e)

    def _populate_tree(self, folder_info: FolderInfo) -> None:
        """Populate tree widget with folder data."""
        try:
            self._tree.clear()

            # Add root item
            root_item = self._create_tree_item(
                folder_info, folder_info.size_bytes)
            self._tree.addTopLevelItem(root_item)
            root_item.setExpanded(True)

            # Expand first level
            for i in range(root_item.childCount()):
                root_item.child(i).setExpanded(False)
        except Exception as e:
            logger.error("Failed to populate tree: %s", e)

    def _create_tree_item(
        self,
        folder_info: FolderInfo,
        parent_size: int
    ) -> QTreeWidgetItem:
        """Create a tree item from FolderInfo."""
        try:
            item = QTreeWidgetItem()

            item.setText(0, folder_info.name or folder_info.path)
            item.setText(1, folder_info.size_formatted())
            item.setText(
                2, f"{folder_info.file_count:,}" if folder_info.file_count else "-")
            item.setText(
                3, f"{folder_info.folder_count:,}" if folder_info.folder_count else "-")

            # Percentage of parent
            if parent_size > 0:
                percent = (folder_info.size_bytes / parent_size) * 100
                item.setText(4, f"{percent:.1f}%")
            else:
                item.setText(4, "-")

            # Store data for later use
            item.setData(0, Qt.ItemDataRole.UserRole, folder_info.path)
            item.setData(1, Qt.ItemDataRole.UserRole, folder_info.size_bytes)

            # Right-align numeric columns
            item.setTextAlignment(
                1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setTextAlignment(
                2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setTextAlignment(
                3, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setTextAlignment(
                4, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            # Add children
            for child in folder_info.children:
                child_item = self._create_tree_item(child, folder_info.size_bytes)
                item.addChild(child_item)

            return item
        except Exception as e:
            logger.error("Failed to create tree item: %s", e)
            return QTreeWidgetItem()

    def _on_item_double_clicked(
            self,
            item: QTreeWidgetItem,
            column: int) -> None:
        """Handle double-click to scan deeper."""
        try:
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path and Path(path).is_dir():
                # Scan this folder with more depth
                self._start_scan(path, max_depth=2)
        except Exception as e:
            logger.error("Failed to handle double-click: %s", e)

    def _update_drive_summary(self) -> None:
        """Update the drive summary display with capacity bars."""
        try:
            # Clear existing drive bars
            while self._drive_bars_layout.count():
                item = self._drive_bars_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            if not self._drives:
                no_drives_label = QLabel(
                    "No drives detected. Click Refresh Drives.")
                no_drives_label.setStyleSheet("color: #666666;")
                self._drive_bars_layout.addWidget(no_drives_label)
                return

            total_used = 0
            total_capacity = 0

            # Sort drives by used space (largest first)
            sorted_drives = sorted(
                self._drives,
                key=lambda d: d.total_gb - d.free_gb,
                reverse=True)

            for drive in sorted_drives:
                used_gb = drive.total_gb - drive.free_gb
                used_percent = int((used_gb / drive.total_gb * 100)
                                   ) if drive.total_gb > 0 else 0

                total_used += used_gb
                total_capacity += drive.total_gb

                # Create row for this drive
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(8)

                # Drive label
                drive_label = QLabel(f"{drive.letter}")
                drive_label.setFixedWidth(30)
                drive_label.setStyleSheet("font-weight: bold; color: #333333;")
                row_layout.addWidget(drive_label)

                # Progress bar
                progress = QProgressBar()
                progress.setValue(used_percent)
                progress.setTextVisible(True)
                progress.setFormat(
                    f"Free: {drive.free_gb:.1f} GB | Used: {used_gb:.1f} GB | Total: {drive.total_gb:.1f} GB")
                progress.setMinimumHeight(24)

                # Color based on usage
                if used_percent > 90:
                    color = "#DC3545"  # Red - critical
                elif used_percent > 75:
                    color = "#FFC107"  # Yellow - warning
                else:
                    color = "#0078D4"  # Blue - normal

                progress.setStyleSheet(f"""
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
                """)
                row_layout.addWidget(progress)

                self._drive_bars_layout.addWidget(row_widget)
        except Exception as e:
            logger.error("Failed to update drive summary: %s", e)

    def _on_refresh(self) -> None:
        """Handle refresh button click."""
        try:
            self.refresh_requested.emit()
        except Exception as e:
            logger.error("Failed to handle refresh: %s", e)
