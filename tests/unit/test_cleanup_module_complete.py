"""
Additional Unit Tests for CleanBox - Cleanup Module
Tests for CleanupProgressWorker, CleanupService, DirectoryDetector
Target: ~25 additional tests
"""
import sys
import os
from unittest.mock import Mock, MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))


class TestCleanupProgressWorkerUnit:
    """Unit tests for CleanupProgressWorker."""
    
    def test_worker_init_stores_directories(self):
        """Test worker stores directories on init."""
        from features.cleanup.worker import CleanupProgressWorker
        dirs = ["C:/Test", "D:/Temp"]
        worker = CleanupProgressWorker(dirs)
        assert worker._directories == dirs
    
    def test_worker_init_creates_service(self):
        """Test worker creates cleanup service on init."""
        from features.cleanup.worker import CleanupProgressWorker
        worker = CleanupProgressWorker([])
        assert worker._service is not None
    
    def test_worker_emits_progress_for_each_directory(self, tmp_path):
        """Test worker emits progress for each directory."""
        from features.cleanup.worker import CleanupProgressWorker
        
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        
        worker = CleanupProgressWorker([str(dir1), str(dir2)])
        progress = []
        worker.progress_updated.connect(lambda c, t: progress.append((c, t)))
        worker.run()
        
        assert len(progress) >= 2
    
    def test_worker_handles_recycle_bin_marker(self):
        """Test worker handles __RECYCLE_BIN__ marker."""
        from features.cleanup.worker import CleanupProgressWorker
        
        worker = CleanupProgressWorker(["__RECYCLE_BIN__"])
        results = []
        worker.cleanup_finished.connect(lambda r: results.append(r))
        
        with patch.object(worker._service, 'empty_recycle_bin', return_value=Mock(
            total_files=0, total_folders=0, total_size_bytes=0, errors=[]
        )):
            worker.run()
        
        assert len(results) == 1
    
    def test_worker_accumulates_results(self, tmp_path):
        """Test worker accumulates results from multiple directories."""
        from features.cleanup.worker import CleanupProgressWorker
        
        (tmp_path / "file1.txt").write_text("x")
        (tmp_path / "file2.txt").write_text("y")
        
        worker = CleanupProgressWorker([str(tmp_path)])
        results = []
        worker.cleanup_finished.connect(lambda r: results.append(r))
        worker.run()
        
        assert results[0].total_files >= 2
    
    def test_worker_catches_exceptions(self):
        """Test worker catches exceptions during cleanup."""
        from features.cleanup.worker import CleanupProgressWorker
        
        worker = CleanupProgressWorker(["nonexistent/path"])
        results = []
        worker.cleanup_finished.connect(lambda r: results.append(r))
        worker.run()
        
        assert len(results) == 1
        # Should complete without crashing


class TestCleanupServiceUnit:
    """Unit tests for CleanupService."""
    
    def test_cleanup_directory_returns_result(self, tmp_path):
        """Test cleanup_directory returns CleanupResult."""
        from features.cleanup import CleanupService
        from features.cleanup.service import CleanupResult
        
        (tmp_path / "file.txt").write_text("x")
        service = CleanupService()
        result = service.cleanup_directory(str(tmp_path))
        
        assert isinstance(result, CleanupResult)
    
    def test_cleanup_directory_counts_files(self, tmp_path):
        """Test cleanup counts deleted files."""
        from features.cleanup import CleanupService
        
        (tmp_path / "f1.txt").write_text("a")
        (tmp_path / "f2.txt").write_text("b")
        
        service = CleanupService()
        result = service.cleanup_directory(str(tmp_path))
        
        assert result.total_files == 2
    
    def test_cleanup_directory_counts_folders(self, tmp_path):
        """Test cleanup counts deleted folders."""
        from features.cleanup import CleanupService
        
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file.txt").write_text("x")
        
        service = CleanupService()
        result = service.cleanup_directory(str(tmp_path))
        
        assert result.total_folders >= 1
    
    def test_cleanup_nonexistent_directory(self):
        """Test cleanup handles nonexistent directory."""
        from features.cleanup import CleanupService
        
        service = CleanupService()
        result = service.cleanup_directory("nonexistent/path/12345")
        
        assert result.total_files == 0
        assert len(result.errors) > 0
    
    def test_cleanup_result_size_mb(self):
        """Test CleanupResult calculates size_mb correctly."""
        from features.cleanup.service import CleanupResult
        
        result = CleanupResult(
            total_files=10,
            total_folders=2,
            total_size_bytes=1024 * 1024 * 5,  # 5MB
            errors=[]
        )
        
        assert result.total_size_mb == 5.0
    
    def test_cleanup_all_multiple_directories(self, tmp_path):
        """Test cleanup_all handles multiple directories."""
        from features.cleanup import CleanupService
        
        dir1 = tmp_path / "d1"
        dir2 = tmp_path / "d2"
        dir1.mkdir()
        dir2.mkdir()
        (dir1 / "f1.txt").write_text("a")
        (dir2 / "f2.txt").write_text("b")
        
        service = CleanupService()
        result = service.cleanup_all([str(dir1), str(dir2)])
        
        assert result.total_files >= 2


class TestDirectoryDetectorUnit:
    """Unit tests for DirectoryDetector."""
    
    def test_get_downloads_folder_returns_string(self):
        """Test get_downloads_folder returns string."""
        from features.cleanup.directory_detector import get_downloads_folder
        result = get_downloads_folder()
        assert isinstance(result, str)
    
    def test_get_default_directories_includes_recycle_bin(self):
        """Test get_default_directories includes recycle bin marker."""
        from features.cleanup.directory_detector import get_default_directories
        result = get_default_directories()
        assert "__RECYCLE_BIN__" in result
    
    def test_get_default_directories_returns_list(self):
        """Test get_default_directories returns list."""
        from features.cleanup.directory_detector import get_default_directories
        result = get_default_directories()
        assert isinstance(result, list)
    
    def test_get_downloads_folder_with_mock_home(self, monkeypatch, tmp_path):
        """Test get_downloads_folder with mocked home directory."""
        from features.cleanup.directory_detector import get_downloads_folder
        
        downloads = tmp_path / "Downloads"
        downloads.mkdir()
        
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        result = get_downloads_folder()
        
        assert "Downloads" in result or result == ""


class TestCleanupResultUnit:
    """Unit tests for CleanupResult dataclass."""
    
    def test_result_post_init_empty(self):
        """Test CleanupResult post init with empty errors."""
        from features.cleanup.service import CleanupResult
        result = CleanupResult()
        assert result.errors == []
    
    def test_result_size_mb_zero(self):
        """Test size_mb when bytes is zero."""
        from features.cleanup.service import CleanupResult
        result = CleanupResult()
        assert result.total_size_mb == 0.0
    
    def test_result_size_mb_large(self):
        """Test size_mb with large size."""
        from features.cleanup.service import CleanupResult
        result = CleanupResult(total_size_bytes=1024**3)  # 1GB
        assert result.total_size_mb == 1024.0
