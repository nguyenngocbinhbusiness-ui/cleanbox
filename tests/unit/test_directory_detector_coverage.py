"""Tests for DirectoryDetector coverage - targeting exception paths."""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestDirectoryDetectorCoverage:
    """Tests for DirectoryDetector exception paths."""

    def test_get_downloads_folder_exists(self, tmp_path):
        """Test get_downloads_folder when folder exists."""
        from features.cleanup.directory_detector import get_downloads_folder
        
        with patch('features.cleanup.directory_detector.Path.home') as mock_home:
            mock_home.return_value = tmp_path
            downloads = tmp_path / "Downloads"
            downloads.mkdir()
            
            result = get_downloads_folder()
            assert result == str(downloads)

    def test_get_downloads_folder_not_exists(self, tmp_path):
        """Test get_downloads_folder when folder doesn't exist."""
        from features.cleanup.directory_detector import get_downloads_folder
        
        with patch('features.cleanup.directory_detector.Path.home') as mock_home:
            mock_home.return_value = tmp_path
            # Don't create Downloads folder
            
            result = get_downloads_folder()
            assert result == ""

    def test_get_downloads_folder_exception(self):
        """Test get_downloads_folder exception handling."""
        from features.cleanup.directory_detector import get_downloads_folder
        
        with patch('features.cleanup.directory_detector.Path.home', side_effect=Exception("Home error")):
            result = get_downloads_folder()
            assert result == ""

    def test_get_default_directories_success(self, tmp_path):
        """Test get_default_directories normal operation."""
        from features.cleanup.directory_detector import get_default_directories
        from shared.constants import RECYCLE_BIN_MARKER
        
        with patch('features.cleanup.directory_detector.get_downloads_folder') as mock_dl:
            mock_dl.return_value = str(tmp_path / "Downloads")
            
            result = get_default_directories()
            assert str(tmp_path / "Downloads") in result
            assert RECYCLE_BIN_MARKER in result

    def test_get_default_directories_no_downloads(self):
        """Test get_default_directories when Downloads not found."""
        from features.cleanup.directory_detector import get_default_directories
        from shared.constants import RECYCLE_BIN_MARKER
        
        with patch('features.cleanup.directory_detector.get_downloads_folder') as mock_dl:
            mock_dl.return_value = ""
            
            result = get_default_directories()
            assert RECYCLE_BIN_MARKER in result
            assert len(result) == 1

    def test_get_default_directories_exception(self):
        """Test get_default_directories exception handling."""
        from features.cleanup.directory_detector import get_default_directories
        from shared.constants import RECYCLE_BIN_MARKER
        
        with patch('features.cleanup.directory_detector.get_downloads_folder', side_effect=Exception("Error")):
            result = get_default_directories()
            assert result == [RECYCLE_BIN_MARKER]
