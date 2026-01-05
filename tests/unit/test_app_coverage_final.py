
import pytest
from unittest.mock import MagicMock, patch
from app import App
from features.storage_monitor.utils import DriveInfo

class TestAppCoverageFinal:
    
    @pytest.fixture
    def app(self):
        # Patch init components
        with patch("app.ConfigManager"), \
             patch("app.CleanupService"), \
             patch("app.NotificationService"), \
             patch("sys.argv", ["test"]):
             app = App()
             # Manually init optional components for testing slots
             app._storage_monitor = MagicMock()
             app._main_window = MagicMock()
             app._tray_icon = MagicMock()
             app._qt_app = MagicMock()
             return app

    def test_start_exception(self, app):
        """Cover exception in start method."""
        # Force QApplication creation to fail
        with patch("app.QApplication", side_effect=Exception("Qt Init Error")), \
             patch("app.logger") as mock_log, \
             patch("atexit.register"):
            
            res = app.start()
            assert res == 1
            mock_log.exception.assert_called()

    def test_cleanup_on_exit_exception(self, app):
        """Cover exception in cleanup_on_exit."""
        app._storage_monitor.stop.side_effect = Exception("Monitor error")
        
        with patch("app.logger") as mock_log:
            app._cleanup_on_exit()
            mock_log.warning.assert_called()

    def test_handle_first_run_exception(self, app):
        """Cover exception in handle_first_run."""
        with patch("app.get_default_directories", side_effect=Exception("Dir Error")), \
             patch("app.logger") as mock_log:
            
            app._handle_first_run()
            mock_log.error.assert_called()

    def test_on_low_space_exception(self, app):
        """Cover exception in _on_low_space."""
        app._notification_service.notify_low_space.side_effect = Exception("Notify Error")
        
        with patch("app.logger") as mock_log:
            app._on_low_space(DriveInfo("C", 100, 10, 90, 90))
            mock_log.error.assert_called()

    def test_emit_signals_exceptions(self, app):
        """Cover exceptions in signal emitters."""
        with patch("app.logger") as mock_log:
            # Cleanup signal
            app._cleanup_signal = MagicMock()
            app._cleanup_signal.emit.side_effect = Exception("Emit Error")
            app._emit_cleanup()
            mock_log.error.assert_called()
            
            # Settings signal
            app._show_settings_signal = MagicMock()
            app._show_settings_signal.emit.side_effect = Exception("Emit Error")
            app._emit_show_settings()
            mock_log.error.assert_called()
            
            # Exit signal
            app._exit_signal = MagicMock()
            app._exit_signal.emit.side_effect = Exception("Emit Error")
            app._emit_exit()
            mock_log.error.assert_called()

    def test_do_handlers_exceptions(self, app):
        """Cover exceptions in _do_* slots."""
        with patch("app.logger") as mock_log:
            # Cleanup - now uses CleanupProgressWorker
            # Force exception by having cleanup_directories property raise
            app._cleanup_worker = None
            type(app._config).cleanup_directories = property(
                lambda self: (_ for _ in ()).throw(Exception("Dir Error"))
            )
            app._do_cleanup()
            mock_log.error.assert_called()
            
            # Show Settings
            app._main_window.show.side_effect = Exception("Show Error")
            app._do_show_settings()
            mock_log.error.assert_called()
            
            # Exit
            app._storage_monitor.stop.side_effect = Exception("Exit Error")
            app._do_exit()
            mock_log.error.assert_called()

    def test_directory_handlers_exceptions(self, app):
        """Cover exceptions in directory slots."""
        with patch("app.logger") as mock_log:
            # Add
            app._config.add_directory.side_effect = Exception("Add Error")
            app._on_directory_added("path")
            mock_log.error.assert_called()
            
            # Remove
            app._config.remove_directory.side_effect = Exception("Remove Error")
            app._on_directory_removed("path")
            mock_log.error.assert_called()

    def test_autostart_handler_exception(self, app):
        """Cover exception in _on_autostart_changed."""
        app._config.auto_start_enabled = False # Default
        # Property setter might fail? Or registry call.
        with patch("app.registry.enable_autostart", side_effect=Exception("Reg Error")), \
             patch("app.logger") as mock_log:
             
             app._on_autostart_changed(True)
             mock_log.error.assert_called()

    def test_refresh_storage_exception(self, app):
        """Cover exception in _refresh_storage_data."""
        app._storage_monitor.get_all_drives.side_effect = Exception("Refresh Error")
        
        with patch("app.logger") as mock_log:
            app._refresh_storage_data()
            mock_log.error.assert_called()

