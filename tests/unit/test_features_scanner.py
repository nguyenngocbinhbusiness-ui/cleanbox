
import pytest
import os
from unittest.mock import MagicMock, patch
from pathlib import Path
from features.folder_scanner.service import FolderScanner, FolderInfo

class TestFolderScanner:
    def test_scan_folder_valid(self, tmp_path):
        """Test scanning a valid folder structure."""
        # Setup
        d = tmp_path / "root"
        d.mkdir()
        (d / "file1.txt").write_text("a" * 100)
        (d / "subdir").mkdir()
        (d / "subdir" / "file2.txt").write_text("b" * 200)

        scanner = FolderScanner()
        
        # Test synchronous-like scan (mocking threads or running simple)
        # scan_folder uses ThreadPoolExecutor if logic allows?
        # Actually scan_folder is blocking in the sense it returns result?
        # No, it uses recursive helper.
        
        result = scanner.scan_folder(str(d))
        
        assert result.path == str(d)
        assert result.file_count == 2
        assert result.folder_count == 1
        assert result.size_bytes == 300
        assert len(result.children) >= 1

    def test_scan_folder_not_found(self):
        """Test scanning a non-existent folder."""
        scanner = FolderScanner()
        result = scanner.scan_folder("C:/NonExistentPath_XYZ_123")
        assert result.size_bytes == 0
        assert result.file_count == 0
        # Should handle gracefully, typically returns empty FolderInfo or valid object with 0 size

    def test_scan_folder_permission_error(self, tmp_path):
        """Test scanning with permission error (mocked)."""
        d = tmp_path / "perm_dir"
        d.mkdir()
        
        scanner = FolderScanner()
        
        # Patch os.scandir to raise PermissionError
        with patch("os.scandir", side_effect=PermissionError("Access denied")):
            result = scanner.scan_folder(str(d))
            # Should return safe result
            assert result.size_bytes == 0
            
    def test_cancel_scan(self, tmp_path):
        """Test cancellation logic."""
        scanner = FolderScanner()
        scanner.cancel()
        assert scanner._cancel_flag.is_set()
        
        # Try scanning while cancelled (call internal method that checks flag)
        # scan_folder clears flag, so we must test internal logic or mock side effect
        result = scanner._scan_recursive(str(tmp_path), 1, 0, None, [0])
        # Logic says: if is_set, return None
        assert result is None

    def test_scan_recursive_depth(self, tmp_path):
        """Test max depth logic."""
        # Create root/sub1/sub2/file.txt
        root = tmp_path / "root"
        sub1 = root / "sub1"
        sub2 = sub1 / "sub2"
        sub2.mkdir(parents=True)
        (sub2 / "file.txt").write_text("content")
        
        scanner = FolderScanner()
        
        # Scan with depth 1 (should see sub1, but not sub2 content logic details if overly strict?)
        # Actually recursive scan typically sums up everything, but "children" list usually limited by depth.
        # Check logic.
        
        result = scanner.scan_folder(str(root), max_depth=1)
        assert len(result.children) == 1 # sub1
        # sub1 children might be empty or present?
        # Usually depth affects the tree structure returned, not total size calculation?
        # Depends on implementation. Assuming total size is always calculated.
        assert result.size_bytes > 0
