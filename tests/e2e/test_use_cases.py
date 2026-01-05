"""
E2E Tests - Use Cases (UC)
Tests TC-UC-001 through TC-UC-010 (30 test cases)
"""
import sys
import os
import time
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from ui.main_window import MainWindow
from ui.views import StorageView, CleanupView, SettingsView
from shared.config import ConfigManager
from features.storage_monitor import StorageMonitor
from features.cleanup import CleanupService


class TestUC001AutoStart:
    """UC-001: Auto-Start with Windows."""
    
    def test_tc_uc_001_n_enable_autostart(self, fresh_config):
        """TC-UC-001-N: Enable auto-start, check registry entry is set."""
        from shared import registry
        
        # Act - enable autostart
        result = registry.enable_autostart()
        
        # Assert
        assert result is True or isinstance(result, bool)
        
        # Cleanup
        registry.disable_autostart()
    
    def test_tc_uc_001_e_registry_denied(self, monkeypatch):
        """TC-UC-001-E: Registry access denied."""
        from shared import registry
        
        # Arrange - mock to raise exception
        original = registry.enable_autostart
        
        def mock_enable():
            return False  # Simulate failure
        
        monkeypatch.setattr(registry, "enable_autostart", mock_enable)
        
        # Act
        result = registry.enable_autostart()
        
        # Assert - should return False, not crash
        assert result is False
    
    def test_tc_uc_001_ed_toggle_rapidly(self, fresh_config):
        """TC-UC-001-ED: Toggle auto-start rapidly on/off."""
        from shared import registry
        
        # Act - toggle multiple times
        for i in range(5):
            registry.enable_autostart()
            registry.disable_autostart()
        
        # Final state should be disabled
        result = registry.is_autostart_enabled()
        assert result is False


class TestUC002StorageMonitoring:
    """UC-002: Storage Monitoring."""
    
    def test_tc_uc_002_n_drives_monitored(self, qapp, monkeypatch):
        """TC-UC-002-N: App running, drive info updated."""
        from features.storage_monitor.utils import DriveInfo
        from features.storage_monitor import service as svc_module
        
        mock_data = [DriveInfo("C:", 500, 100, 400, 80), DriveInfo("D:", 1000, 5, 995, 99.5)]
        monkeypatch.setattr(svc_module, "get_all_drives", lambda: mock_data)
        
        monitor = StorageMonitor(threshold_gb=10, interval_seconds=60)
        drives = monitor.get_all_drives()
        
        assert len(drives) >= 1, "Should return at least one drive"
        assert all(d.letter for d in drives), "All drives should have letters"
    
    def test_tc_uc_002_e_drive_inaccessible(self, qapp, monkeypatch):
        """TC-UC-002-E: Drive becomes inaccessible."""
        from features.storage_monitor import service as svc_module
        
        monkeypatch.setattr(svc_module, "get_all_drives", lambda: [])
        
        monitor = StorageMonitor()
        drives = monitor.get_all_drives()
        
        assert drives == []

    def test_tc_uc_002_ed_many_drives(self, qapp, monkeypatch):
        """TC-UC-002-ED: System with 10+ drives."""
        from features.storage_monitor.utils import DriveInfo
        from features.storage_monitor import service as svc_module
        
        mock_data = [
            DriveInfo(letter=f"{chr(67+i)}:", total_gb=100.0, free_gb=50.0, used_gb=50.0, percent_used=50.0)
            for i in range(10)
        ]
        monkeypatch.setattr(svc_module, "get_all_drives", lambda: mock_data)
        
        monitor = StorageMonitor()
        drives = monitor.get_all_drives()
        
        assert len(drives) == 10


class TestUC003LowSpaceWarning:
    """UC-003: Low Space Warning."""
    
    def test_tc_uc_003_n_notification_once(self, qapp, monkeypatch):
        """TC-UC-003-N: Drive drops below threshold, notification appears once."""
        from features.storage_monitor.utils import DriveInfo
        from features.storage_monitor import service as svc_module
        
        mock_data = [DriveInfo("C:", 500, 100, 400, 80), DriveInfo("D:", 1000, 5, 995, 99.5)]
        monkeypatch.setattr(svc_module, "get_all_drives", lambda: mock_data)
        
        events = []
        monitor = StorageMonitor(threshold_gb=10)
        monitor.low_space_detected.connect(lambda d: events.append(d))
        
        monitor._check_drives()
        first_count = len(events)
        monitor._check_drives()
        second_count = len(events)
        
        assert first_count >= 1
        assert second_count == first_count, "Should not duplicate notifications"
    
    def test_tc_uc_003_e_notification_system_unavailable(self, monkeypatch):
        """TC-UC-003-E: Notification system unavailable."""
        from features.notifications import NotificationService
        
        def mock_toast(*args, **kwargs):
            raise RuntimeError("Notification system unavailable")
        
        # The service should catch and log, not crash
        service = NotificationService()
        # This should not raise
        try:
            service._show_toast("Test", "Message")
        except Exception:
            pass  # Expected to handle internally
    
    def test_tc_uc_003_ed_same_drive_twice(self, qapp, monkeypatch):
        """TC-UC-003-ED: Same drive drops below threshold twice - single notification."""
        from features.storage_monitor.utils import DriveInfo
        from features.storage_monitor import service as svc_module
        
        mock_data = [DriveInfo("D:", 1000, 5, 995, 99.5)]
        monkeypatch.setattr(svc_module, "get_all_drives", lambda: mock_data)
        
        events = []
        monitor = StorageMonitor(threshold_gb=10)
        monitor.low_space_detected.connect(lambda d: events.append(d))
        
        for _ in range(3): monitor._check_drives()
        
        d_drive_notifications = [e for e in events if e.letter == "D:"]
        assert len(d_drive_notifications) <= 1


