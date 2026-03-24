"""Asset path resolution helpers for shared constants."""
import sys
from pathlib import Path


def resolve_assets_dir(module_file: str) -> Path:
    """Resolve the assets directory for script and frozen executable modes."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "assets"
    return Path(module_file).parent.parent / "assets"
