"""Filesystem action helpers for StorageView."""
import ctypes
import os
from pathlib import Path

import winshell

from shared.utils import is_protected_path


class ProtectedPathError(PermissionError):
    """Raised when an action targets a protected system path."""


def _get_explorer_path() -> str:
    """Return the fully-qualified Explorer executable path on Windows."""
    windir = os.environ.get("WINDIR") or os.environ.get("SystemRoot") or r"C:\Windows"
    return str(Path(windir) / "explorer.exe")


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
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "open",
            _get_explorer_path(),
            f'/select,"{target}"',
            None,
            1,
        )
        return
    os.startfile(  # nosec B606: open local path in platform file browser
        str(target.parent if target.parent.exists() else target)
    )
