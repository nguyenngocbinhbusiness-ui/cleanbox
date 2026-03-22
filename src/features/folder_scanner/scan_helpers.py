"""Helpers for folder scanner aggregation and timestamp handling."""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ScanAggregate:
    """Mutable aggregate for folder scan totals."""
    total_size: int = 0
    total_allocated: int = 0
    file_count: int = 0
    folder_count: int = 0
    max_mtime: float = 0.0

    def add_file(self, size_bytes: int, allocated_bytes: int, modified_time: float) -> None:
        self.total_size += size_bytes
        self.total_allocated += allocated_bytes
        if size_bytes > 0:
            self.file_count += 1
        if modified_time > self.max_mtime:
            self.max_mtime = modified_time

    def add_child(self, child_info: Any, modified_time: Optional[float] = None) -> None:
        self.total_size += child_info.size_bytes
        self.total_allocated += child_info.allocated_bytes
        self.file_count += child_info.file_count
        self.folder_count += child_info.folder_count
        if modified_time is not None and modified_time > self.max_mtime:
            self.max_mtime = modified_time


def parse_last_modified(value: str) -> Optional[float]:
    """Parse a stored folder timestamp string into epoch seconds."""
    if not value:
        return None
    try:
        return datetime.datetime.strptime(value, "%m/%d/%Y").timestamp()
    except (OSError, OverflowError, TypeError, ValueError):
        return None


def format_last_modified(timestamp: float) -> str:
    """Format an epoch timestamp using the folder-scanner display format."""
    try:
        if timestamp <= 0:
            return ""
        return datetime.datetime.fromtimestamp(timestamp).strftime("%m/%d/%Y")
    except (OSError, OverflowError, TypeError, ValueError):
        return ""