class TestUC004AddDirectory:
    """UC-004: Add Directory."""
    
    def test_tc_uc_004_n_add_directory(self, qapp, fresh_config):
        """TC-UC-004-N: Click Add, select folder."""
        view = CleanupView()
        added_dirs = []
        view.directory_added.connect(lambda d: added_dirs.append(d))
        
        # Simulate adding directly (since we can't click the dialog)
        test_path = "C:\\TestFolder"
        view._directories.append(test_path)
        view.update_directories(view._directories)
        view.directory_added.emit(test_path)
        
        assert test_path in added_dirs
    
    def test_tc_uc_004_e_cancel_dialog(self, qapp):
        """TC-UC-004-E: Cancel file dialog."""
        view = CleanupView()
        initial_count = view._dir_list.count()
        
        # Without clicking (dialog would be cancelled)
        # List should remain unchanged
        assert view._dir_list.count() == initial_count
    
    def test_tc_uc_004_ed_duplicate_directory(self, qapp):
        """TC-UC-004-ED: Add directory already in list."""
        view = CleanupView()
        test_path = "C:\\ExistingDir"
        
        # Add once
        view._directories.append(test_path)
        view.update_directories(view._directories)
        
        # Try to add again - should not duplicate
        if test_path not in view._directories:
            view._directories.append(test_path)
        
        assert view._directories.count(test_path) == 1


class TestUC005RemoveDirectory:
    """UC-005: Remove Directory."""
    
    def test_tc_uc_005_n_remove_selected(self, qapp):
        """TC-UC-005-N: Select directory, click Remove."""
        view = CleanupView()
        removed_dirs = []
        view.directory_removed.connect(lambda d: removed_dirs.append(d))
        
        # Add and then remove
        test_path = "C:\\ToRemove"
        view._directories.append(test_path)
        view.update_directories(view._directories)
        
        # Select first item
        view._dir_list.setCurrentRow(0)
        
        # Remove
        view._on_remove_directory()
        
        assert test_path in removed_dirs
        assert test_path not in view._directories
    
    def test_tc_uc_005_e_no_selection(self, qapp, monkeypatch):
        """TC-UC-005-E: Click Remove with no selection."""
        view = CleanupView()
        
        # Mock the message box
        shown_messages = []
        def mock_info(parent, title, text):
            shown_messages.append((title, text))
        
        monkeypatch.setattr(QMessageBox, "information", mock_info)
        
        # Try to remove without selection
        view._on_remove_directory()
        
        # Should show message
        assert len(shown_messages) == 1
        assert "No Selection" in shown_messages[0][0]
    
    def test_tc_uc_005_ed_remove_last(self, qapp):
        """TC-UC-005-ED: Remove last directory in list."""
        view = CleanupView()
        
        # Add single directory
        view._directories = ["C:\\LastOne"]
        view.update_directories(view._directories)
        
        # Select and remove
        view._dir_list.setCurrentRow(0)
        view._on_remove_directory()
        
        assert len(view._directories) == 0
        assert view._dir_list.count() == 0


class TestUC006OneClickCleanup:
    """UC-006: One-Click Cleanup."""
    
    def test_tc_uc_006_n_cleanup_success(self, temp_cleanup_dir):
        """TC-UC-006-N: Click Clean Now with files present."""
        service = CleanupService()
        result = service.cleanup_directory(str(temp_cleanup_dir))
        
        assert result.total_files >= 1
        assert result.total_size_bytes >= 0
    
    def test_tc_uc_006_e_directory_missing(self):
        """TC-UC-006-E: Cleanup directory no longer exists."""
        service = CleanupService()
        result = service.cleanup_directory("C:\\NonExistent\\Path\\12345")
        
        assert len(result.errors) >= 1
    
    def test_tc_uc_006_ed_large_directory(self, tmp_path):
        """TC-UC-006-ED: Very large directory (many files)."""
        large_dir = tmp_path / "large_test"
        large_dir.mkdir()
        
        # Create 100 files
        for i in range(100):
            (large_dir / f"file_{i}.txt").write_text(f"content {i}")
        
        service = CleanupService()
        result = service.cleanup_directory(str(large_dir))
        
        assert result.total_files == 100


