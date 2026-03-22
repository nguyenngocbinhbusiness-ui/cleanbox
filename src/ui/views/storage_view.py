"""Storage View - Displays drive information and folder sizes (TreeSize-like)."""
import logging
import time
from typing import Optional, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QHeaderView, QProgressBar, QLabel, QFrame, QPushButton, QComboBox,
    QMenu, QMessageBox, QStyledItemDelegate, QStyleOptionViewItem,
    QStyle, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot, QRect, QTimer
from PyQt6.QtGui import (
    QFont, QAction, QColor, QLinearGradient,
    QPalette, QIcon
)

from features.storage_monitor import DriveInfo
from features.folder_scanner import FolderScanner, FolderInfo, format_size
from shared.utils import is_protected_path
from ui.views.storage_view_actions import (
    open_file_location,
    recycle_path,
)
from ui.views.storage_view_tree import (
    COL_ALLOCATED,
    COL_FILES,
    COL_FOLDERS,
    COL_NAME,
    COL_PERCENT,
    COL_SIZE,
    NUM_COLUMNS,
    ROLE_IS_ROOT,
    ROLE_PERCENT_BAR,
    _BOLD_FONT,
    _ROOT_BG_BRUSH,
    NumericSortItem,
    _get_generic_folder_icon,
    add_file_entries,
    build_tree_item,
)

logger = logging.getLogger(__name__)

# Batch / throttle constants
_BATCH_FLUSH_MS = 200       # D1: flush child buffer every 200ms
_PROGRESS_TEXT_MS = 0.5     # D4: throttle progress text updates to 500ms


class NameColumnDelegate(QStyledItemDelegate):
    """Custom delegate for Name column with yellow size-proportional bar."""

    def paint(self, painter, option, index):
        """Paint yellow bar background then icon + text."""
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        painter.save()
        painter.setClipRect(opt.rect)

        # Base background
        is_root = index.data(ROLE_IS_ROOT)
        if is_root:
            painter.fillRect(opt.rect, QColor("#E8F0FE"))

        # Yellow bar proportional to percent of parent
        if not (opt.state & QStyle.StateFlag.State_Selected):
            percent = index.data(ROLE_PERCENT_BAR) or 0.0
            if percent > 0:
                bar_w = max(1, int(
                    opt.rect.width() * min(percent, 100) / 100))
                bar_rect = QRect(
                    opt.rect.x(), opt.rect.y(),
                    bar_w, opt.rect.height())
                gradient = QLinearGradient(
                    bar_rect.left(), 0, bar_rect.right(), 0)
                gradient.setColorAt(0, QColor(255, 220, 80, 180))
                gradient.setColorAt(1, QColor(255, 190, 40, 140))
                painter.fillRect(bar_rect, gradient)

        # Selection highlight
        if opt.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(opt.rect, opt.palette.highlight())

        # Icon
        icon_x = opt.rect.x() + 2
        icon_size = opt.decorationSize
        icon_y = opt.rect.y() + (opt.rect.height() - icon_size.height()) // 2
        text_x = opt.rect.x() + 4
        if not opt.icon.isNull():
            mode = QIcon.Mode.Normal
            if opt.state & QStyle.StateFlag.State_Selected:
                mode = QIcon.Mode.Selected
            opt.icon.paint(
                painter, icon_x, icon_y,
                icon_size.width(), icon_size.height(),
                Qt.AlignmentFlag.AlignCenter, mode)
            text_x = icon_x + icon_size.width() + 4

        # Text
        text_rect = QRect(
            text_x, opt.rect.y(),
            opt.rect.right() - text_x, opt.rect.height())
        if opt.state & QStyle.StateFlag.State_Selected:
            painter.setPen(opt.palette.color(
                QPalette.ColorRole.HighlightedText))
        else:
            painter.setPen(opt.palette.color(QPalette.ColorRole.Text))
        painter.setFont(opt.font)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            opt.text)

        painter.restore()


