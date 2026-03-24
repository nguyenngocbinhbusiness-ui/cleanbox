"""Scan session orchestration helpers for StorageView."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from PyQt6.QtCore import Qt

from features.folder_scanner import FolderInfo
from ui.storage.workers import RealtimeScanWorker, ScanWorker
from ui.views.storage_view_realtime_finish import (
    build_scanned_status_text,
    cache_scan_result,
    update_child_percentages,
    update_root_item_from_accumulators,
    update_root_item_from_result,
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
    NumericSortItem,
    _BOLD_FONT,
    _ROOT_BG_BRUSH,
    _get_generic_folder_icon,
)

logger = logging.getLogger(__name__)
_PROGRESS_TEXT_MS = 0.5


@dataclass
class ScanSessionState:
    """Mutable realtime scan state owned by StorageView."""

    seq: int = 0
    active_session_id: Optional[int] = None
    cancel_pending: bool = False
    root_item: Optional[NumericSortItem] = None
    root_size_accumulator: int = 0
    root_alloc_accumulator: int = 0
    root_files_accumulator: int = 0
    root_folders_accumulator: int = 0
    child_buffer: list[FolderInfo] = field(default_factory=list)


def _state(view) -> ScanSessionState:
    state = getattr(view, "_scan_session_state", None)
    if state is not None:
        return state

    return ScanSessionState(
        seq=getattr(view, "_scan_session_seq", 0),
        active_session_id=getattr(view, "_active_scan_session_id", None),
        cancel_pending=getattr(view, "_realtime_cancel_pending", False),
        root_item=getattr(view, "_root_item", None),
        root_size_accumulator=getattr(view, "_root_size_accumulator", 0),
        root_alloc_accumulator=getattr(view, "_root_alloc_accumulator", 0),
        root_files_accumulator=getattr(view, "_root_files_accumulator", 0),
        root_folders_accumulator=getattr(view, "_root_folders_accumulator", 0),
        child_buffer=getattr(view, "_child_buffer", []),
    )


def start_realtime_scan(view, path: str) -> None:
    """Start a real-time scan that updates the tree incrementally."""
    try:
        state = _state(view)
        state.seq += 1
        session_id = state.seq
        state.active_session_id = session_id
        state.cancel_pending = False
        view._reset_scan_buffers()
        view._tree.clear()
        view._tree.setSortingEnabled(False)
        view._scan_btn.setEnabled(False)
        view._cancel_btn.setEnabled(True)
        view._progress_bar.show()
        view._progress_bar.setValue(0)
        view._status_label.setText(f"Scanning {path}...")

        state.root_size_accumulator = 0
        state.root_alloc_accumulator = 0
        state.root_files_accumulator = 0
        state.root_folders_accumulator = 0

        state.root_item = NumericSortItem()
        state.root_item.setText(COL_NAME, f"Scanning...   {path}")
        state.root_item.setText(COL_SIZE, "Scanning...")
        state.root_item.setText(COL_ALLOCATED, "...")
        state.root_item.setText(COL_FILES, "...")
        state.root_item.setText(COL_FOLDERS, "...")
        state.root_item.setText(COL_PERCENT, "100.0 %")
        state.root_item.setData(COL_NAME, Qt.ItemDataRole.UserRole, path)
        state.root_item.setData(COL_NAME, ROLE_PERCENT_BAR, 100.0)
        state.root_item.setData(COL_NAME, ROLE_IS_ROOT, True)
        state.root_item.setData(COL_SIZE, Qt.ItemDataRole.UserRole, 0)
        state.root_item.setData(COL_PERCENT, Qt.ItemDataRole.UserRole, 100.0)
        state.root_item.setIcon(COL_NAME, _get_generic_folder_icon())

        for col in range(NUM_COLUMNS):
            state.root_item.setFont(col, _BOLD_FONT)
        for col in (COL_SIZE, COL_ALLOCATED, COL_FILES, COL_FOLDERS):
            state.root_item.setBackground(col, _ROOT_BG_BRUSH)

        view._tree.addTopLevelItem(state.root_item)
        state.root_item.setExpanded(True)

        view._realtime_worker = RealtimeScanWorker(view._scanner, path)
        view._realtime_worker.child_scanned.connect(
            lambda child, sid=session_id: view._on_child_scanned_session(sid, child)
        )
        view._realtime_worker.progress.connect(
            lambda current_path, items_scanned, sid=session_id: view._on_scan_progress_session(
                sid, current_path, items_scanned
            )
        )
        view._realtime_worker.finished.connect(
            lambda result, path_index, sid=session_id: view._on_realtime_finished_session(
                sid, result, path_index
            )
        )
        view._realtime_worker.start()
    except Exception as exc:
        logger.error("Failed to start realtime scan: %s", exc)
        view._reset_scan_buffers()
        view._reset_scan_controls()
        state = _state(view)
        state.active_session_id = None
        state.cancel_pending = False


def start_scan(view, path: str, max_depth: int = 1) -> None:
    """Start scanning a path (non-realtime, used for deeper scans)."""
    try:
        view._tree.clear()
        view._scan_btn.setEnabled(False)
        view._cancel_btn.setEnabled(True)
        view._progress_bar.show()
        view._progress_bar.setValue(0)
        view._status_label.setText(f"Scanning {path}...")

        view._worker = ScanWorker(view._scanner, path, max_depth)
        view._worker.progress.connect(view._on_scan_progress)
        view._worker.finished.connect(view._on_scan_finished)
        view._worker.start()
    except Exception as exc:
        logger.error("Failed to start scan: %s", exc)
        view._reset_scan_controls()


def on_cancel(view) -> None:
    """Cancel ongoing scan."""
    try:
        view._scanner.cancel()
        _state(view).cancel_pending = True
        view._reset_scan_buffers()
        view._reset_scan_controls()
        view._status_label.setText("Cancelling...")
    except Exception as exc:
        logger.error("Failed to cancel scan: %s", exc)


def is_active_realtime_session(view, session_id: int) -> bool:
    """Return True if signal belongs to the currently active scan session."""
    state = _state(view)
    return (
        state.active_session_id is not None
        and session_id == state.active_session_id
    )


def on_scan_progress_session(view, session_id: int, current_path: str, items_scanned: int) -> None:
    """Apply progress only for the active realtime session."""
    if _state(view).cancel_pending or not is_active_realtime_session(view, session_id):
        return
    view._on_scan_progress(current_path, items_scanned)


def on_child_scanned_session(view, session_id: int, child_info: FolderInfo) -> None:
    """Apply child updates only for the active realtime session."""
    if _state(view).cancel_pending or not is_active_realtime_session(view, session_id):
        return
    view._on_child_scanned(child_info)


def on_realtime_finished_session(
    view,
    session_id: int,
    result: Optional[FolderInfo],
    path_index: Optional[dict] = None,
) -> None:
    """Finalize only the active realtime session; ignore stale completions."""
    if not is_active_realtime_session(view, session_id):
        return
    try:
        view._on_realtime_finished(result, path_index)
    finally:
        state = _state(view)
        state.active_session_id = None
        state.cancel_pending = False


def on_scan_progress(view, current_path: str, items_scanned: int) -> None:
    """Update progress display (throttled text update)."""
    try:
        view._progress_bar.setValue(items_scanned)
        now = time.monotonic()
        if now - view._last_progress_text_time >= _PROGRESS_TEXT_MS:
            view._last_progress_text_time = now
            display_path = "..." + current_path[-47:] if len(current_path) > 50 else current_path
            view._status_label.setText(f"Scanning: {display_path}")
    except Exception as exc:
        logger.error("Failed to update scan progress: %s", exc)


def on_child_scanned(view, child_info: FolderInfo) -> None:
    """Buffer child scan result for batched UI update."""
    try:
        state = _state(view)
        if state.root_item is None:
            return

        state.root_size_accumulator += child_info.size_bytes
        state.root_alloc_accumulator += child_info.allocated_bytes
        state.root_files_accumulator += child_info.file_count
        state.root_folders_accumulator += child_info.folder_count

        state.child_buffer.append(child_info)
        if not view._batch_timer.isActive():
            view._batch_timer.start()
    except Exception as exc:
        logger.error("Failed to handle child scan: %s", exc)


def flush_child_buffer(view) -> None:
    """Flush buffered children into tree in one batch."""
    try:
        state = _state(view)
        if state.active_session_id is None or state.cancel_pending:
            state.child_buffer.clear()
            view._batch_timer.stop()
            return
        if not state.child_buffer or state.root_item is None:
            view._batch_timer.stop()
            return

        batch = state.child_buffer[:]
        state.child_buffer.clear()
        view._batch_timer.stop()
        reference_size = view._drive_total_bytes or 1

        try:
            view._tree.setUpdatesEnabled(False)
            for child_info in batch:
                child_item = view._create_tree_item(child_info, reference_size)
                state.root_item.addChild(child_item)

            update_root_item_from_accumulators(
                root_item=state.root_item,
                size_bytes=state.root_size_accumulator,
                allocated_bytes=state.root_alloc_accumulator,
                file_count=state.root_files_accumulator,
                folder_count=state.root_folders_accumulator,
            )
        finally:
            view._tree.setUpdatesEnabled(True)

        if batch:
            last = batch[-1]
            view._status_label.setText(build_scanned_status_text(last.name, last.size_formatted()))
    except Exception as exc:
        logger.error("Failed to flush child buffer: %s", exc)


def on_realtime_finished(view, result: Optional[FolderInfo], path_index: Optional[dict] = None) -> None:
    """Handle realtime scan completion."""
    try:
        state = _state(view)
        view._batch_timer.stop()
        if state.child_buffer:
            view._flush_child_buffer()

        view._scan_btn.setEnabled(True)
        view._cancel_btn.setEnabled(False)
        view._progress_bar.hide()

        if result is None:
            view._status_label.setText("Scan cancelled or failed.")
            view._tree.setSortingEnabled(True)
            return

        try:
            view._tree.setUpdatesEnabled(False)
            if state.root_item:
                update_root_item_from_result(state.root_item, result)
                update_child_percentages(state.root_item, result.size_bytes or 1)
                view._add_file_entries(state.root_item, result, result.size_bytes or 1)
        finally:
            view._tree.setUpdatesEnabled(True)

        view._tree.setSortingEnabled(True)

        cache_scan_result(
            view._scan_cache,
            view._current_scan_path,
            result,
            max_entries=20,
        )
        if view._current_scan_path:
            view._full_tree_cache = result
            view._path_index = path_index if path_index else {}

        view._status_label.setText(view._build_scan_complete_text(result))
    except Exception as exc:
        logger.error("Failed to handle realtime scan completion: %s", exc)
