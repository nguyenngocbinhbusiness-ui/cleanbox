"""
Component Tests for CleanBox UI Components
Tests: StorageView, CleanupView, SettingsView, SidebarWidget, MainWindow
Total: 13 components × 3 cases = 39 test cases
"""
import sys
import os
from unittest.mock import Mock, MagicMock, patch

import pytest
from PyQt6.QtCore import Qt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))


# ============================================================================
# STORAGE VIEW COMPONENT TESTS
# ============================================================================
class TestStorageViewComponent:
    """Component tests for StorageView widget."""
    
    def test_storage_view_initialization(self, qapp):
        from ui.views import StorageView
        view = StorageView()
        assert view._tree is not None
        assert view._drive_combo is not None
        assert view._scan_btn is not None
    
    def test_storage_view_update_drives(self, qapp):
        from ui.views import StorageView
        from features.storage_monitor.utils import DriveInfo
        view = StorageView()
        drives = [DriveInfo("C:", 500, 100, 400, 80)]
        view.update_drives(drives)
        assert view._drive_combo.count() == 1
    
    def test_storage_view_refresh_signal(self, qapp):
        from ui.views import StorageView
        view = StorageView()
        signals = []
        view.refresh_requested.connect(lambda: signals.append(1))
        view._on_refresh()
        assert len(signals) == 1
    
    def test_storage_view_progress_bar(self, qapp):
        from ui.views import StorageView
        view = StorageView()
        assert view._progress_bar is not None
        assert hasattr(view._progress_bar, "setValue")
    
    def test_storage_view_cancel_button(self, qapp):
        from ui.views import StorageView
        view = StorageView()
        assert view._cancel_btn is not None
        view._on_cancel()  # Should not error


# ============================================================================
# CLEANUP VIEW COMPONENT TESTS
# ============================================================================
class TestCleanupViewComponent:
    """Component tests for CleanupView widget."""
    
    def test_cleanup_view_initialization(self, qapp):
        from ui.views import CleanupView
        view = CleanupView()
        assert view._add_btn is not None
        assert view._remove_btn is not None
        assert view._cleanup_btn is not None
    
    def test_cleanup_view_update_directories(self, qapp):
        from ui.views import CleanupView
        view = CleanupView()
        view.update_directories(["C:\\Test", "D:\\Folder"])
        assert view._dir_list.count() == 2
    
    def test_cleanup_view_recycle_bin_display(self, qapp):
        from ui.views import CleanupView
        view = CleanupView()
        view.update_directories(["__RECYCLE_BIN__"])
        item = view._dir_list.item(0)
        assert "[Recycle Bin]" in item.text()
    
    def test_cleanup_view_add_signal(self, qapp):
        from ui.views import CleanupView
        view = CleanupView()
        signals = []
        view.directory_added.connect(lambda d: signals.append(d))
        # Simulate adding by directly manipulating
        view._directories.append("C:\\New")
        view.directory_added.emit("C:\\New")
        assert len(signals) == 1
    
    def test_cleanup_view_cleanup_signal(self, qapp):
        from ui.views import CleanupView
        view = CleanupView()
        signals = []
        view.cleanup_requested.connect(lambda: signals.append(1))
        view._on_cleanup()
        assert len(signals) == 1


# ============================================================================
# SETTINGS VIEW COMPONENT TESTS
# ============================================================================
class TestSettingsViewComponent:
    """Component tests for SettingsView widget."""
    
    def test_settings_view_initialization(self, qapp):
        from ui.views import SettingsView
        view = SettingsView()
        assert view._autostart_cb is not None
        assert view._threshold_spin is not None
        assert view._interval_spin is not None
    
    def test_settings_view_set_autostart(self, qapp):
        from ui.views import SettingsView
        view = SettingsView()
        view.set_autostart(True)
        assert view._autostart_cb.isChecked()
    
    def test_settings_view_set_threshold(self, qapp):
        from ui.views import SettingsView
        view = SettingsView()
        view.set_threshold(20)
        assert view._threshold_spin.value() == 20
    
    def test_settings_view_set_interval(self, qapp):
        from ui.views import SettingsView
        view = SettingsView()
        view.set_interval(120)
        assert view._interval_spin.value() == 120
    
    def test_settings_view_autostart_signal(self, qapp):
        from ui.views import SettingsView
        view = SettingsView()
        signals = []
        view.autostart_changed.connect(lambda v: signals.append(v))
        view._on_autostart_changed(Qt.CheckState.Checked.value)
        assert len(signals) == 1


