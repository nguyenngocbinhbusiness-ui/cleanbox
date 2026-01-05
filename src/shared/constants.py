"""Shared constants for the CleanBox application."""
from pathlib import Path

# Application info
APP_NAME = "CleanBox"

# Paths
CONFIG_DIR = Path.home() / ".cleanbox"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Shared icon path - USE THIS EVERYWHERE
ASSETS_DIR = Path(__file__).parent.parent / "assets"
ICON_PATH = ASSETS_DIR / "icon.png"

# Default Configuration
DEFAULT_THRESHOLD_GB = 10
DEFAULT_POLLING_INTERVAL_SECONDS = 60
REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

# Markers
RECYCLE_BIN_MARKER = "__RECYCLE_BIN__"
