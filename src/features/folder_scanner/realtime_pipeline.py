"""Realtime scanning pipeline helpers for FolderScanner."""

from __future__ import annotations

from typing import Callable, Iterator, List, Optional

from features.folder_scanner.models import FileEntry, FolderInfo, ScanStats
from features.folder_scanner.parallel_executor import (
    scan_realtime_directories as run_realtime_parallel,
)
from features.folder_scanner.scan_helpers import ScanAggregate, parse_last_modified


def scan_realtime_entries(
    scanner,
    entry_iter: Iterator,
    dirs: List,
    direct_files: List[FileEntry],
    items_scanned: List[int],
    stats: ScanStats,
    aggregate: ScanAggregate,
) -> None:
    """Process realtime scandir entries into file and directory buckets."""
    for entry in entry_iter:
        if scanner._cancel_flag.is_set():
            raise RuntimeError("scan cancelled")
        items_scanned[0] += 1
        stats.scanned_entries += 1
        try:
            if entry.is_file(follow_symlinks=False):
                fsize, falloc, mtime, file_processed = scanner._process_file_entry(
                    entry, direct_files, stats
                )
                if file_processed:
                    aggregate.add_file(fsize, falloc, mtime)
            elif entry.is_dir(follow_symlinks=False):
                dirs.append(entry)
                aggregate.folder_count += 1
                stats.scanned_dirs += 1
        except Exception as exc:
            scanner._record_skip(stats, exc)
            scanner._logger.debug("Error processing entry %s: %s", entry, exc)


def merge_realtime_child(
    scanner,
    child_info: FolderInfo,
    children: List[FolderInfo],
    child_callback: Callable[[FolderInfo], None],
    progress_callback: Optional[Callable[[str, int], None]],
    items_scanned: List[int],
    stats: ScanStats,
    aggregate: ScanAggregate,
) -> None:
    """Merge a realtime child result into root aggregates."""
    children.append(child_info)
    stats.merge(child_info.scan_stats)
    child_mtime = parse_last_modified(child_info.last_modified)
    if child_mtime is None:
        scanner._record_timestamp_parse_failure(stats, child_info.last_modified)
    aggregate.add_child(child_info, child_mtime)
    with scanner._progress_lock:
        scanner._emit_progress(progress_callback, child_info.path, items_scanned)
    child_callback(child_info)


def scan_subtree(
    scanner,
    path: str,
    progress_callback: Optional[Callable[[str, int], None]] = None,
    parent_stats: Optional[ScanStats] = None,
) -> Optional[FolderInfo]:
    """Scan a subtree with local counters to avoid shared-state races."""
    local_scanned = [0]
    local_progress_time = [0.0]
    local_stats = ScanStats()
    try:
        return scanner._scan_recursive(
            path, 999, 0, progress_callback, local_scanned, local_progress_time, local_stats
        )
    except Exception as exc:
        scanner._logger.error("Subtree scan failed for %s: %s", path, exc)
        if parent_stats:
            scanner._record_skip(parent_stats, exc)
        return None


def scan_realtime_directories_pipeline(
    scanner,
    dirs: List,
    children: List[FolderInfo],
    child_callback: Callable[[FolderInfo], None],
    progress_callback: Optional[Callable[[str, int], None]],
    items_scanned: List[int],
    stats: ScanStats,
    aggregate: ScanAggregate,
) -> None:
    """Scan child directories using parallel-first, sequential fallback behavior."""

    def _is_cancelled() -> bool:
        return scanner._cancel_flag.is_set()

    def _scan_entry(entry) -> Optional[FolderInfo]:
        return scanner._scan_subtree(entry.path, progress_callback, stats)

    def _merge_child(child_info: FolderInfo) -> None:
        merge_realtime_child(
            scanner,
            child_info,
            children,
            child_callback,
            progress_callback,
            items_scanned,
            stats,
            aggregate,
        )

    def _on_parallel_error(exc: Exception) -> None:
        scanner._logger.error("Parallel scan failed: %s", exc)
        scanner._record_skip(stats, exc)

    run_realtime_parallel(
        dirs=dirs,
        parallel_workers=scanner._parallel_workers,
        is_cancelled=_is_cancelled,
        scan_entry=_scan_entry,
        merge_child=_merge_child,
        on_parallel_error=_on_parallel_error,
    )
