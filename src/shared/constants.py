"""Shared constants for the CleanBox application."""
from pathlib import Path
from shared.constants_assets import resolve_assets_dir
from shared.protected_paths import build_protected_path_sets

# Application info
APP_NAME = "CleanBox"

# Paths
CONFIG_DIR = Path.home() / ".cleanbox"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _get_assets_dir() -> Path:
    """Get assets directory - handles both dev and frozen (PyInstaller) modes."""
    return resolve_assets_dir(__file__)


# Shared icon path - USE THIS EVERYWHERE
ASSETS_DIR = _get_assets_dir()
ICON_PATH = ASSETS_DIR / "icon.png"
CHECKBOX_CHECK_ICON_PATH = ASSETS_DIR / "checkbox-check.svg"

# Default Configuration
DEFAULT_THRESHOLD_GB = 10
DEFAULT_POLLING_INTERVAL_SECONDS = 60
REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

# Markers
RECYCLE_BIN_MARKER = "__RECYCLE_BIN__"


def _build_protected_paths() -> tuple[frozenset, frozenset]:
    """Build sets of protected system paths resolved from environment variables."""
    return build_protected_path_sets()


PROTECTED_PATHS, PROTECTED_PATH_PREFIXES = _build_protected_paths()
