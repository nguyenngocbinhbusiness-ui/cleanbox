from pathlib import Path
from unittest.mock import patch

from PyQt6.QtWidgets import QMessageBox, QTreeWidgetItem

from features.folder_scanner.service import FolderInfo
from ui.storage import storage_view_interactions as interactions
from ui.views.storage_view import StorageView


def _make_folder(path: str) -> FolderInfo:
    return FolderInfo(
        path=path,
        name=Path(path).name or path,
        size_bytes=1024,
        allocated_bytes=4096,
        file_count=1,
        folder_count=0,
        last_modified="",
        children=[],
    )


def test_storage_view_initializes_and_uses_interaction_controller(qapp):
    view = StorageView()

    assert hasattr(view, "_interaction_controller")
    assert view._interaction_controller.view is view

    with patch.object(view._interaction_controller, "on_add_to_cleanup") as controller_method:
        interactions.on_add_to_cleanup(view, "C:\\ok")

    controller_method.assert_called_once_with("C:\\ok")


def test_on_add_to_cleanup_protected_path(qapp):
    view = StorageView()
    with (
        patch("ui.storage.storage_view_interactions.is_protected_path", return_value=True),
        patch("ui.storage.storage_view_interactions.QMessageBox.warning") as warn_mock,
    ):
        interactions.on_add_to_cleanup(view, "C:\\Windows")
    warn_mock.assert_called_once()


def test_on_add_to_cleanup_invalid_directory(qapp):
    view = StorageView()
    with (
        patch("ui.storage.storage_view_interactions.is_protected_path", return_value=False),
        patch("ui.storage.storage_view_interactions.Path.is_dir", return_value=False),
        patch("ui.storage.storage_view_interactions.QMessageBox.warning") as warn_mock,
    ):
        interactions.on_add_to_cleanup(view, "C:\\not_a_dir")
    warn_mock.assert_called_once()


def test_on_add_to_cleanup_success(qapp):
    view = StorageView()
    emitted = []
    view.add_to_cleanup_requested.connect(lambda path: emitted.append(path))
    with (
        patch("ui.storage.storage_view_interactions.is_protected_path", return_value=False),
        patch("ui.storage.storage_view_interactions.Path.is_dir", return_value=True),
    ):
        interactions.on_add_to_cleanup(view, "C:\\ok")
    assert emitted == ["C:\\ok"]


def test_on_delete_item_guard_paths(qapp):
    view = StorageView()
    with (
        patch("ui.storage.storage_view_interactions.is_protected_path", return_value=True),
        patch("ui.storage.storage_view_interactions.QMessageBox.warning") as warn_mock,
    ):
        interactions.on_delete_item(view, "C:\\Windows")
    warn_mock.assert_called_once()

    with (
        patch("ui.storage.storage_view_interactions.is_protected_path", return_value=False),
        patch("ui.storage.storage_view_interactions.Path.exists", return_value=False),
        patch("ui.storage.storage_view_interactions.QMessageBox.information") as info_mock,
    ):
        interactions.on_delete_item(view, "C:\\missing")
    info_mock.assert_called_once()


def test_on_delete_item_cancel_and_success_removal(qapp, tmp_path):
    view = StorageView()
    temp_file = tmp_path / "demo.txt"
    temp_file.write_text("x", encoding="utf-8")

    item = QTreeWidgetItem(view._tree)
    item.setData(0, 0x0100, str(temp_file))

    with (
        patch("ui.storage.storage_view_interactions.is_protected_path", return_value=False),
        patch(
            "ui.storage.storage_view_interactions.QMessageBox.warning",
            return_value=QMessageBox.StandardButton.Cancel,
        ),
        patch("ui.storage.storage_view_interactions.recycle_path") as recycle_mock,
    ):
        interactions.on_delete_item(view, str(temp_file), item)
    recycle_mock.assert_not_called()

    with (
        patch("ui.storage.storage_view_interactions.is_protected_path", return_value=False),
        patch(
            "ui.storage.storage_view_interactions.QMessageBox.warning",
            return_value=QMessageBox.StandardButton.Yes,
        ),
        patch("ui.storage.storage_view_interactions.recycle_path") as recycle_mock,
    ):
        interactions.on_delete_item(view, str(temp_file), item)
    recycle_mock.assert_called_once()


def test_on_open_file_location_errors(qapp):
    view = StorageView()
    with (
        patch(
            "ui.storage.storage_view_interactions.open_file_location",
            side_effect=FileNotFoundError,
        ),
        patch("ui.storage.storage_view_interactions.QMessageBox.information") as info_mock,
    ):
        interactions.on_open_file_location(view, "C:\\missing")
    info_mock.assert_called_once()

    with (
        patch(
            "ui.storage.storage_view_interactions.open_file_location",
            side_effect=RuntimeError("boom"),
        ),
        patch("ui.storage.storage_view_interactions.QMessageBox.warning") as warn_mock,
    ):
        interactions.on_open_file_location(view, "C:\\err")
    warn_mock.assert_called_once()


def test_navigation_handlers_cached_and_uncached(qapp):
    view = StorageView()
    view._current_scan_path = "C:\\root"
    view._nav_history = ["C:\\prev"]
    view._nav_forward = []
    cached = _make_folder("C:\\prev")

    with (
        patch(
            "ui.storage.storage_view_interactions.navigate_back_state",
            return_value=("C:\\prev", [], ["C:\\root"]),
        ),
        patch("ui.storage.storage_view_interactions.resolve_cached_node", return_value=cached),
        patch.object(view, "_populate_tree") as populate_mock,
    ):
        interactions.on_navigate_back(view)
    populate_mock.assert_called_once()

    with (
        patch(
            "ui.storage.storage_view_interactions.navigate_forward_state",
            return_value=("C:\\next", ["C:\\prev"], []),
        ),
        patch("ui.storage.storage_view_interactions.resolve_cached_node", return_value=None),
        patch.object(view, "_start_realtime_scan") as scan_mock,
    ):
        interactions.on_navigate_forward(view)
    scan_mock.assert_called_once_with("C:\\next")


def test_misc_interaction_helpers(qapp):
    view = StorageView()
    interactions.update_nav_buttons(view)
    interactions.on_refresh(view)
    interactions.update_drive_summary(view)
