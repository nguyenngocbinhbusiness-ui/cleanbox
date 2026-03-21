"""Windows elevation helpers used by startup and restart flows."""
import ctypes
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def is_admin() -> bool:
    """Return whether the current process has administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def get_elevation_launch_args() -> tuple[str, Optional[str], str]:
    """Build stable launch arguments for requesting elevation."""
    if getattr(sys, "frozen", False):
        executable = os.path.abspath(sys.argv[0] or sys.executable)
        if not executable.lower().endswith(".exe"):
            executable = os.path.abspath(sys.executable)
        params = subprocess.list2cmdline(sys.argv[1:]) if len(sys.argv) > 1 else ""
    else:
        executable = os.path.abspath(sys.executable)
        params = subprocess.list2cmdline(
            [os.path.abspath(sys.argv[0]), *sys.argv[1:]]
        )

    working_dir = str(Path(executable).resolve().parent)
    return executable, (params or None), working_dir


def request_admin_restart(show_cmd: int = 1) -> int:
    """Ask Windows to relaunch the current app with administrator rights."""
    executable, params, working_dir = get_elevation_launch_args()
    return ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        executable,
        params,
        working_dir,
        show_cmd,
    )
