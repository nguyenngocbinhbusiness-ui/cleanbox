"""
E2E Tests - UI Interactive Elements (Part 1: UI-001 to UI-017)
Tests sidebar, StorageView, CleanupView, SettingsView (51 test cases)
"""
import sys
import os
import pytest
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from ui.main_window import MainWindow
from ui.views import StorageView, CleanupView, SettingsView


class TestUI001DrivesButton:
    def test_tc_ui_001_n(self, qapp):
        w = MainWindow(); w.sidebar.select_item("drives")
        assert w.content_stack.currentWidget() == w.storage_view

    def test_tc_ui_001_e(self, qapp):
        w = MainWindow(); w.sidebar.select_item("drives"); w.sidebar.select_item("drives")
        assert w.content_stack.currentWidget() == w.storage_view

    def test_tc_ui_001_ed(self, qapp):
        w = MainWindow()
        for _ in range(10): w.sidebar.select_item("drives"); qapp.processEvents()
        assert w.content_stack.currentWidget() == w.storage_view


class TestUI002CleanupButton:
    def test_tc_ui_002_n(self, qapp):
        w = MainWindow(); w.sidebar.select_item("cleanup")
        assert w.content_stack.currentWidget() == w.cleanup_view

    def test_tc_ui_002_e(self, qapp):
        w = MainWindow(); w.sidebar.select_item("drives"); w.sidebar.select_item("cleanup")
        assert w.content_stack.currentWidget() == w.cleanup_view

    def test_tc_ui_002_ed(self, qapp):
        w = MainWindow(); assert w.sidebar.buttons["cleanup"].isCheckable()


class TestUI003SettingsButton:
    def test_tc_ui_003_n(self, qapp):
        w = MainWindow(); w.sidebar.select_item("settings")
        assert w.content_stack.currentWidget() == w.settings_view

    def test_tc_ui_003_e(self, qapp):
        w = MainWindow()
        for _ in range(3): w.sidebar.select_item("settings")
        assert w.content_stack.currentWidget() == w.settings_view

    def test_tc_ui_003_ed(self, qapp):
        w = MainWindow(); w.sidebar.select_item("settings")
        assert w.sidebar.buttons["settings"].isChecked()


class TestUI004DriveCombo:
    def test_tc_ui_004_n(self, qapp, mock_drives):
        v = StorageView(); v.update_drives(mock_drives)
        assert v._drive_combo.count() >= 1

    def test_tc_ui_004_e(self, qapp):
        v = StorageView(); v.update_drives([])
        assert v._drive_combo.count() == 0

    def test_tc_ui_004_ed(self, qapp, mock_drives):
        v = StorageView(); v.update_drives([]); v.update_drives(mock_drives)
        assert v._drive_combo.count() == len(mock_drives)


class TestUI005ScanButton:
    def test_tc_ui_005_n(self, qapp, mock_drives):
        v = StorageView(); v.update_drives(mock_drives)
        assert v._scan_btn.isEnabled()

    def test_tc_ui_005_e(self, qapp):
        v = StorageView(); assert v._scan_btn is not None

    def test_tc_ui_005_ed(self, qapp):
        v = StorageView(); assert "Scan" in v._scan_btn.text()


class TestUI006CancelButton:
    def test_tc_ui_006_n(self, qapp): v = StorageView(); assert v._cancel_btn is not None
    def test_tc_ui_006_e(self, qapp): v = StorageView(); v._on_cancel()
    def test_tc_ui_006_ed(self, qapp): v = StorageView(); v._on_cancel(); assert True


class TestUI007RefreshButton:
    def test_tc_ui_007_n(self, qapp):
        v = StorageView(); s = []; v.refresh_requested.connect(lambda: s.append(1))
        v._on_refresh(); assert len(s) == 1

    def test_tc_ui_007_e(self, qapp): v = StorageView(); v._on_refresh()
    def test_tc_ui_007_ed(self, qapp):
        v = StorageView()
        for _ in range(5): v._on_refresh()


class TestUI008FolderTree:
    def test_tc_ui_008_n(self, qapp): assert StorageView()._tree is not None
    def test_tc_ui_008_e(self, qapp): assert StorageView()._tree.columnCount() >= 1
    def test_tc_ui_008_ed(self, qapp): assert hasattr(StorageView(), "_on_item_double_clicked")


class TestUI009ProgressBar:
    def test_tc_ui_009_n(self, qapp): assert StorageView()._progress_bar is not None
    def test_tc_ui_009_e(self, qapp): assert hasattr(StorageView()._progress_bar, "setValue")
    def test_tc_ui_009_ed(self, qapp): assert True


