
import pytest
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QMessageBox

from ui.views.cleanup_view import CleanupView
from ui.views.settings_view import SettingsView
from ui.views.storage_view import StorageView
from ui.main_window import MainWindow

class TestUIErrorCoverage:
    
    def test_cleanup_view_errors(self, qapp):
        """Cover exception handling in CleanupView slots."""
        view = CleanupView()
        
        # 1. _on_add_directory error
        with patch("ui.views.cleanup_view.QFileDialog.getExistingDirectory", side_effect=Exception("Dialog Error")), \
             patch("ui.views.cleanup_view.QMessageBox.warning") as mock_warn, \
             patch("ui.views.cleanup_view.logger") as mock_log:
            
            view._on_add_directory()
            mock_log.error.assert_called()
            mock_warn.assert_called()
            
        # 2. _on_remove_directory error
        # Force currentItem to raise exception when accessed or data retrieved
        with patch.object(view._dir_list, "currentItem", side_effect=Exception("List Error")), \
             patch("ui.views.cleanup_view.QMessageBox.warning") as mock_warn, \
             patch("ui.views.cleanup_view.logger") as mock_log:
             
             view._on_remove_directory()
             mock_log.error.assert_called()
             mock_warn.assert_called()

        # 3. _on_cleanup error
        # Raise exception during signal emit
        view.cleanup_requested = MagicMock()
        view.cleanup_requested.emit.side_effect = Exception("Signal Error")
        
        with patch("ui.views.cleanup_view.logger") as mock_log:
            view._on_cleanup()
            mock_log.error.assert_called()

        # 4. _setup_ui error (simulate by passing invalid parent or patching internal call)
        # It's called in init, so we need to patch before init
        with patch("ui.views.cleanup_view.QVBoxLayout", side_effect=Exception("Layout Error")), \
             patch("ui.views.cleanup_view.logger") as mock_log:
             
             # Should not crash, just log errors
             CleanupView()
             mock_log.error.assert_called()

    def test_settings_view_errors(self, qapp):
        """Cover exception handling in SettingsView."""
        view = SettingsView()
        
    def test_settings_view_errors(self, qapp):
        """Cover exception handling in SettingsView."""
        view = SettingsView()
        
        # Test _on_autostart_changed error
        view.autostart_changed = MagicMock()
        view.autostart_changed.emit.side_effect = Exception("Signal Error")
        
        with patch("ui.views.settings_view.logger") as mock_log:
            view._on_autostart_changed(2)
            mock_log.error.assert_called()

        # Test _on_threshold_changed error
        view.threshold_changed = MagicMock()
        view.threshold_changed.emit.side_effect = Exception("Signal Error")
        
        with patch("ui.views.settings_view.logger") as mock_log:
            view._on_threshold_changed(10)
            mock_log.error.assert_called()

        # Test _on_interval_changed error
        view.interval_changed = MagicMock()
        view.interval_changed.emit.side_effect = Exception("Signal Error")
        
        with patch("ui.views.settings_view.logger") as mock_log:
            view._on_interval_changed(60)
            mock_log.error.assert_called()

    def test_storage_view_errors(self, qapp):
        """Cover StorageView error handling."""
        view = StorageView()
        
        # Test _on_scan_error if it exists
        if hasattr(view, "_on_scan_error"):
             with patch("ui.views.storage_view.QMessageBox.warning") as mock_warn:
                 view._on_scan_error("Test Error")
                 mock_warn.assert_called()
        
    def test_mainwindow_errors(self, qapp):
        """Cover MainWindow error handling."""
        # Setup sidebar items error
        with patch("ui.main_window.SidebarWidget") as MockSidebar, \
             patch("ui.main_window.QVBoxLayout"), \
             patch("ui.main_window.QSplitter"), \
             patch("ui.main_window.QStackedWidget"):
             
             # Make add_item raise exception
             instance = MockSidebar.return_value
             instance.add_item.side_effect = Exception("Sidebar Error")
             
             with patch("ui.main_window.logger") as mock_log:
                 MainWindow()
                 mock_log.error.assert_called()
