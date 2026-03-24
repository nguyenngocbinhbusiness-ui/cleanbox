"""Additional edge-case coverage for storage_view_interactions."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PyQt6.QtCore import QPoint
from PyQt6.QtWidgets import QTreeWidgetItem

from features.folder_scanner.service import FolderInfo
from ui.storage import storage_view_interactions as interactions
from ui.views.storage_view import StorageView


def _folder(path: str) -> FolderInfo:
    return FolderInfo(
        path=path,
        name="x",
        size_bytes=1,
        allocated_bytes=1,
        file_count=1,
        folder_count=1,
        last_modified="",
        children=[],
    )


def test_on_tree_context_menu_guards_and_success(qapp):
    view = StorageView()
    with patch.object(view._tree, "itemAt", return_value=None):
        interactions.on_tree_context_menu(view, object())

    item = MagicMock()
    item.data.return_value = "__placeholder__"
    with patch.object(view._tree, "itemAt", return_value=item):
        interactions.on_tree_context_menu(view, object())

    item.data.return_value = "C:/ok"
    fake_menu = MagicMock()
    with (
        patch.object(view._tree, "itemAt", return_value=item),
        patch("ui.storage.storage_view_interactions.QMenu", return_value=fake_menu),
    ):
        interactions.on_tree_context_menu(view, QPoint(0, 0))
    assert fake_menu.addAction.call_count == 3
    fake_menu.exec.assert_called_once()


def test_on_tree_context_menu_exception_path(qapp):
    view = StorageView()
    with patch.object(view._tree, "itemAt", side_effect=RuntimeError("boom")):
        interactions.on_tree_context_menu(view, object())


def test_on_add_to_cleanup_exception_path(qapp):
    view = StorageView()
    with (
        patch("ui.storage.storage_view_interactions.is_protected_path", return_value=False),
        patch("ui.storage.storage_view_interactions.Path.is_dir", side_effect=RuntimeError("boom")),
    ):
        interactions.on_add_to_cleanup(view, "C:/x")


def test_on_delete_item_top_level_removal_and_exception(qapp):
    view = StorageView()
    top_item = QTreeWidgetItem(view._tree)
    path = "C:/top"

    with (
        patch("ui.storage.storage_view_interactions.is_protected_path", return_value=False),
        patch("ui.storage.storage_view_interactions.Path.exists", return_value=True),
        patch(
            "ui.storage.storage_view_interactions.QMessageBox.warning",
            return_value=interactions.QMessageBox.StandardButton.Yes,
        ),
        patch("ui.storage.storage_view_interactions.recycle_path"),
    ):
        interactions.on_delete_item(view, path, top_item)

    with (
        patch("ui.storage.storage_view_interactions.is_protected_path", return_value=False),
        patch("ui.storage.storage_view_interactions.Path.exists", return_value=True),
        patch("ui.storage.storage_view_interactions.QMessageBox.warning") as warn_mock,
        patch("ui.storage.storage_view_interactions.recycle_path", side_effect=RuntimeError("boom")),
    ):
        warn_mock.side_effect = [interactions.QMessageBox.StandardButton.Yes, None]
        interactions.on_delete_item(view, path, top_item)
    assert warn_mock.call_count >= 2


def test_on_open_file_location_success(qapp):
    view = StorageView()
    with patch("ui.storage.storage_view_interactions.open_file_location"):
        interactions.on_open_file_location(view, "C:/ok")
    assert "Opened file location" in view._status_label.text()


def test_update_drive_summary_and_exception_paths(qapp):
    view = StorageView()
    view._drives = []
    interactions.update_drive_summary(view)

    view._drives = [MagicMock(letter="C:", total_gb=100.0, free_gb=1.0)]
    interactions.update_drive_summary(view)

    with patch.object(view._drive_bars_layout, "count", side_effect=RuntimeError("boom")):
        interactions.update_drive_summary(view)


def test_refresh_and_nav_error_paths(qapp):
    view = StorageView()
    fake_view = SimpleNamespace(refresh_requested=SimpleNamespace(emit=MagicMock(side_effect=RuntimeError("boom"))))
    interactions.on_refresh(fake_view)

    with patch("ui.storage.storage_view_interactions.navigate_back_state", return_value=(None, [], [])):
        interactions.on_navigate_back(view)
    with patch("ui.storage.storage_view_interactions.navigate_back_state", side_effect=RuntimeError("boom")):
        interactions.on_navigate_back(view)

    with patch("ui.storage.storage_view_interactions.navigate_forward_state", return_value=(None, [], [])):
        interactions.on_navigate_forward(view)
    with patch("ui.storage.storage_view_interactions.navigate_forward_state", side_effect=RuntimeError("boom")):
        interactions.on_navigate_forward(view)

    with patch.object(view._back_btn, "setEnabled", side_effect=RuntimeError("boom")):
        interactions.update_nav_buttons(view)


def test_on_item_double_clicked_paths(qapp):
    view = StorageView()
    view._current_scan_path = "C:/old"
    item = QTreeWidgetItem()
    item.setData(interactions.COL_NAME, interactions.Qt.ItemDataRole.UserRole, "C:/new")

    with (
        patch("ui.storage.storage_view_interactions.Path.is_dir", return_value=True),
        patch("ui.storage.storage_view_interactions.update_nav_buttons"),
        patch.object(view, "_start_realtime_scan") as start_scan,
        patch.object(view, "_populate_tree") as populate_tree,
    ):
        interactions.on_item_double_clicked(view, item, 0)
    start_scan.assert_called_once_with("C:/new")
    populate_tree.assert_not_called()

    cached = _folder("C:/new")
    view._path_index["C:/new"] = cached
    with (
        patch("ui.storage.storage_view_interactions.Path.is_dir", return_value=True),
        patch("ui.storage.storage_view_interactions.update_nav_buttons"),
        patch.object(view, "_populate_tree") as populate_tree,
    ):
        interactions.on_item_double_clicked(view, item, 0)
    populate_tree.assert_called_once_with(cached)
