"""Storage View - Displays drive information and folder sizes (TreeSize-like)."""
import logging
from typing import Optional, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QTreeWidgetItem
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QTimer

from features.storage_monitor import DriveInfo
from features.folder_scanner import FolderScanner, FolderInfo
from ui.storage.delegates import NameColumnDelegate, PercentBarDelegate
from ui.storage.storage_view_ui import setup_ui
from ui.storage.storage_view_interactions import (
    StorageInteractionController,
    on_add_to_cleanup,
    on_delete_item,
    on_item_double_clicked,
    on_navigate_back,
    on_navigate_forward,
    on_open_file_location,
    on_refresh,
    on_tree_context_menu,
    update_drive_summary,
    update_nav_buttons,
)
from ui.storage.storage_view_scan_session import (
    ScanSessionState,
    flush_child_buffer,
    is_active_realtime_session,
    on_cancel,
    on_child_scanned,
    on_child_scanned_session,
    on_realtime_finished,
    on_realtime_finished_session,
    on_scan_progress,
    on_scan_progress_session,
    start_realtime_scan,
    start_scan,
)
from ui.storage.storage_view_expand import (
    ExpandFlowState,
    on_expand_finished,
    on_item_expanded,
    populate_expand_from_cache,
    start_expand_scan,
)
from ui.storage.workers import ExpandScanWorker, RealtimeScanWorker, ScanWorker
from ui.views.storage_view_tree import (
    COL_PERCENT as TREE_COL_PERCENT,
    ROLE_IS_ROOT,
    ROLE_PERCENT_BAR,
    add_file_entries,
    build_tree_item,
)
from ui.views.storage_view_status import build_scan_complete_text

logger = logging.getLogger(__name__)

# Backwards-compatible constant export (legacy tests import COL_PERCENT here).
COL_PERCENT = TREE_COL_PERCENT

__all__ = [
    "StorageView",
    "NameColumnDelegate",
    "PercentBarDelegate",
    "ScanWorker",
    "ExpandScanWorker",
    "RealtimeScanWorker",
    "ROLE_IS_ROOT",
    "ROLE_PERCENT_BAR",
]

