"""Expand-flow helpers extracted from StorageView."""
from dataclasses import dataclass
import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTreeWidgetItem

from features.folder_scanner import FolderInfo
from ui.views.storage_view_tree import COL_NAME, COL_SIZE

logger = logging.getLogger(__name__)


@dataclass
class ExpandFlowState:
    """Mutable state for lazy tree expansion flows."""

    worker: object | None = None
    expanding_item: Optional[QTreeWidgetItem] = None
    pending_request: Optional[tuple[QTreeWidgetItem, str]] = None


def _state(view) -> ExpandFlowState:
    state = getattr(view, "_expand_flow_state", None)
    if state is not None:
        return state
    return ExpandFlowState(
        worker=getattr(view, "_expand_worker", None),
        expanding_item=getattr(view, "_expanding_item", None),
        pending_request=getattr(view, "_pending_expand_request", None),
    )


def on_item_expanded(view, item: QTreeWidgetItem, path_cls) -> None:
    """Handle tree item expand - use cache or lazy scan sub-folders."""
    try:
        if item.childCount() == 1:
            child = item.child(0)
            if child and child.data(COL_NAME, Qt.ItemDataRole.UserRole) == "__placeholder__":
                path = item.data(COL_NAME, Qt.ItemDataRole.UserRole)
                if path and path_cls(path).is_dir():
                    cached = view._path_index.get(path)
                    if cached and cached.children:
                        view._populate_expand_from_cache(item, cached)
                    else:
                        view._start_expand_scan(item, path)
    except Exception as error:
        logger.error("Failed to handle item expand: %s", error)


def populate_expand_from_cache(view, item: QTreeWidgetItem, cached: FolderInfo) -> None:
    """Populate expanded item children from cache."""
    try:
        view._tree.setUpdatesEnabled(False)
        try:
            while item.childCount() > 0:
                item.removeChild(item.child(0))

            parent_size = item.data(COL_SIZE, Qt.ItemDataRole.UserRole) or 1
            for child in cached.children:
                child_item = view._create_tree_item(child, parent_size)
                item.addChild(child_item)
            view._add_file_entries(item, cached, parent_size)
        finally:
            view._tree.setUpdatesEnabled(True)

        view._status_label.setText(
            f"Expanded (cached): {cached.name} — {len(cached.children)} sub-folders"
        )
    except Exception as error:
        logger.error("Failed to populate from cache: %s", error)


def start_expand_scan(view, item: QTreeWidgetItem, path: str) -> None:
    """Start scanning sub-folders for a tree item expand."""
    try:
        state = _state(view)
        if state.worker is not None and state.worker.isRunning():
            view._scanner.cancel()
            state.pending_request = (item, path)
            view._status_label.setText("Cancelling previous expand scan...")
            return

        state.expanding_item = item
        state.pending_request = None
        view._status_label.setText(f"Scanning: {path}...")

        state.worker = view._expand_worker_cls(view._scanner, path)
        state.worker.finished.connect(view._on_expand_finished)
        state.worker.start()
    except Exception as error:
        logger.error("Failed to start expand scan: %s", error)


def on_expand_finished(view, result: Optional[FolderInfo]) -> None:
    """Handle expand scan completion and populate children."""
    try:
        state = _state(view)
        item = state.expanding_item
        state.expanding_item = None
        pending_request = state.pending_request
        state.pending_request = None

        if pending_request is not None:
            pending_item, pending_path = pending_request
            view._start_expand_scan(pending_item, pending_path)

        if item is None or result is None:
            if pending_request is None:
                view._status_label.setText("Expand scan cancelled or failed.")
            return

        view._tree.setUpdatesEnabled(False)
        try:
            while item.childCount() > 0:
                item.removeChild(item.child(0))

            parent_size = item.data(COL_SIZE, Qt.ItemDataRole.UserRole) or 1
            for child in result.children:
                child_item = view._create_tree_item(child, parent_size)
                item.addChild(child_item)
            view._add_file_entries(item, result, parent_size)
        finally:
            view._tree.setUpdatesEnabled(True)

        view._status_label.setText(
            f"Expanded: {result.name} — {len(result.children)} sub-folders"
        )
    except Exception as error:
        logger.error("Failed to handle expand completion: %s", error)
