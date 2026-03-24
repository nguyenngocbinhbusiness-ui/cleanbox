"""Shared utility functions for CleanBox application."""
import os
from shared import execution as _execution

from shared.constants import PROTECTED_PATHS, PROTECTED_PATH_PREFIXES

retry = _execution.retry
safe_execute = _execution.safe_execute


class ProtectedPathError(Exception):
    """Raised when an operation targets a protected system path."""
    pass


def normalize_path(path: str) -> str:
    """Normalize a path for consistent comparison (resolve symlinks, case-fold)."""
    return os.path.normcase(os.path.realpath(path))


def _path_matches_or_is_child(path: str, protected_root: str) -> bool:
    """Return True when path equals or is nested inside protected_root."""
    try:
        return os.path.commonpath([path, protected_root]) == protected_root
    except ValueError:
        # Different drives or invalid path components cannot be nested.
        return False


def is_protected_path(path: str) -> bool:
    """Check if a path is a protected system directory.

    Exact-match protection is used for user-profile and drive-root locations.
    Dangerous Windows system roots and special folders are blocked together
    with any subpaths underneath them.
    """
    normalized = normalize_path(path)
    if normalized in PROTECTED_PATHS:
        return True

    return any(
        _path_matches_or_is_child(normalized, protected_root)
        for protected_root in PROTECTED_PATH_PREFIXES
    )
