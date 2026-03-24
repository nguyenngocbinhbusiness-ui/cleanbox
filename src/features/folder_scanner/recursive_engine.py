"""Recursive scan engine helpers for FolderScanner."""

from __future__ import annotations

from typing import Callable, List, Optional

from features.folder_scanner.models import FileEntry, FolderInfo, ScanStats
from features.folder_scanner.scan_helpers import (
    ScanAggregate,
    format_last_modified,
    parse_last_modified,
)


def scan_shallow_directory(
    scanner,
    entry,
    aggregate: ScanAggregate,
    children: List[FolderInfo],
    items_scanned: List[int],
    stats: ScanStats,
) -> bool:
    """Scan directory at depth limit and mark it as unscanned for descendants."""
    child_size, child_alloc = scanner._get_folder_size_fast(entry.path, items_scanned, stats)
    aggregate.total_size += child_size
    aggregate.total_allocated += child_alloc

    entry_mtime = 0.0
    try:
        entry_mtime = float(entry.stat(follow_symlinks=False).st_mtime)
    except Exception as exc:
        scanner._record_skip(stats, exc)

    children.append(
        FolderInfo(
            path=entry.path,
            name=entry.name,
            size_bytes=child_size,
            allocated_bytes=child_alloc,
            file_count=0,
            folder_count=0,
            last_modified=format_last_modified(entry_mtime),
            children=[],
            has_unscanned_children=True,
            scan_stats=ScanStats(),
        )
    )
    if entry_mtime > aggregate.max_mtime:
        aggregate.max_mtime = entry_mtime
    return True


def scan_recursive_directory(
    scanner,
    entry,
    max_depth: int,
    current_depth: int,
    progress_callback: Optional[Callable[[str, int], None]],
    items_scanned: List[int],
    last_progress_time: List[float],
    aggregate: ScanAggregate,
    children: List[FolderInfo],
    stats: ScanStats,
) -> bool:
    """Scan a subdirectory branch recursively or shallow based on depth."""
    aggregate.folder_count += 1
    stats.scanned_dirs += 1

    if current_depth >= max_depth:
        return scan_shallow_directory(scanner, entry, aggregate, children, items_scanned, stats)

    child_info = scan_recursive(
        scanner,
        entry.path,
        max_depth,
        current_depth + 1,
        progress_callback,
        items_scanned,
        last_progress_time,
        ScanStats(),
    )
    if not child_info:
        return False

    children.append(child_info)
    stats.merge(child_info.scan_stats)
    child_mtime = parse_last_modified(child_info.last_modified)
    if child_mtime is None:
        scanner._record_timestamp_parse_failure(stats, child_info.last_modified)
    aggregate.add_child(child_info, child_mtime)
    return False


def scan_recursive_entry(
    scanner,
    entry,
    max_depth: int,
    current_depth: int,
    progress_callback: Optional[Callable[[str, int], None]],
    items_scanned: List[int],
    last_progress_time: List[float],
    aggregate: ScanAggregate,
    children: List[FolderInfo],
    direct_files: List[FileEntry],
    stats: ScanStats,
) -> bool:
    """Scan a single entry (file or directory) and merge into aggregate."""
    if entry.is_file(follow_symlinks=False):
        fsize, falloc, mtime, file_processed = scanner._process_file_entry(
            entry, direct_files, stats
        )
        if file_processed:
            aggregate.add_file(fsize, falloc, mtime)
        return False
    if not entry.is_dir(follow_symlinks=False):
        return False
    return scan_recursive_directory(
        scanner,
        entry,
        max_depth,
        current_depth,
        progress_callback,
        items_scanned,
        last_progress_time,
        aggregate,
        children,
        stats,
    )


def scan_recursive(
    scanner,
    path: str,
    max_depth: int,
    current_depth: int,
    progress_callback: Optional[Callable[[str, int], None]],
    items_scanned: List[int],
    last_progress_time: List[float],
    stats: Optional[ScanStats] = None,
) -> Optional[FolderInfo]:
    """Core recursive folder scanning loop using os.scandir."""
    stats = stats or ScanStats()
    if scanner._cancel_flag.is_set():
        return None

    folder_name = scanner._os.path.basename(path) or path
    aggregate = ScanAggregate()
    children: List[FolderInfo] = []
    direct_files: List[FileEntry] = []
    has_unscanned = False

    try:
        entries = scanner._iter_dir_entries(path, stats)
    except Exception as exc:
        scanner._logger.debug("Cannot access %s: %s", path, exc)
        return scanner._empty_folder_info(path, folder_name, stats)

    try:
        for entry in entries:
            if scanner._cancel_flag.is_set():
                return None

            items_scanned[0] += 1
            stats.scanned_entries += 1
            scanner._maybe_emit_progress(progress_callback, entry.path, items_scanned, last_progress_time)

            try:
                has_unscanned = scan_recursive_entry(
                    scanner,
                    entry,
                    max_depth,
                    current_depth,
                    progress_callback,
                    items_scanned,
                    last_progress_time,
                    aggregate,
                    children,
                    direct_files,
                    stats,
                ) or has_unscanned
            except Exception as exc:
                scanner._record_skip(stats, exc)
                scanner._logger.debug("Error processing entry %s: %s", entry, exc)
    except Exception as exc:
        scanner._logger.debug("Cannot iterate entries for %s: %s", path, exc)
        return scanner._empty_folder_info(path, folder_name, stats)

    children.sort(key=lambda x: x.size_bytes, reverse=True)
    direct_files.sort(key=lambda x: x.size_bytes, reverse=True)

    return FolderInfo(
        path=path,
        name=folder_name,
        size_bytes=aggregate.total_size,
        allocated_bytes=aggregate.total_allocated,
        file_count=aggregate.file_count,
        folder_count=aggregate.folder_count,
        last_modified=format_last_modified(aggregate.max_mtime),
        children=children,
        has_unscanned_children=has_unscanned,
        direct_files=direct_files,
        scan_stats=stats,
    )
