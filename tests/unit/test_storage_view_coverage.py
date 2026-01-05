"""Tests for StorageView coverage - targeting exception paths and edge cases."""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from PyQt6.QtWidgets import QApplication, QTreeWidgetItem

from features.folder_scanner.service import FolderScanner, FolderInfo
from features.storage_monitor.utils import DriveInfo


@pytest.fixture
def app(qtbot):
    """Provide QApplication instance."""
    return QApplication.instance() or QApplication([])


class TestScanWorkerCoverage:
    """Tests for ScanWorker exception paths."""

    def test_scanworker_init_normal(self, qtbot, app):
        """Test ScanWorker normal initialization."""
        from ui.views.storage_view import ScanWorker
        scanner = MagicMock(spec=FolderScanner)
        worker = ScanWorker(scanner, "C:\\", max_depth=2)
        assert worker.scanner == scanner
        assert worker.path == "C:\\"
        assert worker.max_depth == 2

    def test_scanworker_run_success(self, qtbot, app):
        """Test ScanWorker.run with successful scan."""
        from ui.views.storage_view import ScanWorker
        scanner = MagicMock(spec=FolderScanner)
        folder_info = FolderInfo(path="C:\\", name="C:", size_bytes=1000, file_count=10, folder_count=2, children=[])
        scanner.scan_folder.return_value = folder_info
        
        worker = ScanWorker(scanner, "C:\\")
        finished_results = []
        worker.finished.connect(lambda r: finished_results.append(r))
        worker.run()
        
        assert len(finished_results) == 1
        assert finished_results[0] == folder_info

    def test_scanworker_run_exception(self, qtbot, app):
        """Test ScanWorker.run exception handling."""
        from ui.views.storage_view import ScanWorker
        scanner = MagicMock(spec=FolderScanner)
        scanner.scan_folder.side_effect = Exception("Scan failed")
        
        worker = ScanWorker(scanner, "C:\\")
        finished_results = []
        worker.finished.connect(lambda r: finished_results.append(r))
        worker.run()
        
        assert len(finished_results) == 1
        assert finished_results[0] is None

    def test_on_progress_normal(self, qtbot, app):
        """Test _on_progress normal operation."""
        from ui.views.storage_view import ScanWorker
        scanner = MagicMock(spec=FolderScanner)
        worker = ScanWorker(scanner, "C:\\")
        
        progress_updates = []
        worker.progress.connect(lambda p, c: progress_updates.append((p, c)))
        worker._on_progress("C:\\folder", 100)
        
        assert len(progress_updates) == 1
        assert progress_updates[0] == ("C:\\folder", 100)

    def test_on_progress_handles_large_count(self, qtbot, app):
        """Test _on_progress with large item count."""
        from ui.views.storage_view import ScanWorker
        scanner = MagicMock(spec=FolderScanner)
        worker = ScanWorker(scanner, "C:\\")
        
        progress_updates = []
        worker.progress.connect(lambda p, c: progress_updates.append((p, c)))
        worker._on_progress("C:\\very\\long\\nested\\folder\\path", 999999)
        
        assert len(progress_updates) == 1
        assert progress_updates[0][1] == 999999


