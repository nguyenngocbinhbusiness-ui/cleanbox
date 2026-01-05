
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from features.folder_scanner.service import FolderScanner, FolderInfo

class TestFolderScannerCoverage:
    
    @pytest.fixture
    def scanner(self):
        return FolderScanner()

    def test_folder_info_properties(self):
        """Cover FolderInfo property errors."""
        # Create info with "bad" size (though int can't really fail, we can mock it)
        info = FolderInfo("path", "name", 0, 0, 0, [])
        
        # Test size_mb error
        # We can't easily force float division to fail unless size_bytes is non-numeric,
        # but type hinting says int. 
        # However, we can patch the properties or use a mock object.
        pass # The properties are simple try/except blocks around division.
             # Hard to fail unless we pass invalid types, which python allows.
        
        info.size_bytes = "not an int" 
        assert info.size_mb == 0.0
        assert info.size_gb == 0.0
        assert info.size_formatted() == "0 B"

    def test_scan_folder_recursive_error(self, scanner):
        """Cover _scan_recursive unhandled exception."""
        # Patch _scan_recursive to raise generic exception
        with patch.object(scanner, "_scan_recursive", side_effect=Exception("Recursive Error")), \
             patch("features.folder_scanner.service.logger") as mock_log:
            
            res = scanner.scan_folder("C:/Test")
            assert res is None
            mock_log.error.assert_called()

    def test_scan_recursive_permissions(self, scanner):
        """Cover permission handling inside loop."""
        # We need to simulate iterdir returning items that fail on is_file/is_dir or stat
        with patch("pathlib.Path.iterdir") as mock_iter:
            # Create a mock path entry that fails on is_file
            bad_entry = MagicMock()
            bad_entry.is_file.side_effect = Exception("Access Error")
            bad_entry.__str__.return_value = "C:/Test/Bad"
            
            mock_iter.return_value = [bad_entry]
            
            with patch("features.folder_scanner.service.logger") as mock_log:
                scanner.scan_folder("C:/Test")
                # Should catch exception and log debug
                mock_log.debug.assert_called()

    def test_get_folder_size_fast_cancellation(self, scanner):
        """Cover cancellation check in fast scan."""
        scanner._cancel_flag.set()
        assert scanner._get_folder_size_fast("C:/Test") == 0

    def test_get_folder_size_fast_errors(self, scanner):
        """Cover os.walk errors in fast scan."""
        # 1. os.walk raises PermissionError
        with patch("os.walk", side_effect=PermissionError("No Access")), \
             patch("features.folder_scanner.service.logger") as mock_log:
            
            scanner._get_folder_size_fast("C:/Test")
            mock_log.debug.assert_called()
            
        # 2. os.path.getsize raises OSError inside loop
        with patch("os.walk", return_value=[("root", [], ["file1"])]), \
             patch("os.path.getsize", side_effect=OSError("Disk Error")), \
             patch("features.folder_scanner.service.logger") as mock_log:
             
             scanner._get_folder_size_fast("C:/Test")
             mock_log.debug.assert_called()

    def test_scan_recursive_max_depth_reached(self, scanner):
        """Cover max_depth logic calling _get_folder_size_fast."""
        # max_depth=0 means we scan root but for children we use fast scan if we were to recurse?
        # Actually logic is: if current_depth < max_depth: recurse, else: fast scan.
        
        # Let's say max_depth=1. Root is depth 0.
        # Root has child "subdir". 
        # current_depth for subdir is 1. 1 < 1 is False.
        # So it should call fast scan for subdir.
        
        with patch("pathlib.Path.iterdir") as mock_iter, \
             patch.object(scanner, "_get_folder_size_fast", return_value=500) as mock_fast:
             
             # Mock entry
             sub = MagicMock()
             sub.is_file.return_value = False
             sub.is_dir.return_value = True
             sub.name = "Sub"
             sub.__str__.return_value = "C:/Root/Sub"
             
             mock_iter.return_value = [sub]
             
             res = scanner.scan_folder("C:/Root", max_depth=1)
             
             mock_fast.assert_called_with("C:/Root/Sub")
             assert res.size_bytes == 500
             assert res.children[0].size_bytes == 500

    def test_scan_file_stat_error(self, scanner):
        """Cover file stat permission error."""
        with patch("pathlib.Path.iterdir") as mock_iter:
            f = MagicMock()
            f.is_file.return_value = True
            f.stat.side_effect = PermissionError("Restricted")
            f.__str__.return_value = "C:/File"
            
            mock_iter.return_value = [f]
            
            with patch("features.folder_scanner.service.logger") as mock_log:
                scanner.scan_folder("C:/Root")
                mock_log.debug.assert_called()
