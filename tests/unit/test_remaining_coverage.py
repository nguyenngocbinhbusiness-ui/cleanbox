"""Tests for remaining files coverage - app.py, main.py, service files, etc."""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from PyQt6.QtWidgets import QApplication
import sys


@pytest.fixture
def app(qtbot):
    """Provide QApplication instance."""
    return QApplication.instance() or QApplication([])


class TestAppCoverage:
    """Tests for app.py exception paths."""

    def test_app_init_normal(self, qtbot, app):
        """Test App.__init__ normal operation."""
        from app import App
        
        with patch('app.TrayIcon'):
            with patch('app.MainWindow'):
                with patch('app.StorageMonitor'):
                    application = App()
                    assert application is not None

    def test_handle_first_run_not_first(self, qtbot, app):
        """Test _handle_first_run when not first run."""
        from app import App
        
        with patch('app.TrayIcon'):
            with patch('app.MainWindow'):
                with patch('app.StorageMonitor'):
                    application = App()
                    # Call handle first run - should check config
                    application._handle_first_run()


class TestMainCoverage:
    """Tests for main.py exception paths."""

    def test_setup_logging_success(self):
        """Test setup_logging normal operation."""
        from main import setup_logging
        setup_logging()  # Should not raise

    def test_setup_logging_with_existing_config(self, tmp_path):
        """Test setup_logging when config dir exists."""
        from main import setup_logging
        # Just call it - should handle gracefully
        setup_logging()


class TestStorageMonitorServiceCoverage:
    """Tests for storage_monitor/service.py exception paths."""

    def test_init_normal(self, qtbot, app):
        """Test StorageMonitor.__init__ normal operation."""
        from features.storage_monitor.service import StorageMonitor
        
        monitor = StorageMonitor(threshold_gb=10, interval_seconds=60)
        assert monitor._threshold_gb == 10

    def test_start_normal(self, qtbot, app):
        """Test StorageMonitor.start normal operation."""
        from features.storage_monitor.service import StorageMonitor
        
        monitor = StorageMonitor()
        monitor.start()
        monitor.stop()  # Clean up

    def test_stop_normal(self, qtbot, app):
        """Test StorageMonitor.stop normal operation."""
        from features.storage_monitor.service import StorageMonitor
        
        monitor = StorageMonitor()
        monitor.stop()  # Should not raise


class TestTrayIconCoverage:
    """Tests for tray_icon.py exception paths."""

    def test_init_normal(self):
        """Test TrayIcon.__init__ normal operation."""
        from ui.tray_icon import TrayIcon
        
        tray = TrayIcon(
            on_cleanup=lambda: None,
            on_settings=lambda: None,
            on_exit=lambda: None
        )
        assert tray._on_cleanup is not None

    def test_init_exception(self):
        """Test TrayIcon.__init__ exception handling."""
        from ui.tray_icon import TrayIcon
        
        # Test with None callbacks (edge case)
        tray = TrayIcon()
        assert tray._on_cleanup is None

    def test_create_menu(self):
        """Test _create_menu normal operation."""
        from ui.tray_icon import TrayIcon
        
        tray = TrayIcon(
            on_cleanup=lambda: None,
            on_settings=lambda: None,
            on_exit=lambda: None
        )
        menu = tray._create_menu()
        assert menu is not None


class TestSharedUtilsCoverage:
    """Tests for shared/utils.py exception paths."""

    def test_retry_decorator_success(self):
        """Test retry decorator with successful function."""
        from shared.utils import retry
        
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = succeed()
        assert result == "success"
        assert call_count == 1

    def test_retry_decorator_with_retries(self):
        """Test retry decorator that fails then succeeds."""
        from shared.utils import retry
        
        call_count = 0
        
        @retry(max_attempts=3, delay=0.01)
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"
        
        result = fail_then_succeed()
        assert result == "success"
        assert call_count == 2

    def test_safe_execute_success(self):
        """Test safe_execute with successful function."""
        from shared.utils import safe_execute
        
        result = safe_execute(lambda: "success")
        assert result == "success"

    def test_safe_execute_failure(self):
        """Test safe_execute with failing function."""
        from shared.utils import safe_execute
        
        def failing():
            raise ValueError("Error")
        
        result = safe_execute(failing, default="default")
        assert result == "default"

    def test_format_size_from_folder_scanner(self):
        """Test format_size functionality via FolderInfo."""
        from features.folder_scanner.service import FolderInfo
        
        folder = FolderInfo(path="C:", name="C:", size_bytes=1024*1024, file_count=1, folder_count=0, children=[])
        assert "MB" in folder.size_formatted() or "KB" in folder.size_formatted()


class TestCleanupViewCoverage:
    """Tests for cleanup_view.py exception paths."""

    def test_init_normal(self, qtbot, app):
        """Test CleanupView.__init__ normal operation."""
        from ui.views.cleanup_view import CleanupView
        
        view = CleanupView()
        qtbot.addWidget(view)
        assert view is not None

    def test_setup_ui_creates_widgets(self, qtbot, app):
        """Test _setup_ui creates all required widgets."""
        from ui.views.cleanup_view import CleanupView
        
        view = CleanupView()
        qtbot.addWidget(view)
        
        assert hasattr(view, '_dir_list')
        assert hasattr(view, '_cleanup_btn')

    def test_update_directories(self, qtbot, app):
        """Test update_directories with data."""
        from ui.views.cleanup_view import CleanupView
        
        view = CleanupView()
        qtbot.addWidget(view)
        
        view.update_directories(["C:\\temp", "D:\\downloads"])
        assert view._dir_list.count() == 2

    def test_on_cleanup_clicked(self, qtbot, app):
        """Test _on_cleanup button click."""
        from ui.views.cleanup_view import CleanupView
        
        view = CleanupView()
        qtbot.addWidget(view)
        
        signals = []
        view.cleanup_requested.connect(lambda: signals.append(True))
        
        view._on_cleanup()
        assert len(signals) == 1
