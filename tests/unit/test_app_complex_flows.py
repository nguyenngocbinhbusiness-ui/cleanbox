import pytest
from unittest.mock import MagicMock, patch, call, PropertyMock


class TestAppComplexFlows:

    @pytest.fixture
    def app(self, qapp):
        """Create App instance with mocks."""
        import app as app_module

        with (
            patch.object(app_module, "ConfigManager") as MockConfig,
            patch.object(app_module, "StorageMonitor") as MockMonitor,
            patch.object(app_module, "NotificationService") as MockNotify,
            patch.object(app_module, "CleanupService") as MockCleanup,
            patch.object(app_module, "TrayIcon") as MockTray,
            patch.object(app_module, "MainWindow") as MockWindow,
            patch.object(app_module, "get_default_directories") as MockGetDefaults,
        ):

            app_instance = app_module.App()
            # Mocks are not automatically set on instance for services initialized in __init__
            # App.__init__ assigns self._config = ConfigManager() (which returns mock instance)

            # For properties initialized in start(), we must set them manually if testing methods that assume they exist
            # But tests call App methods directly.

            # Expose mocks for verification
            app_instance.mock_config_cls = MockConfig
            app_instance.mock_monitor_cls = MockMonitor
            app_instance.mock_notify_cls = MockNotify
            app_instance.mock_cleanup_cls = MockCleanup
            app_instance.mock_tray_cls = MockTray
            app_instance.mock_window_cls = MockWindow
            app_instance.mock_get_defaults = MockGetDefaults

            # App init calls:
            # self._config = ConfigManager()
            # self._cleanup_service = CleanupService()
            # self._notification_service = NotificationService()

            # Access the instances
            app_instance._config = MockConfig.return_value
            app_instance._cleanup_service = MockCleanup.return_value
            app_instance._notification_service = MockNotify.return_value

            yield app_instance

    def test_handle_first_run(self, app):
        """Test first run logic helper."""
        # This method is called by start() when is_first_run is True

        # Setup defaults
        app.mock_get_defaults.return_value = ["C:/Downloads", "C:/Temp"]

        # Call PRIVATE method
        from app import App

        App._handle_first_run(app)

        # Verify
        app.mock_get_defaults.assert_called_once()
        app._config.add_directory.assert_has_calls(
            [call("C:/Downloads"), call("C:/Temp")]
        )
        app._config.mark_first_run_complete.assert_called_once()

    def test_start_logic_first_run(self, app):
        """Test start() with first run."""
        app._config.is_first_run = True
        app._config.auto_start_enabled = False

        # We must patch app.QApplication because app module already imported the real class
        # And patch("PyQt6...") won't affect app.QApplication reference.
        # We need "app" module to patch against.
        import app as app_module

        with (
            patch("sys.argv", ["cleanbox.exe"]),
            patch.object(app_module, "QApplication") as MockQApp,
            patch.object(app_module, "registry"),
            patch.object(app_module.atexit, "register"),
            patch.object(app_module.App, "_acquire_single_instance", return_value=True),
        ):

            # Setup mock app instance returned by constructor
            mock_qt_instance = MockQApp.return_value
            mock_qt_instance.exec.return_value = 0

            # We need to set mock_get_defaults return value since _handle_first_run uses it
            # fixture sets it on app instance, but start() calls _handle_first_run on self.
            # And self is 'app' fixture instance.
            # app.mock_get_defaults is the mock object for get_default_directories
            app.mock_get_defaults.return_value = ["C:/Def"]

            app.start()

            app._config.mark_first_run_complete.assert_called()

    def test_on_directory_added(self, app):
        """Test directory added slot."""
        from app import App

        App._on_directory_added(app, "C:/NewDir")
        app._config.add_directory.assert_called_with("C:/NewDir")

    def test_do_cleanup_success(self, app):
        """Test cleanup starts worker successfully."""
        # App now uses CleanupProgressWorker for async cleanup
        app._config.cleanup_directories = ["C:/TestDir"]
        app._cleanup_worker = None
        app._main_window = MagicMock()
        app._tray_icon = MagicMock()

        import app as app_module

        with (
            patch.object(app_module, "CleanupProgressWorker") as MockWorker,
            patch.object(app_module, "QMessageBox") as MockMsgBox,
        ):
            MockMsgBox.StandardButton.Ok = 1024
            MockMsgBox.StandardButton.Cancel = 4194304
            MockMsgBox.warning.return_value = MockMsgBox.StandardButton.Ok
            mock_worker_instance = MagicMock()
            MockWorker.return_value = mock_worker_instance

            from app import App

            App._do_cleanup(app)

            # Verify worker was created with directories
            MockWorker.assert_called_once()
            assert mock_worker_instance.start.called
            # Verify UI shows progress
            app._main_window.show_cleanup_progress.assert_called_with(True)
            app._tray_icon.set_status.assert_called()

    def test_do_cleanup_error(self, app):
        """Test cleanup startup error handling for the async worker path."""
        app._cleanup_worker = None
        app._config = MagicMock()
        app._main_window = MagicMock()
        app._tray_icon = MagicMock()
        type(app._config).cleanup_directories = PropertyMock(
            side_effect=Exception("Boom")
        )

        from app import App

        with patch("app.logger") as mock_log:
            App._do_cleanup(app)

        mock_log.error.assert_called()
        app._notification_service.notify_cleanup_result.assert_not_called()

    def test_on_exit(self, app):
        """Test exit cleanup."""
        # Inject mocks for optional components
        app._storage_monitor = MagicMock()
        app._tray_icon = MagicMock()
        app._qt_app = MagicMock()

        from app import App

        App._do_exit(app)

        app._storage_monitor.stop.assert_called_once()
        app._tray_icon.stop.assert_called_once()
        app._qt_app.quit.assert_called_once()

    def test_refresh_storage(self, app):
        """Test manual refresh storage."""
        app._storage_monitor = MagicMock()
        app._main_window = MagicMock()

        from app import App

        App._refresh_storage_data(app)

        app._storage_monitor.get_all_drives.assert_called_once()
        app._main_window.update_drives.assert_called_once()

    def test_acquire_single_instance_returns_false_on_unrecoverable_lock_error(
        self, app
    ):
        """Unrecoverable lock acquisition failures must fail closed."""
        from app import App
        import app as app_module

        mock_socket = MagicMock()
        mock_socket.waitForConnected.return_value = False

        mock_server = MagicMock()
        mock_server.listen.side_effect = [False, False]
        mock_server.errorString.return_value = "listen failed"

        with (
            patch.object(
                app_module, "QLocalSocket", side_effect=[mock_socket, mock_socket]
            ),
            patch.object(app_module, "QLocalServer", return_value=mock_server),
            patch.object(app_module.QLocalServer, "removeServer"),
        ):
            acquired = App._acquire_single_instance(app)

        assert acquired is False
        assert app._startup_error is not None
        assert "Failed to acquire single-instance lock" in app._startup_error