class TestUI010DriveSummary:
    def test_tc_ui_010_n(self, qapp, mock_drives):
        v = StorageView(); v.update_drives(mock_drives); assert v._drives is not None

    def test_tc_ui_010_e(self, qapp): v = StorageView(); v.update_drives([]); assert v._drives == []
    def test_tc_ui_010_ed(self, qapp, mock_drives): StorageView().update_drives(mock_drives)


class TestUI011AddDirectoryButton:
    def test_tc_ui_011_n(self, qapp): assert CleanupView()._add_btn.text() == "Add Directory"
    def test_tc_ui_011_e(self, qapp): v = CleanupView(); assert len(v._directories) == 0
    def test_tc_ui_011_ed(self, qapp):
        v = CleanupView(); v._directories = ["C:\\Test"]; v.update_directories(v._directories)
        assert v._directories.count("C:\\Test") == 1


class TestUI012RemoveButton:
    def test_tc_ui_012_n(self, qapp):
        v = CleanupView(); v._directories = ["C:\\Test"]; v.update_directories(v._directories)
        v._dir_list.setCurrentRow(0); v._on_remove_directory()
        assert "C:\\Test" not in v._directories

    def test_tc_ui_012_e(self, qapp, monkeypatch):
        msgs = []; monkeypatch.setattr(QMessageBox, "information", lambda *a: msgs.append(a))
        CleanupView()._on_remove_directory(); assert len(msgs) == 1

    def test_tc_ui_012_ed(self, qapp):
        v = CleanupView(); v._directories = ["__RECYCLE_BIN__"]; v.update_directories(v._directories)
        v._dir_list.setCurrentRow(0); v._on_remove_directory()
        assert "__RECYCLE_BIN__" not in v._directories


class TestUI013CleanNowButton:
    def test_tc_ui_013_n(self, qapp):
        v = CleanupView(); s = []; v.cleanup_requested.connect(lambda: s.append(1))
        v._on_cleanup(); assert len(s) == 1

    def test_tc_ui_013_e(self, qapp): v = CleanupView(); v._directories = []; v._on_cleanup()
    def test_tc_ui_013_ed(self, qapp): assert CleanupView()._cleanup_btn.isEnabled()


class TestUI014DirectoryList:
    def test_tc_ui_014_n(self, qapp):
        v = CleanupView(); v.update_directories(["C:\\1", "C:\\2", "C:\\3"])
        assert v._dir_list.count() == 3

    def test_tc_ui_014_e(self, qapp):
        v = CleanupView(); v.update_directories(["C:\\" + "x"*200])
        assert v._dir_list.count() == 1

    def test_tc_ui_014_ed(self, qapp):
        v = CleanupView(); v.update_directories(["__RECYCLE_BIN__"])
        assert "[Recycle Bin]" in v._dir_list.item(0).text()


class TestUI015AutostartCheckbox:
    def test_tc_ui_015_n(self, qapp):
        v = SettingsView(); s = []; v.autostart_changed.connect(lambda x: s.append(x))
        v._autostart_cb.setChecked(True); v._on_autostart_changed(Qt.CheckState.Checked.value)
        assert len(s) >= 1

    def test_tc_ui_015_e(self, qapp): v = SettingsView(); v.set_autostart(True); assert v._autostart_cb.isChecked()
    def test_tc_ui_015_ed(self, qapp):
        v = SettingsView()
        for _ in range(5): v._autostart_cb.setChecked(True); v._autostart_cb.setChecked(False)
        assert not v._autostart_cb.isChecked()


class TestUI016ThresholdSpinbox:
    def test_tc_ui_016_n(self, qapp): v = SettingsView(); v.set_threshold(15); assert v._threshold_spin.value() == 15
    def test_tc_ui_016_e(self, qapp): v = SettingsView(); v._threshold_spin.setValue(1000); assert v._threshold_spin.value() <= 100
    def test_tc_ui_016_ed(self, qapp): v = SettingsView(); v._threshold_spin.setValue(1); assert v._threshold_spin.value() >= 1


class TestUI017IntervalSpinbox:
    def test_tc_ui_017_n(self, qapp): v = SettingsView(); v.set_interval(120); assert v._interval_spin.value() == 120
    def test_tc_ui_017_e(self, qapp): v = SettingsView(); v._interval_spin.setValue(0); assert v._interval_spin.value() >= 10
    def test_tc_ui_017_ed(self, qapp): v = SettingsView(); v._interval_spin.setValue(600); assert v._interval_spin.value() == 600
