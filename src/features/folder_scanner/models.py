"""Core models for folder scanner."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from features.folder_scanner.format_utils import format_size


@dataclass
class FileEntry:
    """Information about a single file."""

    name: str
    path: str
    size_bytes: int
    allocated_bytes: int


@dataclass
class ScanStats:
    """Aggregated scan/completeness counters."""

    scanned_entries: int = 0
    scanned_files: int = 0
    scanned_dirs: int = 0
    skipped_count: int = 0
    skipped_reasons: Dict[str, int] = field(default_factory=dict)

    def record_skip(self, reason: str) -> None:
        self.skipped_count += 1
        self.skipped_reasons[reason] = self.skipped_reasons.get(reason, 0) + 1

    def merge(self, other: Optional["ScanStats"]) -> None:
        if other is None:
            return
        self.scanned_entries += other.scanned_entries
        self.scanned_files += other.scanned_files
        self.scanned_dirs += other.scanned_dirs
        self.skipped_count += other.skipped_count
        for reason, count in other.skipped_reasons.items():
            self.skipped_reasons[reason] = self.skipped_reasons.get(reason, 0) + count


@dataclass
class FolderInfo:
    """Information about a folder's size and contents."""

    path: str
    name: str
    size_bytes: int
    allocated_bytes: int
    file_count: int
    folder_count: int
    last_modified: str
    children: List["FolderInfo"]
    has_unscanned_children: bool = False
    direct_files: List[FileEntry] = field(default_factory=list)
    scan_stats: ScanStats = field(default_factory=ScanStats)

    @property
    def size_mb(self) -> float:
        """Size in megabytes."""
        try:
            return self.size_bytes / (1024 * 1024)
        except Exception:
            return 0.0

    @property
    def size_gb(self) -> float:
        """Size in gigabytes."""
        try:
            return self.size_bytes / (1024 * 1024 * 1024)
        except Exception:
            return 0.0

    def size_formatted(self) -> str:
        """Human-readable size string."""
        return format_size(self.size_bytes)

    def allocated_formatted(self) -> str:
        """Human-readable allocated size string."""
        return format_size(self.allocated_bytes)
