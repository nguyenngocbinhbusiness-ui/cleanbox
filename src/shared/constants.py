"""Shared constants for the CleanBox application."""
import os
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
CHECKBOX_CHECK_ICON_PATH = ASSETS_DIR / "checkbox-check.svg"

# Default Configuration
DEFAULT_THRESHOLD_GB = 10
DEFAULT_POLLING_INTERVAL_SECONDS = 60
REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

# Markers
RECYCLE_BIN_MARKER = "__RECYCLE_BIN__"


def _build_protected_paths() -> frozenset:
    """Build set of protected system paths resolved from environment variables."""
    paths = set()

    # Environment-based paths
    env_vars = [
        "WINDIR",               # C:\Windows
        "SYSTEMROOT",           # C:\Windows (alias)
        "PROGRAMFILES",         # C:\Program Files
        "PROGRAMFILES(X86)",    # C:\Program Files (x86)
        "PROGRAMDATA",          # C:\ProgramData
        "APPDATA",              # C:\Users\<user>\AppData\Roaming
        "LOCALAPPDATA",         # C:\Users\<user>\AppData\Local
        "USERPROFILE",          # C:\Users\<user>
        "SYSTEMDRIVE",          # C:
        "HOMEDRIVE",            # C:
        "COMMONPROGRAMFILES",   # C:\Program Files\Common Files
        "COMMONPROGRAMFILES(X86)",
    ]
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            paths.add(os.path.normcase(os.path.realpath(value)))

    # Well-known system directories
    windir = os.environ.get("WINDIR", r"C:\Windows")
    sys_drive = os.environ.get("SYSTEMDRIVE", "C:")
    static_paths = [
        os.path.join(windir, "System32"),
        os.path.join(windir, "SysWOW64"),
        os.path.join(windir, "WinSxS"),
        sys_drive + os.sep,                        # Boot drive root (C:\)
        sys_drive + os.sep + "Recovery",
        sys_drive + os.sep + "$Recycle.Bin",
        sys_drive + os.sep + "System Volume Information",
        sys_drive + os.sep + "Users",
    ]
    for p in static_paths:
        paths.add(os.path.normcase(os.path.realpath(p)))

    return frozenset(paths)


PROTECTED_PATHS: frozenset = _build_protected_paths()

