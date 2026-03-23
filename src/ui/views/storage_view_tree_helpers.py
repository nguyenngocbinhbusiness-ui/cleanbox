"""Pure helpers for storage_view_tree formatting and summary logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from features.folder_scanner import FileEntry


def parse_display_int(text: str) -> int:
    """Parse a tree column display value into an integer."""
    cleaned = text.replace(",", "").strip()
    if cleaned == "-":
        return 0
    return int(cleaned)


def calculate_percent(value: int, reference_size: int) -> float:
    """Return a percentage value using the same guard as the UI code."""
    if reference_size <= 0:
        return 0.0
    return (value / reference_size) * 100


@dataclass(frozen=True)
class DirectFileSummary:
    """Aggregated direct-file metrics for a folder node."""

    file_count: int
    total_size: int
    total_allocated: int
    shown_files: tuple[FileEntry, ...]
    omitted_count: int
    omitted_size: int


def summarize_direct_files(
    direct_files: Sequence[FileEntry],
    max_entries: int,
) -> DirectFileSummary:
    """Summarize direct files without changing presentation semantics."""
    shown_files = tuple(direct_files[:max_entries])
    omitted_files = direct_files[max_entries:]
    return DirectFileSummary(
        file_count=len(direct_files),
        total_size=sum(entry.size_bytes for entry in direct_files),
        total_allocated=sum(entry.allocated_bytes for entry in direct_files),
        shown_files=shown_files,
        omitted_count=len(omitted_files),
        omitted_size=sum(entry.size_bytes for entry in omitted_files),
    )
