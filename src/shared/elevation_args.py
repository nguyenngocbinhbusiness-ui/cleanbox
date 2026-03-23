"""Pure argument-building helpers for elevation launch flows."""

from __future__ import annotations

import os
from subprocess import list2cmdline  # nosec B404: used only for argv quoting, no shell execution


def build_frozen_params(argv: list[str]) -> str | None:
    """Build parameter string when relaunching an executable image."""
    if len(argv) <= 1:
        return None
    params = list2cmdline(argv[1:])
    return params or None


def build_script_launch(executable: str, argv: list[str]) -> tuple[str, str | None]:
    """Build executable and params when relaunching a script via Python."""
    exec_path = os.path.abspath(executable)
    script = os.path.abspath(argv[0]) if argv else ""
    params = list2cmdline([script, *argv[1:]]) if script else ""
    return exec_path, (params or None)
