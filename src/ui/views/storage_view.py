"""Storage View - Displays drive information and folder sizes (TreeSize-like)."""
import logging
from typing import Optional, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QProgressBar, QLabel, QFrame, QPushButton, QComboBox,
    QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QAction

from features.storage_monitor import DriveInfo
from features.folder_scanner import FolderScanner, FolderInfo
from shared.utils import is_protected_path

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


class ExpandScanWorker(QThread):
    """Worker thread for lazy-expand sub-folder scanning."""

    progress = pyqtSignal(str, int)
    finished = pyqtSignal(object)  # FolderInfo or None

    def __init__(self, scanner: FolderScanner, path: str):
        """Initialize expand worker."""
        try:
            super().__init__()
            self.scanner = scanner
            self.path = path
        except Exception as e:
            logger.error("Failed to init ExpandScanWorker: %s", e)

    def run(self):
        """Scan single level for expand."""
        try:
            result = self.scanner.scan_single_level(
                self.path,
                progress_callback=self._on_progress,
            )
            self.finished.emit(result)
        except Exception as e:
            logger.error("Expand scan worker failed: %s", e)
            self.finished.emit(None)

    def _on_progress(self, current_path: str, items_scanned: int):
        """Emit progress signal."""
        try:
            self.progress.emit(current_path, items_scanned)
        except Exception as e:
            logger.error("Failed to emit expand progress: %s", e)


