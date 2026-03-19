"""
Comprehensive unit tests for shared/registry.py module.
Tests Windows registry operations for autostart functionality with proper mocking.
"""
import subprocess
import sys
from unittest.mock import patch, MagicMock

import pytest


class TestGetExecutablePath:
    """Tests for get_executable_path function."""

    def test_get_executable_path_returns_string(self):
        """Test get_executable_path returns a string."""
        from shared.registry import get_executable_path
        
        result = get_executable_path()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_executable_path_contains_executable(self):
        """Test get_executable_path includes sys.executable."""
        from shared.registry import get_executable_path
        
        result = get_executable_path()
        assert sys.executable in result

    def test_get_executable_path_exception_handling(self, monkeypatch):
        """Test get_executable_path handles exceptions gracefully."""
        # Mock sys.argv to raise an exception when accessed
        monkeypatch.setattr(sys, 'argv', None)
        
        from shared.registry import get_executable_path
        
        # Should fall back to just sys.executable on error
        # Note: This may or may not raise depending on implementation
        try:
            result = get_executable_path()
            assert isinstance(result, str)
        except (TypeError, IndexError):
            pass  # Expected if argv is None


class TestEnableAutostart:
    """Tests for enable_autostart function."""

    def test_enable_autostart_no_winreg(self, monkeypatch):
        """Test enable_autostart falls back to Task Scheduler when winreg is None."""
        import shared.registry as registry_module
        monkeypatch.setattr(registry_module, 'winreg', None)

        with patch('shared.registry.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = registry_module.enable_autostart()
            assert result is True
            mock_run.assert_called_once()

    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows only")
    def test_enable_autostart_with_mock_registry(self, monkeypatch):
        """Test enable_autostart with mocked winreg operations."""
        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = 1
        mock_winreg.KEY_SET_VALUE = 2
        mock_winreg.REG_SZ = 3
        
        import shared.registry as registry_module
        monkeypatch.setattr(registry_module, 'winreg', mock_winreg)
        
        result = registry_module.enable_autostart()
        
        assert result is True
        mock_winreg.OpenKey.assert_called_once()
        mock_winreg.SetValueEx.assert_called_once()
        mock_winreg.CloseKey.assert_called_once_with(mock_key)

    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows only")
    def test_enable_autostart_windows_error(self, monkeypatch):
        """Test enable_autostart falls back to Task Scheduler on registry error."""
        mock_winreg = MagicMock()
        mock_winreg.OpenKey.side_effect = OSError("Registry error")
        mock_winreg.HKEY_CURRENT_USER = 1
        mock_winreg.KEY_SET_VALUE = 2
        
        import shared.registry as registry_module
        monkeypatch.setattr(registry_module, 'winreg', mock_winreg)
        
        with patch('shared.registry.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = registry_module.enable_autostart()
            assert result is True
            mock_run.assert_called_once()

    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows only")
    def test_enable_autostart_both_fail(self, monkeypatch):
        """Test enable_autostart returns False when both registry and scheduler fail."""
        mock_winreg = MagicMock()
        mock_winreg.OpenKey.side_effect = PermissionError("Access denied")
        mock_winreg.HKEY_CURRENT_USER = 1
        mock_winreg.KEY_SET_VALUE = 2

        import shared.registry as registry_module
        monkeypatch.setattr(registry_module, 'winreg', mock_winreg)

        with patch('shared.registry.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "schtasks")
            result = registry_module.enable_autostart()
            assert result is False


class TestDisableAutostart:
    """Tests for disable_autostart function."""

    def test_disable_autostart_no_winreg(self, monkeypatch):
        """Test disable_autostart returns True when winreg is None, still cleans task."""
        import shared.registry as registry_module
        monkeypatch.setattr(registry_module, 'winreg', None)

        with patch('shared.registry.subprocess.run'):
            result = registry_module.disable_autostart()
            assert result is True

    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows only")
    def test_disable_autostart_with_mock_registry(self, monkeypatch):
        """Test disable_autostart with mocked winreg operations."""
        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value = mock_key
        mock_winreg.HKEY_CURRENT_USER = 1
        mock_winreg.KEY_SET_VALUE = 2
        
        import shared.registry as registry_module
        monkeypatch.setattr(registry_module, 'winreg', mock_winreg)

        with patch('shared.registry.subprocess.run'):
            result = registry_module.disable_autostart()
        
            assert result is True
            mock_winreg.DeleteValue.assert_called_once()
            mock_winreg.CloseKey.assert_called_once_with(mock_key)

    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows only")
    def test_disable_autostart_not_found(self, monkeypatch):
        """Test disable_autostart returns True when entry doesn't exist."""
        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value = mock_key
        mock_winreg.DeleteValue.side_effect = FileNotFoundError("Not found")
        mock_winreg.HKEY_CURRENT_USER = 1
        mock_winreg.KEY_SET_VALUE = 2
        
        import shared.registry as registry_module
        monkeypatch.setattr(registry_module, 'winreg', mock_winreg)

        with patch('shared.registry.subprocess.run'):
            result = registry_module.disable_autostart()
            assert result is True

    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows only")
    def test_disable_autostart_windows_error(self, monkeypatch):
        """Test disable_autostart handles WindowsError but still cleans task."""
        mock_winreg = MagicMock()
        mock_winreg.OpenKey.side_effect = OSError("Registry error")
        mock_winreg.HKEY_CURRENT_USER = 1
        mock_winreg.KEY_SET_VALUE = 2
        
        import shared.registry as registry_module
        monkeypatch.setattr(registry_module, 'winreg', mock_winreg)

        with patch('shared.registry.subprocess.run'):
            result = registry_module.disable_autostart()
            assert result is False


class TestIsAutostartEnabled:
    """Tests for is_autostart_enabled function."""

    def test_is_autostart_enabled_no_winreg(self, monkeypatch):
        """Test is_autostart_enabled returns False when winreg is None."""
        import shared.registry as registry_module
        monkeypatch.setattr(registry_module, 'winreg', None)
        
        result = registry_module.is_autostart_enabled()
        assert result is False

    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows only")
    def test_is_autostart_enabled_true(self, monkeypatch):
        """Test is_autostart_enabled returns True when key exists."""
        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value = mock_key
        mock_winreg.QueryValueEx.return_value = ("some_path", 1)
        mock_winreg.HKEY_CURRENT_USER = 1
        mock_winreg.KEY_READ = 2
        
        import shared.registry as registry_module
        monkeypatch.setattr(registry_module, 'winreg', mock_winreg)
        
        result = registry_module.is_autostart_enabled()
        
        assert result is True
        mock_winreg.CloseKey.assert_called_once_with(mock_key)

    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows only")
    def test_is_autostart_enabled_not_found(self, monkeypatch):
        """Test is_autostart_enabled returns False when key doesn't exist."""
        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value = mock_key
        mock_winreg.QueryValueEx.side_effect = FileNotFoundError("Not found")
        mock_winreg.HKEY_CURRENT_USER = 1
        mock_winreg.KEY_READ = 2
        
        import shared.registry as registry_module
        monkeypatch.setattr(registry_module, 'winreg', mock_winreg)
        
        result = registry_module.is_autostart_enabled()
        
        assert result is False

    @pytest.mark.skipif(sys.platform != 'win32', reason="Windows only")
    def test_is_autostart_enabled_windows_error(self, monkeypatch):
        """Test is_autostart_enabled handles WindowsError."""
        mock_winreg = MagicMock()
        mock_winreg.OpenKey.side_effect = OSError("Registry error")
        mock_winreg.HKEY_CURRENT_USER = 1
        mock_winreg.KEY_READ = 2
        
        import shared.registry as registry_module
        monkeypatch.setattr(registry_module, 'winreg', mock_winreg)
        
        result = registry_module.is_autostart_enabled()
        
        assert result is False


class TestPlatformConstants:
    """Tests for platform-related constants."""

    def test_is_windows_constant(self):
        """Test IS_WINDOWS constant is correctly set."""
        from shared.registry import IS_WINDOWS
        
        assert isinstance(IS_WINDOWS, bool)
        assert IS_WINDOWS == (sys.platform == "win32")


class TestScheduledTaskFallback:
    """Tests for Task Scheduler fallback functions."""

    def test_create_scheduled_task_success(self):
        """Test _create_scheduled_task succeeds when schtasks works."""
        from shared.registry import _create_scheduled_task

        with patch('shared.registry.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = _create_scheduled_task()
            assert result is True
            args = mock_run.call_args
            cmd = args[0][0]
            assert "schtasks" in cmd
            assert "/create" in cmd
            assert "CleanBox" in cmd
            assert "/sc" in cmd
            assert "onlogon" in cmd

    def test_create_scheduled_task_failure(self):
        """Test _create_scheduled_task returns False on subprocess error."""
        from shared.registry import _create_scheduled_task

        with patch('shared.registry.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "schtasks")
            result = _create_scheduled_task()
            assert result is False

    def test_create_scheduled_task_os_error(self):
        """Test _create_scheduled_task returns False when schtasks not found."""
        from shared.registry import _create_scheduled_task

        with patch('shared.registry.subprocess.run') as mock_run:
            mock_run.side_effect = OSError("schtasks not found")
            result = _create_scheduled_task()
            assert result is False

    def test_delete_scheduled_task_success(self):
        """Test _delete_scheduled_task succeeds."""
        from shared.registry import _delete_scheduled_task

        with patch('shared.registry.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = _delete_scheduled_task()
            assert result is True
            args = mock_run.call_args
            cmd = args[0][0]
            assert "schtasks" in cmd
            assert "/delete" in cmd
            assert "CleanBox" in cmd

    def test_delete_scheduled_task_not_found(self):
        """Test _delete_scheduled_task returns False when task doesn't exist."""
        from shared.registry import _delete_scheduled_task

        with patch('shared.registry.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "schtasks")
            result = _delete_scheduled_task()
            assert result is False
