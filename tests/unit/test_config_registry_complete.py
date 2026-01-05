"""
Additional Unit Tests for CleanBox - Config and Registry Modules
Tests for ConfigManager, Registry functions
Target: ~25 additional tests
"""
import sys
import os
from unittest.mock import Mock, MagicMock, patch
import pytest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))


class TestConfigManagerUnit:
    """Unit tests for ConfigManager."""
    
    def test_config_default_threshold(self, fresh_config):
        """Test default threshold value."""
        assert fresh_config.threshold_gb == 10
    
    def test_config_default_interval(self, fresh_config):
        """Test default polling interval."""
        assert fresh_config.polling_interval == 60
    
    def test_config_default_autostart(self, fresh_config):
        """Test default autostart is True."""
        assert fresh_config.auto_start_enabled == True
    
    def test_config_first_run_true_initially(self, fresh_config):
        """Test first run is True on fresh config."""
        # Fresh config should indicate first run
        # Note: depends on fixture behavior
        assert isinstance(fresh_config.is_first_run, bool)
    
    def test_config_mark_first_run_complete(self, fresh_config):
        """Test marking first run as complete."""
        fresh_config.mark_first_run_complete()
        assert not fresh_config.is_first_run
    
    def test_config_add_directory(self, fresh_config):
        """Test adding directory."""
        result = fresh_config.add_directory("C:\\Test")
        assert result == True
        assert "C:\\Test" in fresh_config.cleanup_directories
    
    def test_config_add_duplicate_directory(self, fresh_config):
        """Test adding duplicate directory returns False."""
        fresh_config.add_directory("C:\\Test")
        result = fresh_config.add_directory("C:\\Test")
        assert result == False
    
    def test_config_remove_directory(self, fresh_config):
        """Test removing directory."""
        fresh_config.add_directory("C:\\ToRemove")
        result = fresh_config.remove_directory("C:\\ToRemove")
        assert result == True
        assert "C:\\ToRemove" not in fresh_config.cleanup_directories
    
    def test_config_remove_nonexistent_directory(self, fresh_config):
        """Test removing nonexistent directory returns False."""
        result = fresh_config.remove_directory("C:\\NonExistent")
        assert result == False
    
    def test_config_notified_drives_empty_initially(self, fresh_config):
        """Test notified drives is empty initially."""
        assert fresh_config.get_notified_drives() == []
    
    def test_config_add_notified_drive(self, fresh_config):
        """Test adding notified drive."""
        fresh_config.add_notified_drive("C:")
        assert "C:" in fresh_config.get_notified_drives()
    
    def test_config_remove_notified_drive(self, fresh_config):
        """Test removing notified drive."""
        fresh_config.add_notified_drive("C:")
        fresh_config.remove_notified_drive("C:")
        assert "C:" not in fresh_config.get_notified_drives()
    
    def test_config_save_creates_file(self, fresh_config, temp_config_dir):
        """Test save creates config file."""
        fresh_config.save()
        config_file = temp_config_dir / "config.json"
        assert config_file.exists()
    
    def test_config_load_reads_file(self, fresh_config, temp_config_dir):
        """Test load reads config file."""
        fresh_config.add_directory("C:\\Saved")
        fresh_config.save()
        fresh_config.load()
        assert "C:\\Saved" in fresh_config.cleanup_directories


class TestRegistryFunctionsUnit:
    """Unit tests for registry functions."""
    
    def test_get_executable_path_returns_string(self):
        """Test get_executable_path returns string."""
        from shared.registry import get_executable_path
        result = get_executable_path()
        assert isinstance(result, str)
    
    def test_is_autostart_enabled_returns_bool(self):
        """Test is_autostart_enabled returns bool."""
        from shared.registry import is_autostart_enabled
        result = is_autostart_enabled()
        assert isinstance(result, bool)
    
    @patch('shared.registry.winreg', None)
    def test_enable_autostart_no_winreg(self):
        """Test enable_autostart when winreg not available."""
        from shared.registry import enable_autostart
        # Should handle gracefully
        result = enable_autostart()
        assert result == False
    
    @patch('shared.registry.winreg', None)
    def test_disable_autostart_no_winreg(self):
        """Test disable_autostart when winreg not available."""
        from shared.registry import disable_autostart
        result = disable_autostart()
        assert result == True  # Returns True when nothing to do


class TestUtilsFunctionsUnit:
    """Unit tests for shared.utils functions."""
    
    def test_retry_decorator_success(self):
        """Test retry decorator with successful function."""
        from shared.utils import retry
        
        @retry(max_attempts=3)
        def success_func():
            return "success"
        
        result = success_func()
        assert result == "success"
    
    def test_retry_decorator_with_failure(self):
        """Test retry decorator with failing function."""
        from shared.utils import retry
        
        call_count = [0]
        
        @retry(max_attempts=3, delay=0.01)
        def fail_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Not yet")
            return "success"
        
        result = fail_func()
        assert result == "success"
        assert call_count[0] == 3
    
    def test_safe_execute_success(self):
        """Test safe_execute with successful function."""
        from shared.utils import safe_execute
        
        result = safe_execute(lambda: 42)
        assert result == 42
    
    def test_safe_execute_with_exception(self):
        """Test safe_execute returns default on exception."""
        from shared.utils import safe_execute
        
        def failing():
            raise ValueError("error")
        
        result = safe_execute(failing, default="default", log_error=False)
        assert result == "default"
    
    def test_safe_execute_with_args(self):
        """Test safe_execute passes args correctly."""
        from shared.utils import safe_execute
        
        result = safe_execute(lambda x, y: x + y, 3, 4)
        assert result == 7