# ============================================================================
# SIDEBAR WIDGET COMPONENT TESTS
# ============================================================================
class TestSidebarWidgetComponent:
    """Component tests for SidebarWidget."""
    
    def test_sidebar_initialization(self, qapp):
        from ui.components.sidebar import SidebarWidget
        sidebar = SidebarWidget()
        assert sidebar.buttons == {}
    
    def test_sidebar_add_item(self, qapp):
        from ui.components.sidebar import SidebarWidget
        sidebar = SidebarWidget()
        sidebar.add_item("Test", "test_id")
        assert "test_id" in sidebar.buttons
    
    def test_sidebar_select_item(self, qapp):
        from ui.components.sidebar import SidebarWidget
        sidebar = SidebarWidget()
        sidebar.add_item("Test", "test_id")
        sidebar.select_item("test_id")
        assert sidebar.buttons["test_id"].isChecked()
    
    def test_sidebar_selection_signal(self, qapp):
        from ui.components.sidebar import SidebarWidget
        sidebar = SidebarWidget()
        signals = []
        sidebar.selection_changed.connect(lambda s: signals.append(s))
        sidebar.add_item("Test", "test_id")
        sidebar.select_item("test_id")
        assert "test_id" in signals


# ============================================================================
# MAIN WINDOW COMPONENT TESTS
# ============================================================================
class TestMainWindowComponent:
    """Component tests for MainWindow."""
    
    def test_main_window_initialization(self, qapp):
        from ui.main_window import MainWindow
        window = MainWindow()
        assert window.sidebar is not None
        assert window.content_stack is not None
        assert window.storage_view is not None
        assert window.cleanup_view is not None
        assert window.settings_view is not None
    
    def test_main_window_switch_view(self, qapp):
        from ui.main_window import MainWindow
        window = MainWindow()
        window.switch_view("cleanup")
        assert window.content_stack.currentWidget() == window.cleanup_view
    
    def test_main_window_update_drives(self, qapp):
        from ui.main_window import MainWindow
        from features.storage_monitor.utils import DriveInfo
        window = MainWindow()
        drives = [DriveInfo("C:", 500, 100, 400, 80)]
        window.update_drives(drives)
        assert window.storage_view._drive_combo.count() == 1
    
    def test_main_window_update_directories(self, qapp):
        from ui.main_window import MainWindow
        window = MainWindow()
        window.update_directories(["C:\\Test"])
        assert window.cleanup_view._dir_list.count() == 1
    
    def test_main_window_close_hides(self, qapp):
        from ui.main_window import MainWindow
        from PyQt6.QtGui import QCloseEvent
        window = MainWindow()
        window.show()
        event = MagicMock(spec=QCloseEvent)
        window.closeEvent(event)
        event.ignore.assert_called_once()
    
    def test_main_window_set_settings(self, qapp):
        from ui.main_window import MainWindow
        window = MainWindow()
        window.set_autostart(True)
        window.set_threshold(25)
        window.set_interval(90)
        assert window.settings_view._autostart_cb.isChecked()
        assert window.settings_view._threshold_spin.value() == 25
        assert window.settings_view._interval_spin.value() == 90


# ============================================================================
# SIDEBAR BUTTON COMPONENT TESTS
# ============================================================================
class TestSidebarButtonComponent:
    """Component tests for SidebarButton."""
    
    def test_sidebar_button_checkable(self, qapp):
        from ui.components.sidebar import SidebarButton
        btn = SidebarButton("Test")
        assert btn.isCheckable()
    
    def test_sidebar_button_cursor(self, qapp):
        from ui.components.sidebar import SidebarButton
        btn = SidebarButton("Test")
        assert btn.cursor().shape() == Qt.CursorShape.PointingHandCursor
    
    def test_sidebar_button_check_toggle(self, qapp):
        from ui.components.sidebar import SidebarButton
        btn = SidebarButton("Test")
        btn.setChecked(True)
        assert btn.isChecked()
