
import pytest
from unittest.mock import MagicMock, patch
from features.storage_monitor.service import StorageMonitor
from features.storage_monitor.utils import DriveInfo

class TestStorageMonitorCoverage:
    
    @pytest.fixture
    def monitor(self):
        return StorageMonitor(threshold_gb=10, interval_seconds=60)

    def test_start_error(self, monitor):
        """Cover start exception."""
        with patch.object(monitor, "_check_drives", side_effect=Exception("Start Error")), \
             patch("features.storage_monitor.service.logger") as mock_log:
            monitor.start()
            mock_log.error.assert_called()

    def test_stop_error(self, monitor):
        """Cover stop exception and finally block."""
        monitor._timer = MagicMock()
        monitor._timer.stop.side_effect = Exception("Stop Error")
        monitor._notified_drives = ["C:"]
        
        with patch("features.storage_monitor.service.logger") as mock_log:
            monitor.stop()
            # Error should be logged
            mock_log.error.assert_called()
            # Finally block should still run
            assert not monitor._notified_drives
            mock_log.debug.assert_called_with("Storage monitor resources cleaned up")

    def test_set_notified_drives_error(self, monitor):
        """Cover set_notified_drives exception."""
        # Pass something that raises exception on copy (not list)
        with patch("features.storage_monitor.service.logger") as mock_log:
            monitor.set_notified_drives(None) # None has no copy
            mock_log.error.assert_called()

    def test_get_low_space_drives_error(self, monitor):
        """Cover get_low_space_drives exception."""
        with patch("features.storage_monitor.service.get_all_drives", side_effect=Exception("Get Error")), \
             patch("features.storage_monitor.service.logger") as mock_log:
            res = monitor.get_low_space_drives()
            assert res == []
            mock_log.error.assert_called()

    def test_get_all_drives_error(self, monitor):
        """Cover get_all_drives exception."""
        with patch("features.storage_monitor.service.get_all_drives", side_effect=Exception("Get Error")), \
             patch("features.storage_monitor.service.logger") as mock_log:
            res = monitor.get_all_drives()
            assert res == []
            mock_log.error.assert_called()

    def test_check_drives_recovery(self, monitor):
        """Test recovery from low space (removing from notified list)."""
        # Initial state: C is notified
        monitor._notified_drives = ["C:"]
        
        # Scenario: C matches threshold now (not low)
        normal_drive = DriveInfo(letter="C:", total_gb=100.0, free_gb=20.0, used_gb=80.0, percent_used=80.0)
        
        with patch("features.storage_monitor.service.get_all_drives", return_value=[normal_drive]), \
             patch("features.storage_monitor.service.logger") as mock_log:
            
            monitor._check_drives()
            
            # Should be removed from notified
            assert "C:" not in monitor._notified_drives
            # Log recovery
            mock_log.info.assert_called()
            # No signal emitted for recovery, just log
    
    def test_check_drives_error(self, monitor):
        """Cover _check_drives exception."""
        with patch("features.storage_monitor.service.get_all_drives", side_effect=Exception("Check Error")), \
             patch("features.storage_monitor.service.logger") as mock_log:
            monitor._check_drives()
            mock_log.error.assert_called()
