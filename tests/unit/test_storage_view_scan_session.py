"""Coverage tests for ui.storage.storage_view_scan_session helpers."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from features.folder_scanner.service import FolderInfo
from ui.storage import storage_view_scan_session as scan_session


def _folder(path: str = "C:/root") -> FolderInfo:
    return FolderInfo(
        path=path,
        name="root",
        size_bytes=1000,
        allocated_bytes=4096,
        file_count=2,
        folder_count=1,
        last_modified="",
        children=[],
    )


def _base_view():
    return SimpleNamespace(
        _scan_session_seq=0,
        _active_scan_session_id=None,
        _realtime_cancel_pending=False,
        _reset_scan_buffers=MagicMock(),
        _reset_scan_controls=MagicMock(),
        _tree=MagicMock(),
        _scan_btn=MagicMock(),
        _cancel_btn=MagicMock(),
        _progress_bar=MagicMock(),
        _status_label=MagicMock(),
        _scanner=MagicMock(),
        _on_child_scanned_session=MagicMock(),
        _on_scan_progress_session=MagicMock(),
        _on_realtime_finished_session=MagicMock(),
        _on_scan_progress=MagicMock(),
        _on_scan_finished=MagicMock(),
        _batch_timer=MagicMock(),
        _root_item=MagicMock(),
        _child_buffer=[],
        _drive_total_bytes=1024,
        _create_tree_item=MagicMock(return_value=MagicMock()),
        _root_size_accumulator=0,
        _root_alloc_accumulator=0,
        _root_files_accumulator=0,
        _root_folders_accumulator=0,
        _flush_child_buffer=MagicMock(),
        _add_file_entries=MagicMock(),
        _scan_cache={},
        _current_scan_path="C:/root",
        _full_tree_cache=None,
        _path_index={},
        _build_scan_complete_text=MagicMock(return_value="Scan complete"),
        _last_progress_text_time=0.0,
    )


def test_start_realtime_scan_supports_dedicated_session_state():
    view = _base_view()
    state = SimpleNamespace(
        seq=5,
        active_session_id=None,
        cancel_pending=True,
        root_item=None,
        root_size_accumulator=99,
        root_alloc_accumulator=88,
        root_files_accumulator=77,
        root_folders_accumulator=66,
        child_buffer=[],
    )
    view._scan_session_state = state

    worker = MagicMock()
    with (
        patch("ui.storage.storage_view_scan_session.NumericSortItem", return_value=MagicMock()),
        patch("ui.storage.storage_view_scan_session._get_generic_folder_icon", return_value=MagicMock()),
        patch("ui.storage.storage_view_scan_session.RealtimeScanWorker", return_value=worker),
    ):
        scan_session.start_realtime_scan(view, "C:/root")

    assert state.seq == 6
    assert state.active_session_id == 6
    assert state.cancel_pending is False


def test_start_realtime_scan_exception_path():
    view = _base_view()
    with patch("ui.storage.storage_view_scan_session.NumericSortItem", side_effect=RuntimeError("boom")):
        scan_session.start_realtime_scan(view, "C:/root")

    view._reset_scan_buffers.assert_called()
    view._reset_scan_controls.assert_called()
    assert view._active_scan_session_id is None
    assert view._realtime_cancel_pending is False


def test_start_scan_exception_path():
    view = _base_view()
    with patch("ui.storage.storage_view_scan_session.ScanWorker", side_effect=RuntimeError("boom")):
        scan_session.start_scan(view, "C:/root")
    view._reset_scan_controls.assert_called_once()


def test_on_cancel_exception_path():
    view = _base_view()
    view._scanner.cancel.side_effect = RuntimeError("boom")
    scan_session.on_cancel(view)
    # no raise


def test_on_scan_progress_exception_path():
    view = _base_view()
    view._progress_bar.setValue.side_effect = RuntimeError("boom")
    scan_session.on_scan_progress(view, "C:/x", 1)
    # no raise


def test_on_child_scanned_exception_path():
    view = _base_view()
    view._child_buffer = None
    scan_session.on_child_scanned(view, _folder())
    # no raise


def test_flush_child_buffer_early_returns():
    view = _base_view()
    view._active_scan_session_id = None
    view._child_buffer = [_folder()]
    scan_session.flush_child_buffer(view)
    assert view._child_buffer == []

    view._active_scan_session_id = 1
    view._child_buffer = []
    scan_session.flush_child_buffer(view)
    assert view._batch_timer.stop.called


def test_flush_child_buffer_exception_path():
    view = _base_view()
    view._active_scan_session_id = 1
    view._child_buffer = [_folder()]
    view._tree.setUpdatesEnabled.side_effect = RuntimeError("boom")
    scan_session.flush_child_buffer(view)
    # no raise


def test_on_realtime_finished_result_none():
    view = _base_view()
    scan_session.on_realtime_finished(view, None)
    view._status_label.setText.assert_called_with("Scan cancelled or failed.")
    view._tree.setSortingEnabled.assert_called_with(True)


def test_on_realtime_finished_success_and_cache_update():
    view = _base_view()
    result = _folder()

    with (
        patch("ui.storage.storage_view_scan_session.update_root_item_from_result"),
        patch("ui.storage.storage_view_scan_session.update_child_percentages"),
        patch("ui.storage.storage_view_scan_session.cache_scan_result"),
    ):
        scan_session.on_realtime_finished(view, result, {"C:/root": result})

    assert view._full_tree_cache == result
    assert "C:/root" in view._path_index
    view._status_label.setText.assert_called_with("Scan complete")


def test_on_realtime_finished_exception_path():
    view = _base_view()
    view._batch_timer.stop.side_effect = RuntimeError("boom")
    scan_session.on_realtime_finished(view, _folder())
    # no raise
