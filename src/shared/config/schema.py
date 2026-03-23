"""Config schema normalization helpers."""

from __future__ import annotations

from typing import Dict, List

from shared.utils import is_protected_path


def normalize_notified_drives(raw: object) -> Dict[str, float]:
    """Normalize notified-drive state to a drive->timestamp mapping."""
    normalized: Dict[str, float] = {}

    if isinstance(raw, dict):
        for drive, timestamp in raw.items():
            if not isinstance(drive, str):
                continue
            try:
                normalized[drive] = float(timestamp)
            except (TypeError, ValueError):
                normalized[drive] = 0.0
    elif isinstance(raw, list):
        for drive in raw:
            if isinstance(drive, str):
                normalized[drive] = 0.0

    return normalized


def filter_protected_cleanup_directories(
    directories: object,
) -> tuple[List[str], List[str]]:
    """
    Remove protected paths from cleanup directories.

    Returns:
        (filtered_directories, removed_directories)
    """
    if not isinstance(directories, list):
        return [], []

    filtered = [directory for directory in directories if not is_protected_path(directory)]
    removed = [directory for directory in directories if directory not in filtered]
    return filtered, removed
