"""Policy helpers for cleanup directory management."""

from __future__ import annotations

from typing import Iterable, Tuple

from shared.constants import RECYCLE_BIN_MARKER
from shared.utils import is_protected_path


def format_directory_display(directory: str) -> str:
    """Return the UI label for a configured cleanup directory."""
    if directory == RECYCLE_BIN_MARKER:
        return "[Recycle Bin]"
    return directory


def validate_directory_addition(
    directory: str,
    existing_directories: Iterable[str],
) -> Tuple[bool, str]:
    """
    Validate whether a directory can be added.

    Returns:
        (True, "ok") when add is allowed.
        (False, "protected"|"duplicate"|"empty") when blocked.
    """
    if not directory:
        return False, "empty"
    if is_protected_path(directory):
        return False, "protected"
    if directory in set(existing_directories):
        return False, "duplicate"
    return True, "ok"