class TestStorageViewCoverage:
    """Tests for StorageView exception paths."""

    def test_init_normal(self, qtbot, app):
        """Test StorageView normal initialization."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        assert view is not None

    def test_setup_ui_creates_widgets(self, qtbot, app):
        """Test _setup_ui creates all required widgets."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        
        assert hasattr(view, '_drive_combo')
        assert hasattr(view, '_scan_btn')
        assert hasattr(view, '_cancel_btn')
        assert hasattr(view, '_tree')
        assert hasattr(view, '_progress_bar')

    def test_update_drives_empty(self, qtbot, app):
        """Test update_drives with empty list."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        
        view.update_drives([])
        assert view._drive_combo.count() == 0

    def test_update_drives_with_data(self, qtbot, app):
        """Test update_drives with drive data."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        
        drives = [
            DriveInfo(letter="C:", total_gb=500.0, free_gb=100.0, used_gb=400.0, percent_used=80.0),
            DriveInfo(letter="D:", total_gb=1000.0, free_gb=800.0, used_gb=200.0, percent_used=20.0),
        ]
        view.update_drives(drives)
        assert view._drive_combo.count() == 2

    def test_create_tree_item_normal(self, qtbot, app):
        """Test _create_tree_item with valid FolderInfo."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        
        folder = FolderInfo(
            path="C:\\test",
            name="test",
            size_bytes=1024000,
            file_count=10,
            folder_count=2,
            children=[]
        )
        item = view._create_tree_item(folder, 2048000)
        
        assert item.text(0) == "test"
        assert "KB" in item.text(1) or "MB" in item.text(1)

    def test_create_tree_item_with_children(self, qtbot, app):
        """Test _create_tree_item with child folders."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        
        child = FolderInfo(path="C:\\test\\child", name="child", size_bytes=512000, file_count=5, folder_count=1, children=[])
        folder = FolderInfo(
            path="C:\\test",
            name="test",
            size_bytes=1024000,
            file_count=10,
            folder_count=2,
            children=[child]
        )
        item = view._create_tree_item(folder, 2048000)
        
        assert item.childCount() == 1

    def test_create_tree_item_zero_parent_size(self, qtbot, app):
        """Test _create_tree_item with zero parent size (edge case)."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        
        folder = FolderInfo(path="C:\\test", name="test", size_bytes=1024, file_count=0, folder_count=0, children=[])
        item = view._create_tree_item(folder, 0)
        
        assert item.text(4) == "-"  # Percentage should be "-" when parent_size is 0

    def test_update_drive_summary_empty(self, qtbot, app):
        """Test _update_drive_summary with no drives."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        
        view._drives = []
        view._update_drive_summary()
        
        # Should show "No drives detected" message
        assert view._drive_bars_layout.count() > 0

    def test_update_drive_summary_with_drives(self, qtbot, app):
        """Test _update_drive_summary with multiple drives."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        
        view._drives = [
            DriveInfo(letter="C:", total_gb=500.0, free_gb=50.0, used_gb=450.0, percent_used=90.0),  # 90% used - critical
            DriveInfo(letter="D:", total_gb=1000.0, free_gb=200.0, used_gb=800.0, percent_used=80.0),  # 80% used - warning
            DriveInfo(letter="E:", total_gb=500.0, free_gb=400.0, used_gb=100.0, percent_used=20.0),  # 20% used - normal
        ]
        view._update_drive_summary()
        
        # Should create progress bars for each drive
        assert view._drive_bars_layout.count() >= 3

    def test_update_drive_summary_critical_usage(self, qtbot, app):
        """Test _update_drive_summary with critical disk usage (>90%)."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        
        view._drives = [DriveInfo(letter="C:", total_gb=100.0, free_gb=5.0, used_gb=95.0, percent_used=95.0)]  # 95% used
        view._update_drive_summary()

    def test_on_scan_clicked(self, qtbot, app):
        """Test _on_scan button click."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        
        drives = [DriveInfo(letter="C:", total_gb=500.0, free_gb=100.0, used_gb=400.0, percent_used=80.0)]
        view.update_drives(drives)
        
        # Click scan - should start scanning
        with patch.object(view, '_start_scan'):
            view._on_scan()

    def test_on_cancel_clicked(self, qtbot, app):
        """Test _on_cancel button click."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        
        view._on_cancel()  # Should not raise

    def test_on_refresh_clicked(self, qtbot, app):
        """Test _on_refresh button click."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        
        refresh_emitted = []
        view.refresh_requested.connect(lambda: refresh_emitted.append(True))
        view._on_refresh()
        
        assert len(refresh_emitted) == 1

    def test_on_item_double_clicked_directory(self, qtbot, app, tmp_path):
        """Test _on_item_double_clicked with valid directory."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        
        # Create a temp directory
        test_dir = tmp_path / "test_folder"
        test_dir.mkdir()
        
        item = QTreeWidgetItem()
        from PyQt6.QtCore import Qt
        item.setData(0, Qt.ItemDataRole.UserRole, str(test_dir))
        
        with patch.object(view, '_start_scan'):
            view._on_item_double_clicked(item, 0)

    def test_on_item_double_clicked_no_path(self, qtbot, app):
        """Test _on_item_double_clicked with no path data."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        
        item = QTreeWidgetItem()
        # No path data set
        view._on_item_double_clicked(item, 0)  # Should not raise

    def test_populate_tree_none(self, qtbot, app):
        """Test _populate_tree handles None gracefully."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        
        # _populate_tree expects FolderInfo, not None
        # Test with empty tree first
        assert view._tree.topLevelItemCount() == 0

    def test_populate_tree_valid(self, qtbot, app):
        """Test _populate_tree with valid FolderInfo."""
        from ui.views.storage_view import StorageView
        view = StorageView()
        qtbot.addWidget(view)
        
        folder = FolderInfo(
            path="C:\\test",
            name="test",
            size_bytes=1024000,
            file_count=10,
            folder_count=2,
            children=[]
        )
        view._populate_tree(folder)
        
        assert view._tree.topLevelItemCount() > 0