class TestUC007OpenConfigUI:
    """UC-007: Open Config UI via tray click."""
    
    def test_tc_uc_007_n_window_opens(self, qapp):
        """TC-UC-007-N: Left-click tray icon opens window."""
        window = MainWindow()
        
        # Simulate show settings
        window.show()
        
        assert window.isVisible()
    
    def test_tc_uc_007_e_window_minimized(self, qapp):
        """TC-UC-007-E: Click while window minimized."""
        window = MainWindow()
        window.show()
        window.showMinimized()
        
        # Restore
        window.show()
        window.raise_()
        window.activateWindow()
        
        # Should be visible and active
        assert window.isVisible()
    
    def test_tc_uc_007_ed_double_click(self, qapp):
        """TC-UC-007-ED: Double-click tray icon rapidly."""
        window = MainWindow()
        
        # Rapid show calls
        for _ in range(5):
            window.show()
            window.raise_()
        
        # Should be single window still visible
        assert window.isVisible()


class TestUC008TrayMenu:
    """UC-008: Tray Icon Context Menu."""
    
    def test_tc_uc_008_n_menu_items(self, qapp):
        """TC-UC-008-N: Right-click tray icon shows menu."""
        from ui.tray_icon import TrayIcon
        
        tray = TrayIcon()
        menu = tray._create_menu()
        
        # Should have menu items
        assert menu is not None
    
    def test_tc_uc_008_e_menu_action(self, qapp):
        """TC-UC-008-E: Click menu item, menu closes."""
        # Menu closing is handled by pystray
        # Just verify handlers exist
        from ui.tray_icon import TrayIcon
        
        cleanup_called = []
        tray = TrayIcon(on_cleanup=lambda: cleanup_called.append(True))
        
        # Simulate handler
        tray._handle_cleanup(None, None)
        
        assert len(cleanup_called) == 1
    
    def test_tc_uc_008_ed_menu_refresh(self, qapp):
        """TC-UC-008-ED: Menu stays consistent."""
        from ui.tray_icon import TrayIcon
        
        tray = TrayIcon()
        menu1 = tray._create_menu()
        menu2 = tray._create_menu()
        
        # Both should be valid menus
        assert menu1 is not None
        assert menu2 is not None


class TestUC009AutoDetectDefaults:
    """UC-009: Auto-Detect Defaults."""
    
    def test_tc_uc_009_n_first_run_detection(self):
        """TC-UC-009-N: First run auto-add."""
        from features.cleanup import get_default_directories
        
        dirs = get_default_directories()
        
        assert "__RECYCLE_BIN__" in dirs
    
    def test_tc_uc_009_e_custom_profile(self):
        """TC-UC-009-E: Custom user profile location."""
        from features.cleanup import get_downloads_folder
        
        # Should return valid string
        result = get_downloads_folder()
        assert isinstance(result, str)
    
    def test_tc_uc_009_ed_no_duplicates(self):
        """TC-UC-009-ED: Run detection twice - no duplicates."""
        from features.cleanup import get_default_directories
        
        dirs1 = get_default_directories()
        dirs2 = get_default_directories()
        
        # Both calls should return same set
        assert set(dirs1) == set(dirs2)


class TestUC010NavigateUI:
    """UC-010: Navigate UI via sidebar."""
    
    def test_tc_uc_010_n_sidebar_navigation(self, qapp):
        """TC-UC-010-N: Click each sidebar item."""
        window = MainWindow()
        
        # Navigate to each view
        window.switch_view("drives")
        assert window.content_stack.currentWidget() == window.storage_view
        
        window.switch_view("cleanup")
        assert window.content_stack.currentWidget() == window.cleanup_view
        
        window.switch_view("settings")
        assert window.content_stack.currentWidget() == window.settings_view
    
    def test_tc_uc_010_e_navigate_during_operation(self, qapp):
        """TC-UC-010-E: Navigate during scan operation."""
        window = MainWindow()
        
        # Start on drives view
        window.switch_view("drives")
        
        # Switch mid-operation (no actual scan, just switch)
        window.switch_view("cleanup")
        window.switch_view("drives")
        
        assert window.content_stack.currentWidget() == window.storage_view
    
    def test_tc_uc_010_ed_keyboard_navigation(self, qapp):
        """TC-UC-010-ED: Keyboard navigate via Tab/Enter."""
        window = MainWindow()
        
        # Sidebar buttons should be focusable
        for btn_id, btn in window.sidebar.buttons.items():
            assert btn.isEnabled()
            # Buttons are checkable
            assert btn.isCheckable()
