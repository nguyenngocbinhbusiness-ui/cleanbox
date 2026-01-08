"""
Unit tests for shared/constants.py module.
Tests the _get_assets_dir() function in both frozen (PyInstaller) and script modes,
and validates all constant values.
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestGetAssetsDir:
    """Test _get_assets_dir() function for different execution modes."""

    def test_get_assets_dir_script_mode(self):
        """Test _get_assets_dir returns correct path when running as script."""
        # Ensure we're not in frozen mode
        if hasattr(sys, 'frozen'):
            delattr(sys, 'frozen')
        
        # Re-import to get fresh module state
        import importlib
        import shared.constants as constants_module
        importlib.reload(constants_module)
        
        assets_dir = constants_module._get_assets_dir()
        
        # Should return path relative to constants.py -> parent.parent / "assets"
        expected_parent = Path(constants_module.__file__).parent.parent / "assets"
        assert assets_dir == expected_parent
        assert isinstance(assets_dir, Path)

    def test_get_assets_dir_frozen_mode(self):
        """Test _get_assets_dir returns correct path when running as frozen exe."""
        # Simulate PyInstaller frozen mode
        mock_meipass = Path("C:/fake/meipass")
        
        with patch.object(sys, 'frozen', True, create=True):
            with patch.object(sys, '_MEIPASS', str(mock_meipass), create=True):
                # Need to call the function directly since module-level constant is already set
                from shared.constants import _get_assets_dir
                assets_dir = _get_assets_dir()
                
                expected = mock_meipass / "assets"
                assert assets_dir == expected

    def test_get_assets_dir_frozen_false_explicitly(self):
        """Test _get_assets_dir when frozen attribute exists but is False."""
        with patch.object(sys, 'frozen', False, create=True):
            from shared.constants import _get_assets_dir
            assets_dir = _get_assets_dir()
            
            # Should use script path, not MEIPASS
            assert isinstance(assets_dir, Path)
            assert "assets" in str(assets_dir)


class TestConstantValues:
    """Test that constant values are correct types and expected values."""

    def test_app_name_is_string(self):
        """Test APP_NAME is a non-empty string."""
        from shared.constants import APP_NAME
        
        assert isinstance(APP_NAME, str)
        assert len(APP_NAME) > 0
        assert APP_NAME == "CleanBox"

    def test_config_paths_are_path_objects(self):
        """Test CONFIG_DIR and CONFIG_FILE are Path objects."""
        from shared.constants import CONFIG_DIR, CONFIG_FILE
        
        assert isinstance(CONFIG_DIR, Path)
        assert isinstance(CONFIG_FILE, Path)
        # CONFIG_FILE should be inside CONFIG_DIR
        assert CONFIG_FILE.parent == CONFIG_DIR

    def test_config_file_has_json_extension(self):
        """Test CONFIG_FILE has .json extension."""
        from shared.constants import CONFIG_FILE
        
        assert CONFIG_FILE.suffix == ".json"
        assert CONFIG_FILE.name == "config.json"

    def test_default_threshold_gb_is_positive_int(self):
        """Test DEFAULT_THRESHOLD_GB is a positive integer."""
        from shared.constants import DEFAULT_THRESHOLD_GB
        
        assert isinstance(DEFAULT_THRESHOLD_GB, int)
        assert DEFAULT_THRESHOLD_GB > 0
        assert DEFAULT_THRESHOLD_GB == 10

    def test_default_polling_interval_is_positive(self):
        """Test DEFAULT_POLLING_INTERVAL_SECONDS is positive."""
        from shared.constants import DEFAULT_POLLING_INTERVAL_SECONDS
        
        assert isinstance(DEFAULT_POLLING_INTERVAL_SECONDS, int)
        assert DEFAULT_POLLING_INTERVAL_SECONDS > 0
        assert DEFAULT_POLLING_INTERVAL_SECONDS == 60

    def test_registry_key_is_valid_path(self):
        """Test REGISTRY_KEY is a valid Windows registry path string."""
        from shared.constants import REGISTRY_KEY
        
        assert isinstance(REGISTRY_KEY, str)
        assert "Windows" in REGISTRY_KEY
        assert "Run" in REGISTRY_KEY

    def test_recycle_bin_marker_is_string(self):
        """Test RECYCLE_BIN_MARKER is a recognizable marker string."""
        from shared.constants import RECYCLE_BIN_MARKER
        
        assert isinstance(RECYCLE_BIN_MARKER, str)
        assert len(RECYCLE_BIN_MARKER) > 0
        # Should be a special marker, not a real path
        assert "__" in RECYCLE_BIN_MARKER


class TestAssetPaths:
    """Test asset-related paths and constants."""

    def test_assets_dir_is_path(self):
        """Test ASSETS_DIR is a Path object."""
        from shared.constants import ASSETS_DIR
        
        assert isinstance(ASSETS_DIR, Path)

    def test_icon_path_is_path(self):
        """Test ICON_PATH is a Path object."""
        from shared.constants import ICON_PATH
        
        assert isinstance(ICON_PATH, Path)
        assert ICON_PATH.suffix == ".png"
        assert ICON_PATH.name == "icon.png"

    def test_icon_path_inside_assets_dir(self):
        """Test ICON_PATH is inside ASSETS_DIR."""
        from shared.constants import ASSETS_DIR, ICON_PATH
        
        assert ICON_PATH.parent == ASSETS_DIR
