"""Windows elevation helpers used by startup and restart flows."""
import ctypes
import os
import sys
from pathlib import Path
from typing import Optional

from shared.elevation_args import build_frozen_params, build_script_launch


def is_admin() -> bool:
    """Return whether the current process has administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def _get_current_process_image_path() -> str:
    """Return the full path to the current process image from Windows."""
    buffer = ctypes.create_unicode_buffer(32768)
    length = ctypes.windll.kernel32.GetModuleFileNameW(None, buffer, len(buffer))
    if length == 0:
        raise ctypes.WinError()
    return os.path.abspath(buffer.value)


def get_elevation_launch_args() -> tuple[str, Optional[str], str]:
    """Build stable launch arguments for requesting elevation."""
    argv0 = sys.argv[0] if sys.argv else ""
    launched_as_exe = Path(argv0).suffix.lower() == ".exe"

    if getattr(sys, "frozen", False) or launched_as_exe:
        executable = _get_current_process_image_path()
        params = build_frozen_params(sys.argv)
    else:
        executable, params = build_script_launch(sys.executable, sys.argv)

    working_dir = str(Path(executable).resolve().parent)
    return executable, params, working_dir


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