class StorageView(QWidget):
    """View displaying drives and folder sizes with TreeSize-like interface."""

    refresh_requested = pyqtSignal()
    add_to_cleanup_requested = pyqtSignal(str)  # directory path

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the storage view."""
        try:
            super().__init__(parent)
            self._drives: List[DriveInfo] = []
            self._scanner = FolderScanner()
            self._worker: Optional[ScanWorker] = None
            self._expand_worker: Optional[ExpandScanWorker] = None
            self._expanding_item: Optional[QTreeWidgetItem] = None
            self._drive_total_bytes: int = 0
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
                ["Name", "Size", "Files", "Folders", "% of Drive"])
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

            # Context menu for right-click
            self._tree.setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu)
            self._tree.customContextMenuRequested.connect(
                self._on_tree_context_menu)

            # Expand arrow triggers lazy sub-folder scan
            self._tree.itemExpanded.connect(self._on_item_expanded)

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
                label = f"{drive.letter} ({drive.free_gb:.1f} GB free of {drive.total_gb:.1f} GB)"
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

            # Store drive total size for % calculation
            for drive in self._drives:
                if drive.letter == drive_letter:
                    self._drive_total_bytes = int(drive.total_gb * (1024 ** 3))
                    break

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
                f"Scan complete: {result.size_formatted()} in {result.file_count:,} files")

            # Populate tree
            self._populate_tree(result)
        except Exception as e:
            logger.error("Failed to handle scan completion: %s", e)

    def _populate_tree(self, folder_info: FolderInfo) -> None:
        """Populate tree widget with folder data."""
        try:
            self._tree.clear()

            # Use drive total for % at root level; fall back to scan size
            reference_size = self._drive_total_bytes or folder_info.size_bytes

            # Add root item (the drive itself = 100%)
            root_item = self._create_tree_item(
                folder_info, reference_size, is_root=True)
            self._tree.addTopLevelItem(root_item)
            root_item.setExpanded(True)

            # Add "(Other files)" entry if folder sizes don't account for all space
            self._add_other_files_entry(root_item, folder_info, reference_size)
        except Exception as e:
            logger.error("Failed to populate tree: %s", e)

    def _create_tree_item(
        self,
        folder_info: FolderInfo,
        reference_size: int,
        is_root: bool = False,
    ) -> QTreeWidgetItem:
        """Create a tree item from FolderInfo.

        Args:
            folder_info: Folder data
            reference_size: Size to compute % against (drive total at root, parent size for sub-levels)
            is_root: Whether this is the drive root item
        """
        try:
            item = QTreeWidgetItem()

            item.setText(0, folder_info.name or folder_info.path)
            item.setText(1, folder_info.size_formatted())
            item.setText(
                2, f"{folder_info.file_count:,}" if folder_info.file_count else "-")
            item.setText(
                3, f"{folder_info.folder_count:,}" if folder_info.folder_count else "-")

            # % of reference (drive total at root level)
            if reference_size > 0:
                percent = (folder_info.size_bytes / reference_size) * 100
                item.setText(4, f"{percent:.1f}%")
            else:
                item.setText(4, "-")

            # Store data for later use
            item.setData(0, Qt.ItemDataRole.UserRole, folder_info.path)
            item.setData(1, Qt.ItemDataRole.UserRole, folder_info.size_bytes)
            # Store whether this has unscanned children for lazy expand
            item.setData(
                2, Qt.ItemDataRole.UserRole,
                folder_info.has_unscanned_children)

            # Right-align numeric columns
            item.setTextAlignment(
                1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setTextAlignment(
                2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setTextAlignment(
                3, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setTextAlignment(
                4, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            # Children use parent's size as reference for sub-level %
            child_reference = folder_info.size_bytes if folder_info.size_bytes > 0 else 1

            for child in folder_info.children:
                child_item = self._create_tree_item(
                    child, child_reference)
                item.addChild(child_item)

            # Add "(Other files)" for this level if it has children
            if folder_info.children:
                self._add_other_files_entry(
                    item, folder_info, child_reference)

            # If folder has unscanned children, add a placeholder for expand arrow
            if folder_info.has_unscanned_children and not folder_info.children:
                placeholder = QTreeWidgetItem()
                placeholder.setText(0, "Loading...")
                placeholder.setData(0, Qt.ItemDataRole.UserRole, "__placeholder__")
                item.addChild(placeholder)

            return item
        except Exception as e:
            logger.error("Failed to create tree item: %s", e)
            return QTreeWidgetItem()

    def _add_other_files_entry(
        self,
        parent_item: QTreeWidgetItem,
        folder_info: FolderInfo,
        reference_size: int,
    ) -> None:
        """Add '(Other files)' entry to make percentages sum to 100%."""
        try:
            children_total = sum(c.size_bytes for c in folder_info.children)
            other_size = folder_info.size_bytes - children_total

            if other_size > 0 and folder_info.children:
                other_item = QTreeWidgetItem()
                other_item.setText(0, "(Other files)")

                # Format size
                if other_size >= 1024 * 1024 * 1024:
                    size_str = f"{other_size / (1024**3):.2f} GB"
                elif other_size >= 1024 * 1024:
                    size_str = f"{other_size / (1024**2):.2f} MB"
                elif other_size >= 1024:
                    size_str = f"{other_size / 1024:.2f} KB"
                else:
                    size_str = f"{other_size} B"

                other_item.setText(1, size_str)
                other_item.setText(2, "-")
                other_item.setText(3, "-")

                if reference_size > 0:
                    percent = (other_size / reference_size) * 100
                    other_item.setText(4, f"{percent:.1f}%")
                else:
                    other_item.setText(4, "-")

                other_item.setData(
                    0, Qt.ItemDataRole.UserRole, "__other_files__")
                other_item.setData(1, Qt.ItemDataRole.UserRole, other_size)

                # Right-align
                other_item.setTextAlignment(
                    1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                other_item.setTextAlignment(
                    2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                other_item.setTextAlignment(
                    3, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                other_item.setTextAlignment(
                    4, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                # Italic style for visual distinction
                font = QFont()
                font.setItalic(True)
                other_item.setFont(0, font)

                parent_item.addChild(other_item)
        except Exception as e:
            logger.error("Failed to add other files entry: %s", e)

    def _on_item_expanded(self, item: QTreeWidgetItem) -> None:
        """Handle tree item expand — lazy scan sub-folders on demand."""
        try:
            # Check if first child is placeholder
            if item.childCount() == 1:
                child = item.child(0)
                if (child and
                        child.data(0, Qt.ItemDataRole.UserRole) == "__placeholder__"):
                    path = item.data(0, Qt.ItemDataRole.UserRole)
                    if path and Path(path).is_dir():
                        self._start_expand_scan(item, path)
        except Exception as e:
            logger.error("Failed to handle item expand: %s", e)

    def _start_expand_scan(
            self, item: QTreeWidgetItem, path: str) -> None:
        """Start scanning sub-folders for a tree item expand."""
        try:
            # Cancel any previous expand scan
            if (self._expand_worker is not None
                    and self._expand_worker.isRunning()):
                self._scanner.cancel()
                self._expand_worker.wait(2000)

            self._expanding_item = item
            self._status_label.setText(f"Scanning: {path}...")

            self._expand_worker = ExpandScanWorker(self._scanner, path)
            self._expand_worker.finished.connect(self._on_expand_finished)
            self._expand_worker.start()
        except Exception as e:
            logger.error("Failed to start expand scan: %s", e)

    @pyqtSlot(object)
    def _on_expand_finished(self, result: Optional[FolderInfo]) -> None:
        """Handle expand scan completion — populate children."""
        try:
            item = self._expanding_item
            self._expanding_item = None

            if item is None or result is None:
                self._status_label.setText("Expand scan cancelled or failed.")
                return

            # Remove placeholder
            while item.childCount() > 0:
                item.removeChild(item.child(0))

            parent_size = item.data(1, Qt.ItemDataRole.UserRole) or 1

            # Add scanned children sorted by size (already sorted by scanner)
            for child in result.children:
                child_item = self._create_tree_item(child, parent_size)
                item.addChild(child_item)

            # Add "(Other files)" for this level
            self._add_other_files_entry(item, result, parent_size)

            # Mark as scanned
            item.setData(2, Qt.ItemDataRole.UserRole, False)

            self._status_label.setText(
                f"Expanded: {result.name} — "
                f"{len(result.children)} sub-folders")
        except Exception as e:
            logger.error("Failed to handle expand completion: %s", e)

    def _on_tree_context_menu(self, position) -> None:
        """Show context menu with 'Add to Cleanup' option."""
        try:
            item = self._tree.itemAt(position)
            if item is None:
                return

            path = item.data(0, Qt.ItemDataRole.UserRole)
            if not path or path in ("__placeholder__", "__other_files__"):
                return

            menu = QMenu(self)
            add_action = QAction("Add to Cleanup", self)
            add_action.triggered.connect(
                lambda: self._on_add_to_cleanup(path))
            menu.addAction(add_action)

            menu.exec(self._tree.viewport().mapToGlobal(position))
        except Exception as e:
            logger.error("Failed to show context menu: %s", e)

    def _on_add_to_cleanup(self, path: str) -> None:
        """Handle 'Add to Cleanup' action from context menu."""
        try:
            if is_protected_path(path):
                QMessageBox.warning(
                    self,
                    "Protected Directory",
                    f"'{path}' is a protected system directory "
                    f"and cannot be added to cleanup.",
                )
                return

            if not Path(path).is_dir():
                QMessageBox.warning(
                    self,
                    "Not a Directory",
                    f"'{path}' is not a valid directory.",
                )
                return

            self.add_to_cleanup_requested.emit(path)
            self._status_label.setText(f"Added to cleanup: {path}")
        except Exception as e:
            logger.error("Failed to add to cleanup: %s", e)

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

    def _on_item_double_clicked(
            self,
            item: QTreeWidgetItem,
            column: int) -> None:
        """Handle double-click to scan deeper (legacy support)."""
        try:
            path = item.data(0, Qt.ItemDataRole.UserRole)
            if path and path not in ("__placeholder__", "__other_files__"):
                if Path(path).is_dir():
                    self._start_scan(path, max_depth=2)
        except Exception as e:
            logger.error("Failed to handle double-click: %s", e)
