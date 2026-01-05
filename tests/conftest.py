"""
pytest configuration and fixtures for CleanBox E2E tests.
Uses pytest-qt for Qt widget testing and PyAutoGUI for desktop automation.
"""
import sys
import os
import json
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication

# Mock win11toast globally before any other imports
import sys
if "win11toast" not in sys.modules:
    mock_toast = MagicMock()
    sys.modules["win11toast"] = mock_toast
    sys.modules["win11toast"].toast = MagicMock()

if "winshell" not in sys.modules:
    sys.modules["winshell"] = MagicMock()

# psutil is a real library that works in tests - don't mock it globally

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from shared.constants import CONFIG_DIR, CONFIG_FILE
from shared.config import ConfigManager


@pytest.fixture(scope="session")
def qapp() -> Generator[QApplication, None, None]:
    """Create a QApplication instance for the entire test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary config directory for testing."""
    config_dir = tmp_path / ".cleanbox_test"
    config_dir.mkdir(parents=True, exist_ok=True)
    yield config_dir
    # Cleanup
    if config_dir.exists():
        shutil.rmtree(config_dir)


@pytest.fixture
def fresh_config(temp_config_dir: Path, monkeypatch) -> ConfigManager:
    """Create a fresh ConfigManager with isolated config."""
    # Monkeypatch the config paths
    monkeypatch.setattr("shared.constants.CONFIG_DIR", temp_config_dir)
    monkeypatch.setattr("shared.constants.CONFIG_FILE", temp_config_dir / "config.json")
    
    # Also patch in the config module
    import shared.config.manager as config_module
    monkeypatch.setattr(config_module, "CONFIG_DIR", temp_config_dir)
    monkeypatch.setattr(config_module, "CONFIG_FILE", temp_config_dir / "config.json")
    
    return ConfigManager()


@pytest.fixture
def temp_cleanup_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory with test files for cleanup testing."""
    cleanup_dir = tmp_path / "cleanup_test"
    cleanup_dir.mkdir(parents=True, exist_ok=True)
    
    # Create some test files
    (cleanup_dir / "file1.txt").write_text("test content 1")
    (cleanup_dir / "file2.txt").write_text("test content 2")
    
    # Create a subdirectory with files
    subdir = cleanup_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested_file.txt").write_text("nested content")
    
    yield cleanup_dir


@pytest.fixture
def mock_drives(monkeypatch):
    """Mock drive information for testing."""
    from features.storage_monitor.utils import DriveInfo
    
    mock_drive_list = [
        DriveInfo(letter="C:", total_gb=500.0, free_gb=100.0, used_gb=400.0, percent_used=80.0),
        DriveInfo(letter="D:", total_gb=1000.0, free_gb=5.0, used_gb=995.0, percent_used=99.5),  # Low space
    ]
    
    def mock_get_all_drives():
        return mock_drive_list
    
    from features.storage_monitor import utils
    monkeypatch.setattr(utils, "get_all_drives", mock_get_all_drives)
    
    return mock_drive_list


class TestResult:
    """Helper class to track test results."""
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []
    
    def mark_passed(self, tc_id: str):
        self.passed.append(tc_id)
    
    def mark_failed(self, tc_id: str, reason: str = ""):
        self.failed.append((tc_id, reason))
    
    def mark_skipped(self, tc_id: str, reason: str = ""):
        self.skipped.append((tc_id, reason))
    
    def summary(self) -> dict:
        return {
            "total": len(self.passed) + len(self.failed) + len(self.skipped),
            "passed": len(self.passed),
            "failed": len(self.failed),
            "skipped": len(self.skipped),
        }


@pytest.fixture(scope="session")
def test_results() -> TestResult:
    """Track test results across the session."""
    return TestResult()


@pytest.fixture(autouse=True)
def mock_toast(monkeypatch):
    """# Mock platform-specific modules that might not be available or desirable during tests"""
    sys.modules["win11toast"] = MagicMock()
    sys.modules["winshell"] = MagicMock()
    mock = MagicMock()
    
    # Patch win11toast module function
    import win11toast
    monkeypatch.setattr(win11toast, "toast", mock)
    
    # Patch local import in notification service if it's already imported
    try:
        import features.notifications.service as notification_service
        monkeypatch.setattr(notification_service, "toast", mock)
    except ImportError:
        pass
        
    yield mock
