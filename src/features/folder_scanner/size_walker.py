"""Fast recursive folder size walking helpers."""

from __future__ import annotations

import os
from threading import Event
from typing import Callable, List, Optional, Tuple


def get_folder_size_fast(
    path: str,
    cancel_flag: Event,
    cluster_size: int,
    record_skip: Callable[[Exception], None],
    items_scanned: Optional[List[int]] = None,
    stats_scanned_entries: Optional[Callable[[], None]] = None,
    stats_scanned_files: Optional[Callable[[], None]] = None,
    stats_scanned_dirs: Optional[Callable[[], None]] = None,
) -> Tuple[int, int]:
    """Walk directory tree with os.scandir and return (total_bytes, allocated_bytes)."""
    total = 0
    allocated = 0
    stack = [path]

    while stack:
        if cancel_flag.is_set():
            return total, allocated
        current = stack.pop()
        try:
            with os.scandir(current) as iterator:
                for entry in iterator:
                    if cancel_flag.is_set():
                        return total, allocated
                    if items_scanned is not None:
                        items_scanned[0] += 1
                    if stats_scanned_entries is not None:
                        stats_scanned_entries()
                    try:
                        if entry.is_file(follow_symlinks=False):
                            file_size = entry.stat(follow_symlinks=False).st_size
                            total += file_size
                            allocated += ((file_size + cluster_size - 1) // cluster_size) * cluster_size
                            if stats_scanned_files is not None:
                                stats_scanned_files()
                        elif entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                            if stats_scanned_dirs is not None:
                                stats_scanned_dirs()
                    except Exception as exc:
                        record_skip(exc)
        except Exception as exc:
            record_skip(exc)
    return total, allocated
