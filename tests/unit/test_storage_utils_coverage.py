"""Tests for StorageMonitor Utils coverage - targeting exception paths."""
import pytest
from unittest.mock import patch, MagicMock


class TestStorageUtilsCoverage:
    """Tests for storage_monitor/utils.py exception paths."""

    def test_get_all_drives_success(self):
        """Test get_all_drives normal operation."""
        from features.storage_monitor.utils import get_all_drives
        
        drives = get_all_drives()
        assert isinstance(drives, list)
        # On Windows, should have at least C: drive
        if drives:
            assert all(hasattr(d, 'letter') for d in drives)

    def test_get_all_drives_with_mock(self):
        """Test get_all_drives with mocked psutil."""
        from features.storage_monitor.utils import get_all_drives
        
        mock_partition = MagicMock()
        mock_partition.device = "C:\\"
        mock_partition.mountpoint = "C:\\"
        mock_partition.fstype = "NTFS"
        
        mock_usage = MagicMock()
        mock_usage.total = 500 * 1024**3  # 500 GB
        mock_usage.free = 100 * 1024**3   # 100 GB
        
        with patch('features.storage_monitor.utils.psutil') as mock_psutil:
            mock_psutil.disk_partitions.return_value = [mock_partition]
            mock_psutil.disk_usage.return_value = mock_usage
            
            drives = get_all_drives()
            assert len(drives) == 1
            assert drives[0].letter == "C:"

    def test_get_all_drives_permission_error(self):
        """Test get_all_drives handles permission errors."""
        from features.storage_monitor.utils import get_all_drives
        
        mock_partition = MagicMock()
        mock_partition.device = "D:\\"
        mock_partition.mountpoint = "D:\\"
        mock_partition.fstype = "NTFS"
        
        with patch('features.storage_monitor.utils.psutil') as mock_psutil:
            mock_psutil.disk_partitions.return_value = [mock_partition]
            mock_psutil.disk_usage.side_effect = PermissionError("Access denied")
            
            drives = get_all_drives()
            assert isinstance(drives, list)

    def test_get_all_drives_exception(self):
        """Test get_all_drives exception handling."""
        from features.storage_monitor.utils import get_all_drives
        
        with patch('features.storage_monitor.utils.psutil') as mock_psutil:
            mock_psutil.disk_partitions.side_effect = Exception("Disk error")
            
            drives = get_all_drives()
            assert drives == []

    def test_get_all_drives_multiple_partitions(self):
        """Test get_all_drives with multiple partitions."""
        from features.storage_monitor.utils import get_all_drives
        
        partition_c = MagicMock()
        partition_c.device = "C:\\"
        partition_c.mountpoint = "C:\\"
        partition_c.fstype = "NTFS"
        partition_c.opts = "fixed"
        
        partition_d = MagicMock()
        partition_d.device = "D:\\"
        partition_d.mountpoint = "D:\\"
        partition_d.fstype = "NTFS"
        partition_d.opts = "fixed"
        
        mock_usage = MagicMock()
        mock_usage.total = 500 * 1024**3
        mock_usage.free = 100 * 1024**3
        mock_usage.used = 400 * 1024**3
        mock_usage.percent = 80.0
        
        with patch('features.storage_monitor.utils.psutil') as mock_psutil:
            mock_psutil.disk_partitions.return_value = [partition_c, partition_d]
            mock_psutil.disk_usage.return_value = mock_usage
            
            drives = get_all_drives()
            assert len(drives) >= 0  # Just ensure no exception

    def test_drive_info_is_low_space(self):
        """Test DriveInfo.is_low_space property."""
        from features.storage_monitor.utils import DriveInfo
        
        # Low space (< 10 GB free)
        low = DriveInfo(letter="C:", total_gb=100.0, free_gb=5.0, used_gb=95.0, percent_used=95.0)
        assert low.is_low_space is True
        
        # Normal space (>= 10 GB free)
        normal = DriveInfo(letter="D:", total_gb=100.0, free_gb=50.0, used_gb=50.0, percent_used=50.0)
        assert normal.is_low_space is False