class PercentBarDelegate(QStyledItemDelegate):
    """Custom delegate for % of Parent column with gradient bar."""

    def paint(self, painter, option, index):
        """Paint purple gradient bar with percent text overlay."""
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        painter.save()
        painter.setClipRect(opt.rect)

        # White base
        painter.fillRect(opt.rect, QColor(255, 255, 255))

        # Gradient bar proportional to percent
        percent = index.data(Qt.ItemDataRole.UserRole) or 0.0
        if percent > 0:
            bar_w = max(1, int(
                opt.rect.width() * min(percent, 100) / 100))
            bar_rect = QRect(
                opt.rect.x(), opt.rect.y(),
                bar_w, opt.rect.height())
            gradient = QLinearGradient(
                bar_rect.left(), 0, bar_rect.right(), 0)
            gradient.setColorAt(0, QColor(160, 150, 220, 200))
            gradient.setColorAt(1, QColor(120, 100, 200, 220))
            painter.fillRect(bar_rect, gradient)

        # Selection highlight
        if opt.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(opt.rect, opt.palette.highlight())
            painter.setPen(opt.palette.color(
                QPalette.ColorRole.HighlightedText))
        else:
            painter.setPen(QColor(0, 0, 0))

        # Text
        painter.setFont(opt.font)
        text = f"{percent:.1f} %" if percent > 0 else opt.text
        painter.drawText(
            opt.rect.adjusted(0, 0, -4, 0),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            text)

        painter.restore()


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