# Batch / throttle constants
_BATCH_FLUSH_MS = 200       # D1: flush child buffer every 200ms


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
            self._expand_flow_state = ExpandFlowState()
            self._expand_worker_cls = ExpandScanWorker
            self._drive_total_bytes: int = 0
            self._scan_session_state = ScanSessionState()
            self._nav_history: List[str] = []
            self._nav_forward: List[str] = []
            self._current_scan_path: Optional[str] = None
            self._scan_cache: dict[str, FolderInfo] = {}
            self._full_tree_cache: Optional[FolderInfo] = None
            self._path_index: dict[str, FolderInfo] = {}
            self._interaction_controller = StorageInteractionController(self)

            # D1: Batch buffer for child scan results
            self._batch_timer = QTimer(self)
            self._batch_timer.setInterval(_BATCH_FLUSH_MS)
            self._batch_timer.timeout.connect(self._flush_child_buffer)

            # D4: Throttle progress text
            self._last_progress_text_time: float = 0.0

            self._setup_ui()
        except Exception as e:
            logger.error("Failed to init StorageView: %s", e)

    @property
    def _scan_session_seq(self) -> int:
        return self._scan_session_state.seq

    @_scan_session_seq.setter
    def _scan_session_seq(self, value: int) -> None:
        self._scan_session_state.seq = value

    @property
    def _active_scan_session_id(self) -> Optional[int]:
        return self._scan_session_state.active_session_id

    @_active_scan_session_id.setter
    def _active_scan_session_id(self, value: Optional[int]) -> None:
        self._scan_session_state.active_session_id = value

    @property
    def _realtime_cancel_pending(self) -> bool:
        return self._scan_session_state.cancel_pending

    @_realtime_cancel_pending.setter
    def _realtime_cancel_pending(self, value: bool) -> None:
        self._scan_session_state.cancel_pending = value

    @property
    def _root_item(self) -> Optional[QTreeWidgetItem]:
        return self._scan_session_state.root_item

    @_root_item.setter
    def _root_item(self, value: Optional[QTreeWidgetItem]) -> None:
        self._scan_session_state.root_item = value

    @property
    def _root_size_accumulator(self) -> int:
        return self._scan_session_state.root_size_accumulator

    @_root_size_accumulator.setter
    def _root_size_accumulator(self, value: int) -> None:
        self._scan_session_state.root_size_accumulator = value

    @property
    def _root_alloc_accumulator(self) -> int:
        return self._scan_session_state.root_alloc_accumulator

    @_root_alloc_accumulator.setter
    def _root_alloc_accumulator(self, value: int) -> None:
        self._scan_session_state.root_alloc_accumulator = value

    @property
    def _root_files_accumulator(self) -> int:
        return self._scan_session_state.root_files_accumulator

    @_root_files_accumulator.setter
    def _root_files_accumulator(self, value: int) -> None:
        self._scan_session_state.root_files_accumulator = value

    @property
    def _root_folders_accumulator(self) -> int:
        return self._scan_session_state.root_folders_accumulator

    @_root_folders_accumulator.setter
    def _root_folders_accumulator(self, value: int) -> None:
        self._scan_session_state.root_folders_accumulator = value

    @property
    def _child_buffer(self) -> List[FolderInfo]:
        return self._scan_session_state.child_buffer

    @_child_buffer.setter
    def _child_buffer(self, value: List[FolderInfo]) -> None:
        self._scan_session_state.child_buffer = value

    @property
    def _expand_worker(self) -> Optional[ExpandScanWorker]:
        return self._expand_flow_state.worker

    @_expand_worker.setter
    def _expand_worker(self, value: Optional[ExpandScanWorker]) -> None:
        self._expand_flow_state.worker = value

    @property
    def _expanding_item(self) -> Optional[QTreeWidgetItem]:
        return self._expand_flow_state.expanding_item

    @_expanding_item.setter
    def _expanding_item(self, value: Optional[QTreeWidgetItem]) -> None:
        self._expand_flow_state.expanding_item = value

    @property
    def _pending_expand_request(self) -> Optional[tuple[QTreeWidgetItem, str]]:
        return self._expand_flow_state.pending_request

    @_pending_expand_request.setter
    def _pending_expand_request(self, value: Optional[tuple[QTreeWidgetItem, str]]) -> None:
        self._expand_flow_state.pending_request = value

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        setup_ui(self)

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

    def _reset_scan_controls(self) -> None:
        """Return scan controls to their ready state."""
        self._scan_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._progress_bar.hide()
        self._tree.setSortingEnabled(True)

    def _reset_scan_buffers(self) -> None:
        """Stop buffered realtime updates and discard pending children."""
        self._batch_timer.stop()
        self._child_buffer.clear()

    def _start_realtime_scan(self, path: str) -> None:
        """Start a real-time scan that updates the tree incrementally."""
        start_realtime_scan(self, path)

    def _start_scan(self, path: str, max_depth: int = 1) -> None:
        """Start scanning a path (non-realtime, used for deeper scans)."""
        start_scan(self, path, max_depth)

    def _on_cancel(self) -> None:
        """Cancel ongoing scan."""
        on_cancel(self)

    def _is_active_realtime_session(self, session_id: int) -> bool:
        """Return True if signal belongs to the currently active scan session."""
        return is_active_realtime_session(self, session_id)

    def _on_scan_progress_session(
            self, session_id: int, current_path: str, items_scanned: int) -> None:
        """Apply progress only for the active realtime session."""
        on_scan_progress_session(self, session_id, current_path, items_scanned)

    def _on_child_scanned_session(
            self, session_id: int, child_info: FolderInfo) -> None:
        """Apply child updates only for the active realtime session."""
        on_child_scanned_session(self, session_id, child_info)

    def _on_realtime_finished_session(
            self,
            session_id: int,
            result: Optional[FolderInfo],
            path_index: Optional[dict] = None) -> None:
        """Finalize only the active realtime session; ignore stale completions."""
        on_realtime_finished_session(self, session_id, result, path_index)

    @pyqtSlot(str, int)
    def _on_scan_progress(self, current_path: str, items_scanned: int) -> None:
        """Update progress display (D4: throttle text to 500ms)."""
        on_scan_progress(self, current_path, items_scanned)

    @pyqtSlot(object)
    def _on_child_scanned(self, child_info: FolderInfo) -> None:
        """Buffer child scan result for batched UI update (D1)."""
        on_child_scanned(self, child_info)

    def _flush_child_buffer(self) -> None:
        """Flush buffered children into tree in one batch (D1, D2)."""
        flush_child_buffer(self)

    @pyqtSlot(object, object)
    def _on_realtime_finished(self, result: Optional[FolderInfo],
                              path_index: Optional[dict] = None) -> None:
        """Handle realtime scan completion."""
        on_realtime_finished(self, result, path_index)

    @staticmethod
    def _build_scan_complete_text(result: FolderInfo) -> str:
        """Bridge for backwards-compatible call sites during extraction."""
        return build_scan_complete_text(result)

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
        on_item_expanded(self, item, Path)

    def _populate_expand_from_cache(
            self, item: QTreeWidgetItem, cached: FolderInfo) -> None:
        """Populate expanded item children from cache (D2: batched)."""
        populate_expand_from_cache(self, item, cached)

    def _start_expand_scan(
            self, item: QTreeWidgetItem, path: str) -> None:
        """Start scanning sub-folders for a tree item expand."""
        start_expand_scan(self, item, path)

    @pyqtSlot(object)
    def _on_expand_finished(self, result: Optional[FolderInfo]) -> None:
        """Handle expand scan completion - populate children (D2: batched)."""
        on_expand_finished(self, result)

    def _on_tree_context_menu(self, position) -> None:
        """Show context menu for the selected file system item."""
        on_tree_context_menu(self, position)

    def _on_add_to_cleanup(self, path: str) -> None:
        """Handle 'Add to Cleanup' action from context menu."""
        on_add_to_cleanup(self, path)

    def _on_delete_item(
        self,
        path: str,
        item: Optional[QTreeWidgetItem] = None,
    ) -> None:
        """Move the selected file or folder to the Recycle Bin."""
        on_delete_item(self, path, item)

    def _on_open_file_location(self, path: str) -> None:
        """Open Explorer and select the file or folder."""
        on_open_file_location(self, path)

    def _update_drive_summary(self) -> None:
        """Update the drive summary display with capacity bars."""
        update_drive_summary(self)

    def _on_refresh(self) -> None:
        """Handle refresh button click."""
        on_refresh(self)

    def _on_item_double_clicked(
            self,
            item: QTreeWidgetItem,
            column: int) -> None:
        """Handle double-click to navigate into subfolder."""
        on_item_double_clicked(self, item, column)

    def _on_navigate_back(self) -> None:
        """Navigate back to the previous folder (cached if available)."""
        on_navigate_back(self)

    def _on_navigate_forward(self) -> None:
        """Navigate forward to the next folder (cached if available)."""
        on_navigate_forward(self)

    def _update_nav_buttons(self) -> None:
        """Update enabled state of back/forward buttons."""
        update_nav_buttons(self)
