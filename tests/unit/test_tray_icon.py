
import pytest
from unittest.mock import MagicMock, patch
import threading

from ui.tray_icon import TrayIcon, load_icon

class TestTrayIcon:
    
    @pytest.fixture
    def mock_callbacks(self):
        return {
            "cleanup": MagicMock(),
            "settings": MagicMock(),
            "exit": MagicMock()
        }
    
    @pytest.fixture
    def tray_icon(self, mock_callbacks):
        return TrayIcon(
            on_cleanup=mock_callbacks["cleanup"],
            on_settings=mock_callbacks["settings"],
            on_exit=mock_callbacks["exit"]
        )

    def test_load_icon_success(self):
        """Test loading icon from file."""
        with patch("ui.tray_icon.ICON_PATH") as mock_path, \
             patch("ui.tray_icon.Image.open") as mock_open:
            mock_path.exists.return_value = True
            
            icon = load_icon()
            
            mock_open.assert_called_once()
            assert icon == mock_open.return_value

    def test_load_icon_fallback(self):
        """Test fallback icon creation."""
        with patch("ui.tray_icon.ICON_PATH") as mock_path, \
             patch("ui.tray_icon.Image.new") as mock_new:
            # Case 1: File doesn't exist
            mock_path.exists.return_value = False
            load_icon()
            mock_new.assert_called()
            
            # Case 2: Error loading file
            mock_path.exists.return_value = True
            with patch("ui.tray_icon.Image.open", side_effect=Exception("Load Error")):
                load_icon()
                # Should fall back to new
                assert mock_new.call_count == 2

    def test_initialization(self, tray_icon, mock_callbacks):
        """Test correct initialization."""
        assert tray_icon._on_cleanup == mock_callbacks["cleanup"]
        assert tray_icon._on_settings == mock_callbacks["settings"]
        assert tray_icon._on_exit == mock_callbacks["exit"]
        assert tray_icon._icon is None
        assert tray_icon._thread is None

    def test_create_menu_success(self, tray_icon):
        """Test menu creation."""
        with patch("ui.tray_icon.pystray.Menu") as mock_menu:
            tray_icon._create_menu()
            # Should contain Cleanup, Settings, Separator, Exit
            mock_menu.assert_called()
            args = mock_menu.call_args[0]
            assert len(args) == 4

    def test_create_menu_error(self, tray_icon):
        """Test safe menu creation on error."""
        with patch("ui.tray_icon.pystray.Menu", side_effect=[Exception("Menu Error"), MagicMock()]) as mock_menu:
            menu = tray_icon._create_menu()
            # Should retry with simple menu (Exit only)
            assert mock_menu.call_count == 2

    def test_start_success(self, tray_icon):
        """Test starting the tray icon."""
        with patch("ui.tray_icon.Icon") as MockIcon, \
             patch("ui.tray_icon.load_icon"), \
             patch("ui.tray_icon.threading.Thread") as MockThread:
            
            tray_icon.start()
            
            MockIcon.assert_called_once()
            MockThread.assert_called_once()
            MockThread.return_value.start.assert_called_once()
            assert tray_icon._icon is not None

    def test_start_error(self, tray_icon):
        """Test start error handling."""
        with patch("ui.tray_icon.load_icon", side_effect=Exception("Start Error")), \
             patch("ui.tray_icon.logger") as mock_logger:
            tray_icon.start()
            mock_logger.error.assert_called()
            assert tray_icon._icon is None

    def test_stop_success(self, tray_icon):
        """Test stopping the tray icon."""
        mock_icon = MagicMock()
        tray_icon._icon = mock_icon
        tray_icon._thread = MagicMock()
        
        tray_icon.stop()
        
        mock_icon.stop.assert_called_once()
        assert tray_icon._icon is None
        assert tray_icon._thread is None

    def test_stop_error(self, tray_icon):
        """Test stop error handling."""
        mock_icon = MagicMock()
        mock_icon.stop.side_effect = Exception("Stop Error")
        tray_icon._icon = mock_icon
        
        with patch("ui.tray_icon.logger") as mock_logger:
            tray_icon.stop()
            # Should still cleanup resources
            mock_logger.error.assert_called()
            assert tray_icon._icon is None

    def test_callbacks(self, tray_icon, mock_callbacks):
        """Test callback handling."""
        # Cleanup
        tray_icon._handle_cleanup(None, None)
        mock_callbacks["cleanup"].assert_called_once()
        
        # Settings
        tray_icon._handle_settings(None, None)
        mock_callbacks["settings"].assert_called_once()
        
        # Exit
        with patch.object(tray_icon, "stop") as mock_stop:
            tray_icon._handle_exit(None, None)
            mock_stop.assert_called_once()
            mock_callbacks["exit"].assert_called_once()

    def test_callback_errors(self, tray_icon, mock_callbacks):
        """Test callback exceptions."""
        mock_callbacks["cleanup"].side_effect = Exception("Callback Error")
        mock_callbacks["settings"].side_effect = Exception("Callback Error")
        mock_callbacks["exit"].side_effect = Exception("Callback Error")
        
        with patch("ui.tray_icon.logger") as mock_logger:
            tray_icon._handle_cleanup(None, None)
            tray_icon._handle_settings(None, None)
            with patch.object(tray_icon, "stop"):
                tray_icon._handle_exit(None, None)
            
            assert mock_logger.error.call_count == 3