class RealtimeScanWorker(QThread):
    """Worker thread that emits per-child results for real-time UI updates."""

    child_scanned = pyqtSignal(object)  # FolderInfo for one child
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(object, object)  # (root FolderInfo, path_index dict)

    def __init__(self, scanner: FolderScanner, path: str):
        """Initialize realtime scan worker."""
        try:
            super().__init__()
            self.scanner = scanner
            self.path = path
        except Exception as e:
            logger.error("Failed to init RealtimeScanWorker: %s", e)

    def run(self):
        """Scan children and emit each as completed."""
        try:
            result = self.scanner.scan_children_realtime(
                self.path,
                child_callback=self._on_child,
                progress_callback=self._on_progress,
            )
            # D5: Build path index on worker thread to avoid blocking UI
            path_index = {}
            if result is not None:
                self._build_index(result, path_index)
            self.finished.emit(result, path_index)
        except Exception as e:
            logger.error("Realtime scan worker failed: %s", e)
            self.finished.emit(None, {})

    @staticmethod
    def _build_index(node: FolderInfo, index: dict) -> None:
        """Build flat path→FolderInfo index (D5: off main thread)."""
        stack = [node]
        while stack:
            n = stack.pop()
            index[n.path] = n
            stack.extend(n.children)

    def _on_child(self, child_info: FolderInfo):
        """Emit child_scanned signal."""
        try:
            self.child_scanned.emit(child_info)
        except Exception as e:
            logger.error("Failed to emit child_scanned: %s", e)

    def _on_progress(self, current_path: str, items_scanned: int):
        """Emit progress signal."""
        try:
            self.progress.emit(current_path, items_scanned)
        except Exception as e:
            logger.error("Failed to emit realtime progress: %s", e)


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
            self._realtime_worker: Optional[RealtimeScanWorker] = None
            self._expand_worker: Optional[ExpandScanWorker] = None
            self._expanding_item: Optional[QTreeWidgetItem] = None
            self._drive_total_bytes: int = 0
            self._root_item: Optional[QTreeWidgetItem] = None
            self._root_size_accumulator: int = 0
            self._root_alloc_accumulator: int = 0
            self._root_files_accumulator: int = 0
            self._root_folders_accumulator: int = 0
            self._nav_history: List[str] = []
            self._nav_forward: List[str] = []
            self._current_scan_path: Optional[str] = None
            self._scan_cache: dict[str, FolderInfo] = {}
            self._full_tree_cache: Optional[FolderInfo] = None
            self._path_index: dict[str, FolderInfo] = {}
            self._scan_session_seq: int = 0
            self._active_scan_session_id: Optional[int] = None

            # D1: Batch buffer for child scan results
            self._child_buffer: List[FolderInfo] = []
            self._batch_timer = QTimer(self)
            self._batch_timer.setInterval(_BATCH_FLUSH_MS)
            self._batch_timer.timeout.connect(self._flush_child_buffer)

            # D4: Throttle progress text
            self._last_progress_text_time: float = 0.0

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

            # Back/Forward navigation buttons
            self._back_btn = QPushButton("◀ Back")
            self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._back_btn.clicked.connect(self._on_navigate_back)
            self._back_btn.setEnabled(False)
            self._back_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F0F0F0;
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #E0E0E0; }
                QPushButton:disabled { color: #AAAAAA; }
            """)
            drive_layout.addWidget(self._back_btn)

            self._forward_btn = QPushButton("Forward ▶")
            self._forward_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._forward_btn.clicked.connect(self._on_navigate_forward)
            self._forward_btn.setEnabled(False)
            self._forward_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F0F0F0;
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #E0E0E0; }
                QPushButton:disabled { color: #AAAAAA; }
            """)
            drive_layout.addWidget(self._forward_btn)

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
            self._status_label.setWordWrap(True)
            self._status_label.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            self._status_label.setMaximumHeight(
                self._status_label.fontMetrics().lineSpacing() * 2 + 4
            )
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

            # Tree widget for folder sizes - TreeSize-like columns
            self._tree = QTreeWidget()
            self._tree.setHeaderLabels([
                "Name", "Size", "Allocated", "Files",
                "Folders", "% of Parent (Size)"
            ])
            self._tree.setAlternatingRowColors(True)
            self._tree.setRootIsDecorated(True)
            self._tree.setSortingEnabled(True)
            self._tree.sortByColumn(COL_PERCENT, Qt.SortOrder.DescendingOrder)

            # Column widths – Interactive resize so users can drag to see full content
            header = self._tree.header()
            header.setSectionResizeMode(
                COL_NAME, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(
                COL_SIZE, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(
                COL_ALLOCATED, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(
                COL_FILES, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(
                COL_FOLDERS, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(
                COL_PERCENT, QHeaderView.ResizeMode.Interactive)
            header.setStretchLastSection(True)
            # Sensible default widths
            header.resizeSection(COL_NAME, 260)
            header.resizeSection(COL_SIZE, 90)
            header.resizeSection(COL_ALLOCATED, 90)
            header.resizeSection(COL_FILES, 80)
            header.resizeSection(COL_FOLDERS, 80)
            header.resizeSection(COL_PERCENT, 130)

            # Custom delegates for Name and % columns
            self._name_delegate = NameColumnDelegate(self._tree)
            self._tree.setItemDelegateForColumn(
                COL_NAME, self._name_delegate)
            self._percent_delegate = PercentBarDelegate(self._tree)
            self._tree.setItemDelegateForColumn(
                COL_PERCENT, self._percent_delegate)

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

            # Double-click to navigate into subfolder
            self._tree.itemDoubleClicked.connect(
                self._on_item_double_clicked)

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
                label = (
                    f"{drive.letter} ({drive.free_gb:.1f} GB free "
                    f"of {drive.total_gb:.1f} GB)")
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
            # Reset navigation when scanning a new drive
            self._nav_history.clear()
            self._nav_forward.clear()
            self._scan_cache.clear()
            self._full_tree_cache = None
            self._path_index.clear()
            self._current_scan_path = path
            self._update_nav_buttons()
            self._start_realtime_scan(path)
        except Exception as e:
            logger.error("Failed to start scan: %s", e)

    def _start_realtime_scan(self, path: str) -> None:
        """Start a real-time scan that updates the tree incrementally."""
        try:
            self._scan_session_seq += 1
            session_id = self._scan_session_seq
            self._active_scan_session_id = session_id
            self._batch_timer.stop()
            self._child_buffer.clear()
            self._tree.clear()
            self._tree.setSortingEnabled(False)
            self._scan_btn.setEnabled(False)
            self._cancel_btn.setEnabled(True)
            self._progress_bar.show()
            self._progress_bar.setValue(0)
            self._status_label.setText(f"Scanning {path}...")

            # Reset accumulators
            self._root_size_accumulator = 0
            self._root_alloc_accumulator = 0
            self._root_files_accumulator = 0
            self._root_folders_accumulator = 0

            # Create root item
            self._root_item = NumericSortItem()
            self._root_item.setText(
                COL_NAME, f"Scanning...   {path}")
            self._root_item.setText(COL_SIZE, "Scanning...")
            self._root_item.setText(COL_ALLOCATED, "...")
            self._root_item.setText(COL_FILES, "...")
            self._root_item.setText(COL_FOLDERS, "...")
            self._root_item.setText(COL_PERCENT, "100.0 %")
            self._root_item.setData(
                COL_NAME, Qt.ItemDataRole.UserRole, path)
            self._root_item.setData(
                COL_NAME, ROLE_PERCENT_BAR, 100.0)
            self._root_item.setData(
                COL_NAME, ROLE_IS_ROOT, True)
            self._root_item.setData(
                COL_SIZE, Qt.ItemDataRole.UserRole, 0)
            self._root_item.setData(
                COL_PERCENT, Qt.ItemDataRole.UserRole, 100.0)

            # Drive icon (D3: use generic for speed)
            self._root_item.setIcon(COL_NAME, _get_generic_folder_icon())

            # D8: Cached font/brush
            for col in range(NUM_COLUMNS):
                self._root_item.setFont(col, _BOLD_FONT)
            for col in (COL_SIZE, COL_ALLOCATED, COL_FILES,
                        COL_FOLDERS):
                self._root_item.setBackground(col, _ROOT_BG_BRUSH)

            self._tree.addTopLevelItem(self._root_item)
            self._root_item.setExpanded(True)

            # Start realtime worker
            self._realtime_worker = RealtimeScanWorker(
                self._scanner, path)
            self._realtime_worker.child_scanned.connect(
                lambda child, sid=session_id:
                self._on_child_scanned_session(sid, child))
            self._realtime_worker.progress.connect(
                lambda current_path, items_scanned, sid=session_id:
                self._on_scan_progress_session(sid, current_path, items_scanned))
            self._realtime_worker.finished.connect(
                lambda result, path_index, sid=session_id:
                self._on_realtime_finished_session(sid, result, path_index))
            self._realtime_worker.start()
        except Exception as e:
            logger.error("Failed to start realtime scan: %s", e)
            self._scan_btn.setEnabled(True)

    def _start_scan(self, path: str, max_depth: int = 1) -> None:
        """Start scanning a path (non-realtime, used for deeper scans)."""
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
            self._active_scan_session_id = None
            self._batch_timer.stop()
            self._child_buffer.clear()
            self._cancel_btn.setEnabled(False)
            self._status_label.setText("Cancelling...")
        except Exception as e:
            logger.error("Failed to cancel scan: %s", e)

    def _is_active_realtime_session(self, session_id: int) -> bool:
        """Return True if signal belongs to the currently active scan session."""
        return (
            self._active_scan_session_id is not None
            and session_id == self._active_scan_session_id
        )

    def _on_scan_progress_session(
            self, session_id: int, current_path: str, items_scanned: int) -> None:
        """Apply progress only for the active realtime session."""
        if not self._is_active_realtime_session(session_id):
            return
        self._on_scan_progress(current_path, items_scanned)

    def _on_child_scanned_session(
            self, session_id: int, child_info: FolderInfo) -> None:
        """Apply child updates only for the active realtime session."""
        if not self._is_active_realtime_session(session_id):
            return
        self._on_child_scanned(child_info)

    def _on_realtime_finished_session(
            self,
            session_id: int,
            result: Optional[FolderInfo],
            path_index: Optional[dict] = None) -> None:
        """Finalize only the active realtime session; ignore stale completions."""
        if not self._is_active_realtime_session(session_id):
            return
        self._on_realtime_finished(result, path_index)
        self._active_scan_session_id = None

    @pyqtSlot(str, int)
    def _on_scan_progress(self, current_path: str, items_scanned: int) -> None:
        """Update progress display (D4: throttle text to 500ms)."""
        try:
            self._progress_bar.setValue(items_scanned)
            # D4: Only update text label every 500ms to reduce repaints
            now = time.monotonic()
            if now - self._last_progress_text_time >= _PROGRESS_TEXT_MS:
                self._last_progress_text_time = now
                if len(current_path) > 50:
                    display_path = "..." + current_path[-47:]
                else:
                    display_path = current_path
                self._status_label.setText(f"Scanning: {display_path}")
        except Exception as e:
            logger.error("Failed to update scan progress: %s", e)

    @pyqtSlot(object)
    def _on_child_scanned(self, child_info: FolderInfo) -> None:
        """Buffer child scan result for batched UI update (D1)."""
        try:
            if self._root_item is None:
                return

            # Update accumulators immediately (lightweight)
            self._root_size_accumulator += child_info.size_bytes
            self._root_alloc_accumulator += child_info.allocated_bytes
            self._root_files_accumulator += child_info.file_count
            self._root_folders_accumulator += child_info.folder_count

            # Buffer for batched tree insert
            self._child_buffer.append(child_info)

            # Start flush timer if not already running
            if not self._batch_timer.isActive():
                self._batch_timer.start()
        except Exception as e:
            logger.error("Failed to handle child scan: %s", e)

    def _flush_child_buffer(self) -> None:
        """Flush buffered children into tree in one batch (D1, D2)."""
        try:
            if self._active_scan_session_id is None:
                self._child_buffer.clear()
                self._batch_timer.stop()
                return
            if not self._child_buffer or self._root_item is None:
                self._batch_timer.stop()
                return

            batch = self._child_buffer[:]
            self._child_buffer.clear()
            self._batch_timer.stop()

            reference_size = self._drive_total_bytes or 1

            # D2: Suppress repaints during bulk insert
            try:
                self._tree.setUpdatesEnabled(False)
                for child_info in batch:
                    child_item = self._create_tree_item(
                        child_info, reference_size)
                    self._root_item.addChild(child_item)

                # Update root item totals once
                root_path = self._root_item.data(
                    COL_NAME, Qt.ItemDataRole.UserRole) or ""
                root_size_str = format_size(self._root_size_accumulator)
                self._root_item.setText(
                    COL_NAME, f"{root_size_str}   {root_path}")
                self._root_item.setText(COL_SIZE, root_size_str)
                self._root_item.setText(
                    COL_ALLOCATED,
                    format_size(self._root_alloc_accumulator))
                self._root_item.setText(
                    COL_FILES, f"{self._root_files_accumulator:,}")
                self._root_item.setText(
                    COL_FOLDERS, f"{self._root_folders_accumulator:,}")
                self._root_item.setData(
                    COL_SIZE, Qt.ItemDataRole.UserRole,
                    self._root_size_accumulator)
            finally:
                # D2: Always re-enable updates
                self._tree.setUpdatesEnabled(True)

            if batch:
                last = batch[-1]
                self._status_label.setText(
                    f"Scanned: {last.name} "
                    f"({last.size_formatted()})")
        except Exception as e:
            logger.error("Failed to flush child buffer: %s", e)

    @pyqtSlot(object, object)
    def _on_realtime_finished(self, result: Optional[FolderInfo],
                              path_index: Optional[dict] = None) -> None:
        """Handle realtime scan completion."""
        try:
            # D1: Flush any remaining buffered children
            self._batch_timer.stop()
            if self._child_buffer:
                self._flush_child_buffer()

            self._scan_btn.setEnabled(True)
            self._cancel_btn.setEnabled(False)
            self._progress_bar.hide()

            if result is None:
                self._status_label.setText("Scan cancelled or failed.")
                self._tree.setSortingEnabled(True)
                return

            # D2: Batch all final updates with repaints suppressed
            try:
                self._tree.setUpdatesEnabled(False)
                # Update root item with final data
                if self._root_item:
                    root_path = self._root_item.data(
                        COL_NAME, Qt.ItemDataRole.UserRole) or ""
                    self._root_item.setText(
                        COL_NAME,
                        f"{result.size_formatted()}   {root_path}")
                    self._root_item.setText(
                        COL_SIZE, result.size_formatted())
                    self._root_item.setText(
                        COL_ALLOCATED, result.allocated_formatted())
                    self._root_item.setText(
                        COL_FILES,
                        f"{result.file_count:,}" if result.file_count else "-")
                    self._root_item.setText(
                        COL_FOLDERS,
                        f"{result.folder_count:,}" if result.folder_count else "-")
                    self._root_item.setText(COL_PERCENT, "100.0 %")
                    self._root_item.setData(
                        COL_SIZE, Qt.ItemDataRole.UserRole, result.size_bytes)

                    # Recalculate children % using parent's actual scanned size
                    parent_size = result.size_bytes or 1
                    for i in range(self._root_item.childCount()):
                        child_item = self._root_item.child(i)
                        if child_item:
                            child_size = child_item.data(
                                COL_SIZE, Qt.ItemDataRole.UserRole)
                            if child_size is not None and parent_size > 0:
                                percent = (child_size / parent_size) * 100
                                child_item.setText(
                                    COL_PERCENT, f"{percent:.1f} %")
                                child_item.setData(
                                    COL_PERCENT, Qt.ItemDataRole.UserRole,
                                    percent)
                                child_item.setData(
                                    COL_NAME, ROLE_PERCENT_BAR, percent)

                    # Add grouped file entries for root-level files
                    self._add_file_entries(
                        self._root_item, result,
                        result.size_bytes or 1)
            finally:
                # D2: Always re-enable
                self._tree.setUpdatesEnabled(True)

            self._tree.setSortingEnabled(True)

            # Cache result for back/forward navigation
            if self._current_scan_path:
                # Limit cache to 20 entries
                if len(self._scan_cache) >= 20:
                    oldest_key = next(iter(self._scan_cache))
                    del self._scan_cache[oldest_key]
                self._scan_cache[self._current_scan_path] = result

                # D5: Use pre-built index from worker thread
                self._full_tree_cache = result
                self._path_index = path_index if path_index else {}

            self._status_label.setText(
                self._build_scan_complete_text(result))
        except Exception as e:
            logger.error("Failed to handle realtime scan completion: %s", e)

    @staticmethod
    def _build_scan_complete_text(result: FolderInfo) -> str:
        """Build completion text and include completeness accounting when present."""
        base = (
            f"Scan complete: {result.size_formatted()} in "
            f"{result.file_count:,} files, "
            f"{result.folder_count:,} folders"
        )

        stats = getattr(result, "scan_stats", None)
        if stats is None:
            return base

        scanned_files = getattr(stats, "scanned_files", None)
        scanned_dirs = getattr(stats, "scanned_dirs", None)
        skipped = getattr(stats, "skipped_count", None)
        reasons = getattr(stats, "skipped_reasons", None)

        parts = []
        if isinstance(scanned_files, int):
            parts.append(f"scanned_files={scanned_files}")
        if isinstance(scanned_dirs, int):
            parts.append(f"scanned_dirs={scanned_dirs}")
        if isinstance(skipped, int):
            parts.append(f"skipped={skipped}")
        if isinstance(reasons, dict) and reasons:
            reason_items = [f"{k}:{v}" for k, v in sorted(reasons.items())]
            extra_count = max(0, len(reason_items) - 2)
            compact_reasons = ", ".join(reason_items[:2])
            if extra_count:
                compact_reasons += f", +{extra_count} more"
            parts.append(f"skip_reasons={compact_reasons}")

        if not parts:
            return base
        return f"{base}\n{'; '.join(parts)}"

    @pyqtSlot(object)
    def _on_scan_finished(self, result: Optional[FolderInfo]) -> None:
        """Handle scan completion (non-realtime)."""
        try:
            self._scan_btn.setEnabled(True)
            self._cancel_btn.setEnabled(False)
            self._progress_bar.hide()

            if result is None:
                self._status_label.setText("Scan cancelled or failed.")
                return

            self._status_label.setText(
                self._build_scan_complete_text(result))

            # Cache result for back/forward navigation
            if self._current_scan_path:
                if len(self._scan_cache) >= 20:
                    oldest_key = next(iter(self._scan_cache))
                    del self._scan_cache[oldest_key]
                self._scan_cache[self._current_scan_path] = result

            # Populate tree
            self._populate_tree(result)
        except Exception as e:
            logger.error("Failed to handle scan completion: %s", e)

    def _populate_tree(self, folder_info: FolderInfo) -> None:
        """Populate tree widget with folder data (D2: batched)."""
        try:
            self._tree.setUpdatesEnabled(False)
            self._tree.setSortingEnabled(False)
            try:
                self._tree.clear()

                # Use the scanned folder's own size as reference for 100%
                reference_size = folder_info.size_bytes or 1

                # Add root item (the drive itself = 100%)
                root_item = self._create_tree_item(
                    folder_info, reference_size, is_root=True)
                self._tree.addTopLevelItem(root_item)
                root_item.setExpanded(True)
            finally:
                self._tree.setSortingEnabled(True)
                self._tree.setUpdatesEnabled(True)
        except Exception as e:
            logger.error("Failed to populate tree: %s", e)

    def _create_tree_item(
        self,
        folder_info: FolderInfo,
        reference_size: int,
        is_root: bool = False,
    ) -> QTreeWidgetItem:
        """Create a tree item from FolderInfo."""
        return build_tree_item(folder_info, reference_size, is_root=is_root)

    def _add_file_entries(
        self,
        parent_item: QTreeWidgetItem,
        folder_info: FolderInfo,
        reference_size: int,
    ) -> None:
        """Add grouped file entries under a folder tree item."""
        add_file_entries(parent_item, folder_info, reference_size)

    def _on_item_expanded(self, item: QTreeWidgetItem) -> None:
        """Handle tree item expand - use cache or lazy scan sub-folders."""
        try:
            # Check if first child is placeholder
            if item.childCount() == 1:
                child = item.child(0)
                if (child and
                        child.data(
                            COL_NAME,
                            Qt.ItemDataRole.UserRole) == "__placeholder__"):
                    path = item.data(COL_NAME, Qt.ItemDataRole.UserRole)
                    if path and Path(path).is_dir():
                        # Try cache first for instant expand
                        cached = self._path_index.get(path)
                        if cached and cached.children:
                            self._populate_expand_from_cache(item, cached)
                        else:
                            self._start_expand_scan(item, path)
        except Exception as e:
            logger.error("Failed to handle item expand: %s", e)

    def _populate_expand_from_cache(
            self, item: QTreeWidgetItem, cached: FolderInfo) -> None:
        """Populate expanded item children from cache (D2: batched)."""
        try:
            self._tree.setUpdatesEnabled(False)
            try:
                # Remove placeholder
                while item.childCount() > 0:
                    item.removeChild(item.child(0))

                parent_size = item.data(
                    COL_SIZE, Qt.ItemDataRole.UserRole) or 1

                for child in cached.children:
                    child_item = self._create_tree_item(child, parent_size)
                    item.addChild(child_item)

                self._add_file_entries(item, cached, parent_size)

                item.setData(
                    COL_ALLOCATED, Qt.ItemDataRole.UserRole, False)
            finally:
                self._tree.setUpdatesEnabled(True)

            self._status_label.setText(
                f"Expanded (cached): {cached.name} — "
                f"{len(cached.children)} sub-folders")
        except Exception as e:
            logger.error("Failed to populate from cache: %s", e)

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
        """Handle expand scan completion - populate children (D2: batched)."""
        try:
            item = self._expanding_item
            self._expanding_item = None

            if item is None or result is None:
                self._status_label.setText("Expand scan cancelled or failed.")
                return

            self._tree.setUpdatesEnabled(False)
            try:
                # Remove placeholder
                while item.childCount() > 0:
                    item.removeChild(item.child(0))

                parent_size = item.data(
                    COL_SIZE, Qt.ItemDataRole.UserRole) or 1

                for child in result.children:
                    child_item = self._create_tree_item(child, parent_size)
                    item.addChild(child_item)

                self._add_file_entries(item, result, parent_size)

                item.setData(
                    COL_ALLOCATED, Qt.ItemDataRole.UserRole, False)
            finally:
                self._tree.setUpdatesEnabled(True)

            self._status_label.setText(
                f"Expanded: {result.name} \u2014 "
                f"{len(result.children)} sub-folders")
        except Exception as e:
            logger.error("Failed to handle expand completion: %s", e)

    def _on_tree_context_menu(self, position) -> None:
        """Show context menu for the selected file system item."""
        try:
            item = self._tree.itemAt(position)
            if item is None:
                return

            path = item.data(COL_NAME, Qt.ItemDataRole.UserRole)
            if not path or path in (
                    "__placeholder__", "__other_files__",
                    "__files_group__"):
                return

            menu = QMenu(self)
            add_action = QAction("Add to Cleanup", self)
            add_action.triggered.connect(
                lambda: self._on_add_to_cleanup(path))
            menu.addAction(add_action)

            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(
                lambda: self._on_delete_item(path, item))
            menu.addAction(delete_action)

            open_location_action = QAction("Open file location", self)
            open_location_action.triggered.connect(
                lambda: self._on_open_file_location(path))
            menu.addAction(open_location_action)

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

    def _on_delete_item(
        self,
        path: str,
        item: Optional[QTreeWidgetItem] = None,
    ) -> None:
        """Move the selected file or folder to the Recycle Bin."""
        try:
            if is_protected_path(path):
                QMessageBox.warning(
                    self,
                    "Protected Path",
                    f"'{path}' is a protected system path and cannot be deleted.",
                )
                return

            target = Path(path)
            if not target.exists():
                QMessageBox.information(
                    self,
                    "Item Not Found",
                    f"'{path}' no longer exists.",
                )
                return

            result = QMessageBox.warning(
                self,
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
                    index = self._tree.indexOfTopLevelItem(item)
                    if index >= 0:
                        self._tree.takeTopLevelItem(index)

            self._status_label.setText(f"Deleted: {path}")
        except Exception as e:
            logger.error("Failed to delete item: %s", e)
            QMessageBox.warning(self, "Delete Failed", f"Failed to delete '{path}': {e}")

    def _on_open_file_location(self, path: str) -> None:
        """Open Explorer and select the file or folder."""
        try:
            open_file_location(path)
            self._status_label.setText(f"Opened file location: {path}")
        except FileNotFoundError:
            QMessageBox.information(
                self,
                "Item Not Found",
                f"'{path}' no longer exists.",
            )
        except Exception as e:
            logger.error("Failed to open file location: %s", e)
            QMessageBox.warning(
                self,
                "Open Location Failed",
                f"Failed to open file location for '{path}': {e}",
            )

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
                used_percent = int(
                    (used_gb / drive.total_gb * 100)
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
                drive_label.setStyleSheet(
                    "font-weight: bold; color: #333333;")
                row_layout.addWidget(drive_label)

                # Progress bar
                progress = QProgressBar()
                progress.setValue(used_percent)
                progress.setTextVisible(True)
                progress.setFormat(
                    f"Free: {drive.free_gb:.1f} GB | "
                    f"Used: {used_gb:.1f} GB | "
                    f"Total: {drive.total_gb:.1f} GB")
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
        """Handle double-click to navigate into subfolder."""
        try:
            path = item.data(COL_NAME, Qt.ItemDataRole.UserRole)
            if path and path not in (
                    "__placeholder__", "__other_files__",
                    "__files_group__"):
                if Path(path).is_dir():
                    # Push current path to history for back navigation
                    if self._current_scan_path:
                        self._nav_history.append(self._current_scan_path)
                        self._nav_forward.clear()
                    self._current_scan_path = path
                    self._update_nav_buttons()

                    # Use full tree cache for instant navigation
                    cached = self._path_index.get(path)
                    if cached:
                        self._populate_tree(cached)
                        self._status_label.setText(
                            f"Navigated: {cached.size_formatted()} in "
                            f"{cached.file_count:,} files, "
                            f"{cached.folder_count:,} folders")
                    else:
                        self._start_realtime_scan(path)
        except Exception as e:
            logger.error("Failed to handle double-click: %s", e)

    def _on_navigate_back(self) -> None:
        """Navigate back to the previous folder (cached if available)."""
        try:
            if not self._nav_history:
                return
            if self._current_scan_path:
                self._nav_forward.append(self._current_scan_path)
            prev_path = self._nav_history.pop()
            self._current_scan_path = prev_path
            self._update_nav_buttons()

            # Use cache if available for instant navigation
            cached = self._path_index.get(prev_path) or self._scan_cache.get(prev_path)
            if cached:
                self._populate_tree(cached)
                self._status_label.setText(
                    f"Navigated back: {cached.size_formatted()} in "
                    f"{cached.file_count:,} files, "
                    f"{cached.folder_count:,} folders")
            else:
                self._start_realtime_scan(prev_path)
        except Exception as e:
            logger.error("Failed to navigate back: %s", e)

    def _on_navigate_forward(self) -> None:
        """Navigate forward to the next folder (cached if available)."""
        try:
            if not self._nav_forward:
                return
            if self._current_scan_path:
                self._nav_history.append(self._current_scan_path)
            next_path = self._nav_forward.pop()
            self._current_scan_path = next_path
            self._update_nav_buttons()

            # Use cache if available for instant navigation
            cached = self._path_index.get(next_path) or self._scan_cache.get(next_path)
            if cached:
                self._populate_tree(cached)
                self._status_label.setText(
                    f"Navigated forward: {cached.size_formatted()} in "
                    f"{cached.file_count:,} files, "
                    f"{cached.folder_count:,} folders")
            else:
                self._start_realtime_scan(next_path)
        except Exception as e:
            logger.error("Failed to navigate forward: %s", e)

    def _update_nav_buttons(self) -> None:
        """Update enabled state of back/forward buttons."""
        try:
            self._back_btn.setEnabled(len(self._nav_history) > 0)
            self._forward_btn.setEnabled(len(self._nav_forward) > 0)
        except Exception as e:
            logger.error("Failed to update nav buttons: %s", e)
