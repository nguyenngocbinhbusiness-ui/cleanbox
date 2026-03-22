"""Filesystem action helpers for StorageView."""
import os
import subprocess
from pathlib import Path

import winshell

from shared.utils import is_protected_path


class ProtectedPathError(PermissionError):
    """Raised when an action targets a protected system path."""


def recycle_path(path: str) -> None:
    """Move a file or directory to the Recycle Bin."""
    if is_protected_path(path):
        raise ProtectedPathError(path)
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(path)
    winshell.delete_file(
        path,
        allow_undo=True,
        no_confirm=True,
        silent=False,
    )


def open_file_location(path: str) -> None:
    """Open the platform file browser and select the target."""
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(path)
    if os.name == "nt":
        subprocess.run(
            ["explorer", "/select,", str(target)],
            check=False,
            capture_output=True,
            text=True,
        )
        return
    os.startfile(str(target.parent if target.parent.exists() else target))
