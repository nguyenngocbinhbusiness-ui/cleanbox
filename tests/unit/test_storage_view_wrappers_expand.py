"""Targeted coverage tests for StorageView wrappers and expand flows."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTreeWidgetItem

from features.folder_scanner.service import FolderInfo
from ui.views.storage_view import StorageView


def _folder(path: str, name: str, children=None) -> FolderInfo:
    return FolderInfo(
        path=path,
        name=name,
        size_bytes=1000,
        allocated_bytes=4096,
        file_count=2,
        folder_count=1,
        last_modified="",
        children=children or [],
    )


def test_wrapper_forwarding_methods(qapp):
    view = StorageView()

    with (
        patch("ui.storage.storage_view.start_realtime_scan") as start_rt,
        patch("ui.storage.storage_view.start_scan") as start_scan,
        patch("ui.storage.storage_view.on_cancel") as on_cancel,
        patch("ui.storage.storage_view.is_active_realtime_session", return_value=True) as active,
        patch("ui.storage.storage_view.on_scan_progress_session") as progress_session,
        patch("ui.storage.storage_view.on_child_scanned_session") as child_session,
        patch("ui.storage.storage_view.on_realtime_finished_session") as finish_session,
        patch("ui.storage.storage_view.on_scan_progress") as progress,
        patch("ui.storage.storage_view.on_child_scanned") as child,
        patch("ui.storage.storage_view.flush_child_buffer") as flush,
        patch("ui.storage.storage_view.on_realtime_finished") as finish,
        patch("ui.storage.storage_view.on_tree_context_menu") as tree_menu,
        patch("ui.storage.storage_view.on_add_to_cleanup") as add_cleanup,
        patch("ui.storage.storage_view.on_delete_item") as delete_item,
        patch("ui.storage.storage_view.on_open_file_location") as open_loc,
        patch("ui.storage.storage_view.update_drive_summary") as update_summary,
        patch("ui.storage.storage_view.on_refresh") as refresh,
        patch("ui.storage.storage_view.on_item_double_clicked") as double_clicked,
        patch("ui.storage.storage_view.on_navigate_back") as nav_back,
        patch("ui.storage.storage_view.on_navigate_forward") as nav_forward,
        patch("ui.storage.storage_view.update_nav_buttons") as nav_buttons,
    ):
        view._start_realtime_scan("C:\\")
        view._start_scan("C:\\", 2)
        view._on_cancel()
        assert view._is_active_realtime_session(1) is True
        view._on_scan_progress_session(1, "C:\\", 5)
        view._on_child_scanned_session(1, _folder("C:\\a", "a"))
        view._on_realtime_finished_session(1, None, {})
        view._on_scan_progress("C:\\", 5)
        view._on_child_scanned(_folder("C:\\a", "a"))
        view._flush_child_buffer()
        view._on_realtime_finished(None, {})
        view._on_tree_context_menu(None)
        view._on_add_to_cleanup("C:\\a")
        view._on_delete_item("C:\\a", None)
        view._on_open_file_location("C:\\a")
        view._update_drive_summary()
        view._on_refresh()
        view._on_item_double_clicked(QTreeWidgetItem(), 0)
        view._on_navigate_back()
        view._on_navigate_forward()
        view._update_nav_buttons()

    start_rt.assert_called_once()
    start_scan.assert_called_once()
    on_cancel.assert_called_once()
    active.assert_called_once()
    progress_session.assert_called_once()
    child_session.assert_called_once()
    finish_session.assert_called_once()
    progress.assert_called_once()
    child.assert_called_once()
    flush.assert_called_once()
    finish.assert_called_once()
    tree_menu.assert_called_once()
    add_cleanup.assert_called_once()
    delete_item.assert_called_once()
    open_loc.assert_called_once()
    update_summary.assert_called_once()
    refresh.assert_called_once()
    double_clicked.assert_called_once()
    nav_back.assert_called_once()
    nav_forward.assert_called_once()
    nav_buttons.assert_called_once()


def test_on_scan_finished_cache_eviction_and_none_result(qapp):
    view = StorageView()
    view._scan_btn = MagicMock()
    view._cancel_btn = MagicMock()
    view._progress_bar = MagicMock()
    view._status_label = MagicMock()
    view._current_scan_path = "C:\\root"
    view._scan_cache = {f"k{i}": _folder(f"C:\\k{i}", f"k{i}") for i in range(20)}

    with patch.object(view, "_populate_tree") as populate:
        view._on_scan_finished(_folder("C:\\root", "root"))

    assert len(view._scan_cache) == 20
    assert "C:\\root" in view._scan_cache
    populate.assert_called_once()

    view._on_scan_finished(None)
    view._status_label.setText.assert_called_with("Scan cancelled or failed.")


def test_on_item_expanded_cached_and_scan_paths(qapp):
    view = StorageView()
    parent = QTreeWidgetItem(view._tree)
    placeholder = QTreeWidgetItem(parent)
    placeholder.setData(0, Qt.ItemDataRole.UserRole, "__placeholder__")
    parent.setData(0, Qt.ItemDataRole.UserRole, "C:\\root")
    parent.setData(1, Qt.ItemDataRole.UserRole, 1000)

    cached = _folder("C:\\root", "root", children=[_folder("C:\\root\\a", "a")])
    view._path_index["C:\\root"] = cached

    with (
        patch("ui.storage.storage_view.Path.is_dir", return_value=True),
        patch.object(view, "_populate_expand_from_cache") as from_cache,
        patch.object(view, "_start_expand_scan") as start_scan,
    ):
        view._on_item_expanded(parent)
    from_cache.assert_called_once()
    start_scan.assert_not_called()

    view._path_index.clear()
    with (
        patch("ui.storage.storage_view.Path.is_dir", return_value=True),
        patch.object(view, "_populate_expand_from_cache") as from_cache,
        patch.object(view, "_start_expand_scan") as start_scan,
    ):
        view._on_item_expanded(parent)
    from_cache.assert_not_called()
    start_scan.assert_called_once()


def test_populate_expand_from_cache_and_start_expand_scan(qapp):
    view = StorageView()
    parent = QTreeWidgetItem(view._tree)
    placeholder = QTreeWidgetItem(parent)
    placeholder.setData(0, Qt.ItemDataRole.UserRole, "__placeholder__")
    parent.setData(1, Qt.ItemDataRole.UserRole, 1000)

    cached = _folder(
        "C:\\root",
        "root",
        children=[_folder("C:\\root\\a", "a"), _folder("C:\\root\\b", "b")],
    )
    view._populate_expand_from_cache(parent, cached)
    assert parent.childCount() >= 2

    running_worker = MagicMock()
    running_worker.isRunning.return_value = True
    view._expand_worker = running_worker
    view._start_expand_scan(parent, "C:\\root")
    assert view._pending_expand_request == (parent, "C:\\root")


def test_start_expand_scan_supports_dedicated_expand_state(qapp):
    view = StorageView()
    parent = QTreeWidgetItem(view._tree)
    running_worker = MagicMock()
    running_worker.isRunning.return_value = True
    view._expand_flow_state.worker = running_worker

    view._start_expand_scan(parent, "C:\\stateful")

    assert view._expand_flow_state.pending_request == (parent, "C:\\stateful")


def test_on_expand_finished_paths(qapp):
    view = StorageView()
    parent = QTreeWidgetItem(view._tree)
    placeholder = QTreeWidgetItem(parent)
    placeholder.setData(0, Qt.ItemDataRole.UserRole, "__placeholder__")
    parent.setData(1, Qt.ItemDataRole.UserRole, 1000)

    view._expanding_item = parent
    view._pending_expand_request = (parent, "C:\\next")
    with patch.object(view, "_start_expand_scan") as start_scan:
        view._on_expand_finished(None)
    start_scan.assert_called_once_with(parent, "C:\\next")

    view._expanding_item = parent
    view._pending_expand_request = None
    result = _folder("C:\\root", "root", children=[_folder("C:\\root\\a", "a")])
    view._on_expand_finished(result)
    assert parent.childCount() >= 1
