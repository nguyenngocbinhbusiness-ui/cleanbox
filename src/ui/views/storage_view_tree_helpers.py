"""Pure helpers for storage_view_tree formatting and summary logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from features.folder_scanner import FileEntry, FolderInfo


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


def compare_sort_values(
    *,
    column: int,
    percent_column: int,
    size_columns: tuple[int, ...],
    count_columns: tuple[int, ...],
    self_text: str,
    other_text: str,
    self_user_value: object,
    other_user_value: object,
) -> bool | None:
    """Return numeric comparison result for supported tree columns."""
    if column == percent_column:
        self_val = self_user_value or 0.0
        other_val = other_user_value or 0.0
        return float(self_val) < float(other_val)

    if column in size_columns:
        self_val = self_user_value or 0
        other_val = other_user_value or 0
        return int(self_val) < int(other_val)

    if column in count_columns:
        self_val = parse_display_int(self_text)
        other_val = parse_display_int(other_text)
        return self_val < other_val

    return None


def format_count(value: int) -> str:
    """Format count fields using tree conventions."""
    return f"{value:,}" if value else "-"


def build_folder_row_values(
    folder_info: FolderInfo,
    reference_size: int,
) -> dict[str, object]:
    """Build row texts and user-role values for a folder item."""
    percent = calculate_percent(folder_info.size_bytes, reference_size)
    display_name = folder_info.name or folder_info.path
    size_text = folder_info.size_formatted()
    return {
        "name_text": f"{size_text}   {display_name}",
        "size_text": size_text,
        "allocated_text": folder_info.allocated_formatted(),
        "files_text": format_count(folder_info.file_count),
        "folders_text": format_count(folder_info.folder_count),
        "percent_text": f"{percent:.1f} %" if reference_size > 0 else "-",
        "percent": percent,
        "size_bytes": folder_info.size_bytes,
        "allocated_bytes": folder_info.allocated_bytes,
        "path": folder_info.path,
    }


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
