"""Additional path coverage for app.App."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app import App
from features.storage_monitor.utils import DriveInfo
from PyQt6.QtWidgets import QMessageBox


@pytest.fixture
def app_instance():
    with (
        patch("app.ConfigManager"),
        patch("app.CleanupService"),
        patch("app.NotificationService"),
        patch("sys.argv", ["test"]),
    ):
        app = App()
        app._storage_monitor = MagicMock()
        app._main_window = MagicMock()
        app._tray_icon = MagicMock()
        app._qt_app = MagicMock()
        return app


def test_handle_new_connection_show_command(app_instance):
    socket = MagicMock()
    socket.readAll.return_value.data.return_value.decode.return_value = "show"
    app_instance._local_server = MagicMock()
    app_instance._local_server.nextPendingConnection.return_value = socket

    with patch.object(app_instance, "_do_show_settings") as show_settings:
        app_instance._handle_new_connection()

    show_settings.assert_called_once()
    socket.close.assert_called_once()


def test_cleanup_on_exit_closes_local_server(app_instance):
    app_instance._local_server = MagicMock()
    app_instance._cleanup_on_exit()
    app_instance._local_server.close.assert_called_once()
    app_instance._storage_monitor.stop.assert_called_once()
    app_instance._tray_icon.stop.assert_called_once()


def test_on_low_space_cleared_success(app_instance):
    app_instance._on_low_space_cleared("C:")
    app_instance._config.remove_notified_drive.assert_called_once_with("C:")


def test_do_cleanup_skips_when_worker_running(app_instance):
    worker = MagicMock()
    worker.isRunning.return_value = True
    app_instance._cleanup_worker = worker

    app_instance._do_cleanup()

    app_instance._main_window.show_cleanup_progress.assert_not_called()


def test_do_cleanup_skips_when_no_directories(app_instance):
    app_instance._cleanup_worker = None
    app_instance._config.cleanup_directories = []

    app_instance._do_cleanup()

    app_instance._tray_icon.set_status.assert_not_called()


def test_do_cleanup_cancelled_in_confirmation_dialog(app_instance):
    app_instance._cleanup_worker = None
    app_instance._config.cleanup_directories = ["C:/tmp"]

    with patch("app.QMessageBox.warning", return_value=QMessageBox.StandardButton.Cancel):
        app_instance._do_cleanup()

    assert app_instance._cleanup_worker is None


def test_on_cleanup_progress_updates_ui_and_tray(app_instance):
    app_instance._on_cleanup_progress(2, 9)
    app_instance._main_window.set_cleanup_progress.assert_called_once_with(2, 9)
    app_instance._tray_icon.set_status.assert_called_once_with("Cleaning 2/9...")


def test_on_cleanup_finished_success(app_instance):
    result = SimpleNamespace(total_files=1, total_folders=2, total_size_mb=3.5, errors=[])
    app_instance._cleanup_worker = MagicMock()

    app_instance._on_cleanup_finished(result)

    app_instance._main_window.show_cleanup_progress.assert_called_with(False)
    app_instance._tray_icon.set_status.assert_called_with(None)
    app_instance._notification_service.notify_cleanup_result.assert_called_once()
    assert app_instance._cleanup_worker is None


def test_on_do_show_settings_calls_window_methods(app_instance):
    app_instance._do_show_settings()
    app_instance._main_window.show.assert_called_once()
    app_instance._main_window.raise_.assert_called_once()
    app_instance._main_window.activateWindow.assert_called_once()


def test_autostart_disable_branch(app_instance):
    with patch("app.registry.disable_autostart") as disable_mock:
        app_instance._on_autostart_changed(False)
    disable_mock.assert_called_once()


def test_threshold_and_interval_update_monitor(app_instance):
    app_instance._on_threshold_changed(12)
    app_instance._storage_monitor.update_threshold.assert_called_once_with(12)
    app_instance._on_interval_changed(33)
    app_instance._storage_monitor.update_interval.assert_called_once_with(33)


def test_refresh_storage_data_success(app_instance):
    drives = [DriveInfo("C:", 100.0, 50.0, 50.0, 50.0)]
    app_instance._storage_monitor.get_all_drives.return_value = drives

    app_instance._refresh_storage_data()

    app_instance._main_window.update_drives.assert_called_once_with(drives)
