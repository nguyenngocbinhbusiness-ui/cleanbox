
import pytest
import sys
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import main (requires path hack manipulation if not installed as package, 
# but tests/conftest.py might help. main.py is in src/)
from main import main, setup_logging, should_request_admin

class TestMainEntry:
    
    @pytest.fixture(autouse=True)
    def mock_sys_path(self):
        # Add src to sys.path so 'app' can be imported during patching
        # tests/unit/test_main_entry.py -> project/src
        src_path = Path(__file__).resolve().parents[2] / "src"
        # Preserve existing path to find stdlib and site-packages
        new_path = sys.path + [str(src_path)]
        with patch.object(sys, 'path', new_path):
            yield


    def test_setup_logging_success(self, tmp_path):
        """Test logging setup creates file."""
        # Patch CONFIG_DIR in main module. 
        # Since main.py imports CONFIG_DIR, we patch main.CONFIG_DIR
        with patch("main.CONFIG_DIR", tmp_path), \
             patch("logging.basicConfig") as mock_basic:
            
            setup_logging()
            
            assert (tmp_path).exists()
            mock_basic.assert_called_once()    

    def test_main_success(self):
        """Test main execution flow."""
        # Patch app.App because main() does 'from app import App'
        # app module is available because main.py modifies sys.path
        with patch("main.setup_logging") as mock_setup, \
             patch("main.should_request_admin", return_value=False), \
             patch("main.is_admin", return_value=True), \
             patch("app.App") as MockApp, \
             patch("logging.getLogger") as mock_logger:
            
            app_instance = MockApp.return_value
            app_instance.start.return_value = 0
            
            ret = main()
            
            assert ret == 0
            mock_setup.assert_called_once()
            MockApp.assert_called_once()
            app_instance.start.assert_called_once()

    def test_main_error_start(self):
        """Test main catches exceptions from App."""
        with patch("main.setup_logging"), \
             patch("main.should_request_admin", return_value=False), \
             patch("main.is_admin", return_value=True), \
             patch("app.App") as MockApp, \
             patch("logging.getLogger"):
            
            app_instance = MockApp.return_value
            app_instance.start.side_effect = Exception("Start failed")
            
            ret = main()
            
            assert ret == 1

    def test_main_fail_app_init(self):
         """Test main catches App init failure."""
         with patch("main.setup_logging"), \
              patch("main.should_request_admin", return_value=False), \
              patch("main.is_admin", return_value=True), \
              patch("app.App", side_effect=Exception("Init failed")), \
              patch("logging.getLogger"):
             
             ret = main()
             assert ret == 1

    def test_should_request_admin_reads_config(self):
        """Test persisted admin-start preference is read from config."""
        with patch("shared.config.ConfigManager") as MockConfig:
            MockConfig.return_value.run_as_admin_enabled = False
            assert should_request_admin() is False

    def test_main_skips_elevation_when_disabled(self):
        """Test main does not request elevation when setting is disabled."""
        with patch("main.setup_logging"), \
             patch("main.should_request_admin", return_value=False), \
             patch("main.is_admin", return_value=False), \
             patch("main.run_as_admin") as run_as_admin_mock, \
             patch("app.App") as MockApp, \
             patch("logging.getLogger"):

            MockApp.return_value.start.return_value = 0
            ret = main()

            assert ret == 0
            run_as_admin_mock.assert_not_called()
