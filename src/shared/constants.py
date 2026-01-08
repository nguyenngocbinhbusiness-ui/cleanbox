"""Shared constants for the CleanBox application."""
import sys
from pathlib import Path

# Application info
APP_NAME = "CleanBox"

# Paths
CONFIG_DIR = Path.home() / ".cleanbox"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _get_assets_dir() -> Path:
    """Get assets directory - handles both dev and frozen (PyInstaller) modes."""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe - assets bundled inside exe
        base_path = Path(sys._MEIPASS)
        return base_path / "assets"
    else:
        # Running as script - use relative path
        return Path(__file__).parent.parent / "assets"


# Shared icon path - USE THIS EVERYWHERE
ASSETS_DIR = _get_assets_dir()
ICON_PATH = ASSETS_DIR / "icon.png"

# Default Configuration
DEFAULT_THRESHOLD_GB = 10
DEFAULT_POLLING_INTERVAL_SECONDS = 60
REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

# Markers
RECYCLE_BIN_MARKER = "__RECYCLE_BIN__"

