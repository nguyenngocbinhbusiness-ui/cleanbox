"""Folder Scanner - Recursive folder size calculation.

Uses TreeSize-style scanning techniques:
- os.scandir() for cached stat (simulates FindFirstFileExW with LARGE_FETCH)
- ThreadPoolExecutor for parallel subdirectory scanning
"""
import os
import logging
import time
import math
import ctypes
from typing import Optional, Callable, List, Tuple, Iterator
from concurrent.futures import ThreadPoolExecutor
import threading

from features.folder_scanner.format_utils import format_size as _format_size
from features.folder_scanner.models import FileEntry, FolderInfo, ScanStats
from features.folder_scanner.realtime_pipeline import (
    merge_realtime_child,
    scan_realtime_directories_pipeline,
    scan_realtime_entries,
    scan_subtree,
)
from features.folder_scanner.recursive_engine import (
    scan_recursive,
    scan_recursive_directory,
    scan_recursive_entry,
    scan_shallow_directory,
)
from features.folder_scanner.size_walker import get_folder_size_fast
from features.folder_scanner.scan_helpers import (
    ScanAggregate,
    format_last_modified,
)


logger = logging.getLogger(__name__)

format_size = _format_size

_PROGRESS_INTERVAL = 0.1  # seconds (~10 calls/sec max)
_DEFAULT_CLUSTER_SIZE = 4096
_MIN_WORKERS = 2
_MAX_WORKERS = 8
_DEFAULT_WORKERS = 4
_WORKERS_ENV = "CLEANBOX_SCANNER_WORKERS"


def _get_cluster_size(path: str) -> int:
    """Get filesystem cluster size for the drive containing path."""
    try:
        drive = os.path.splitdrive(path)[0] + '\\'
        sectors = ctypes.c_ulong(0)
        bytes_per = ctypes.c_ulong(0)
        free_c = ctypes.c_ulong(0)
        total_c = ctypes.c_ulong(0)
        ok = ctypes.windll.kernel32.GetDiskFreeSpaceW(
            ctypes.c_wchar_p(drive),
            ctypes.byref(sectors),
            ctypes.byref(bytes_per),
            ctypes.byref(free_c),
            ctypes.byref(total_c),
        )
        if ok:
            cluster = sectors.value * bytes_per.value
            if cluster > 0:
                return cluster
    except Exception as e:
        logger.debug("Failed to get cluster size: %s", e)
    return _DEFAULT_CLUSTER_SIZE


def _calc_allocated(file_size: int, cluster_size: int) -> int:
    """Calculate allocated disk space for a file."""
    if file_size == 0:
        return 0
    return math.ceil(file_size / cluster_size) * cluster_size


class FolderScanner:
    """
    Service for recursively scanning folder sizes.

    Uses TreeSize-style techniques for fast scanning:
    - os.scandir() with cached stat (simulates FindFirstFileExW)
    - Parallel subdirectory scanning via ThreadPoolExecutor

    Supports:
    - Async scanning with progress callbacks
    - Scan cancellation
    - Real-time per-child scanning
    - Error handling for inaccessible folders
    """
    def __init__(self):
        """Initialize the folder scanner service."""
        try:
            self._logger = logger
            self._os = os
            self._cancel_flag = threading.Event()
            self._executor: Optional[ThreadPoolExecutor] = None
            self._cluster_size: int = _DEFAULT_CLUSTER_SIZE
            self._progress_lock = threading.Lock()
            self._parallel_workers: int = self._resolve_parallel_workers()
        except Exception as e:
            logger.error("Failed to init FolderScanner: %s", e)

    def _resolve_parallel_workers(self) -> int:
        """Resolve worker count from env/cpu with sane bounds."""
        try:
            env_value = os.getenv(_WORKERS_ENV)
            if env_value:
                parsed = int(env_value)
                return max(_MIN_WORKERS, min(parsed, _MAX_WORKERS))
        except (TypeError, ValueError):
            logger.debug("Invalid %s value; using adaptive default", _WORKERS_ENV)

        cpu = os.cpu_count() or _DEFAULT_WORKERS
        adaptive = max(_MIN_WORKERS, min(cpu // 2, _MAX_WORKERS))
        return adaptive if adaptive > 0 else _DEFAULT_WORKERS

    @staticmethod
    def _skip_reason(exc: Exception) -> str:
        if isinstance(exc, PermissionError):
            return "permission_denied"
        if isinstance(exc, OSError):
            return "os_error"
        return "entry_processing_error"

    def _record_skip(self, stats: ScanStats, exc: Exception) -> None:
        stats.record_skip(self._skip_reason(exc))

    @staticmethod
    def _empty_folder_info(path: str, folder_name: str, stats: ScanStats) -> FolderInfo:
        """Return a safe empty FolderInfo for inaccessible paths."""
        return FolderInfo(
            path=path,
            name=folder_name,
            size_bytes=0,
            allocated_bytes=0,
            file_count=0,
            folder_count=0,
            last_modified="",
            children=[],
            scan_stats=stats,
        )

    @staticmethod
    def _record_timestamp_parse_failure(stats: ScanStats, timestamp_value: str) -> None:
        """Record timestamp parse failures only when a value was present."""
        if timestamp_value:
            stats.record_skip("mtime_parse_error")

    @staticmethod
    def _emit_progress(
        progress_callback: Optional[Callable[[str, int], None]],
        path: str,
        items_scanned: List[int],
    ) -> None:
        if progress_callback:
            progress_callback(path, items_scanned[0])

    def _maybe_emit_progress(
        self,
        progress_callback: Optional[Callable[[str, int], None]],
        path: str,
        items_scanned: List[int],
        last_progress_time: List[float],
    ) -> None:
        if not progress_callback:
            return
        now = time.monotonic()
        if now - last_progress_time[0] >= _PROGRESS_INTERVAL:
            last_progress_time[0] = now
            self._emit_progress(progress_callback, path, items_scanned)

    def _iter_dir_entries(self, path: str, stats: ScanStats) -> Iterator[os.DirEntry]:
        """Iterate directory entries while capturing scandir errors deterministically."""
        try:
            raw_iter = os.scandir(path)
            if hasattr(raw_iter, "__enter__"):
                with raw_iter as it:
                    for entry in it:
                        yield entry
            else:
                for entry in raw_iter:
                    yield entry
        except Exception as e:
            self._record_skip(stats, e)
            raise

    def _process_file_entry(
        self,
        entry: os.DirEntry,
        direct_files: List[FileEntry],
        stats: ScanStats,
    ) -> Tuple[int, int, float, bool]:
        """
        Process a file entry and return (size, allocated, mtime, success).
        Returns success=False when file cannot be accessed.
        """
        try:
            st = entry.stat(follow_symlinks=False)
            fsize = st.st_size
            falloc = _calc_allocated(fsize, self._cluster_size)
            direct_files.append(
                FileEntry(
                    name=entry.name,
                    path=entry.path,
                    size_bytes=fsize,
                    allocated_bytes=falloc,
                )
            )
            stats.scanned_files += 1
            return fsize, falloc, float(st.st_mtime), True
        except Exception as e:
            self._record_skip(stats, e)
            logger.debug("Cannot access file %s: %s", entry, e)
            return 0, 0, 0.0, False

    def _scan_shallow_directory(
        self,
        entry: os.DirEntry,
        aggregate: ScanAggregate,
        children: List[FolderInfo],
        items_scanned: List[int],
        stats: ScanStats,
    ) -> bool:
        return scan_shallow_directory(
            self, entry, aggregate, children, items_scanned, stats
        )

    def _scan_recursive_directory(
        self,
        entry: os.DirEntry,
        max_depth: int,
        current_depth: int,
        progress_callback: Optional[Callable[[str, int], None]],
        items_scanned: List[int],
        last_progress_time: List[float],
        aggregate: ScanAggregate,
        children: List[FolderInfo],
        stats: ScanStats,
    ) -> bool:
        return scan_recursive_directory(
            self,
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

    def _scan_recursive_entry(
        self,
        entry: os.DirEntry,
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
        return scan_recursive_entry(
            self,
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
        )

    def scan_folder(
        self,
        path: str,
        max_depth: int = 1,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> Optional[FolderInfo]:
        """
        Scan a folder recursively up to max_depth.

        Args:
            path: Root folder path
            max_depth: How deep to scan (1 = immediate children only)
            progress_callback: Called with (current_path, items_scanned)

        Returns:
            FolderInfo with size data, or None if cancelled/error
        """
        self._cancel_flag.clear()
        self._cluster_size = _get_cluster_size(path)
        items_scanned = [0]
        last_progress_time = [0.0]
        stats = ScanStats()

        try:
            return self._scan_recursive(
                path, max_depth, 0, progress_callback, items_scanned,
                last_progress_time, stats)
        except Exception as e:
            logger.error("Scan failed for %s: %s", path, e)
            return None
        finally:
            self._cancel_flag.clear()
            logger.debug("Scan resources cleaned up")

    def scan_single_level(
        self,
        path: str,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> Optional[FolderInfo]:
        """Scan a single folder level (immediate children only)."""
        self._cancel_flag.clear()
        self._cluster_size = _get_cluster_size(path)
        items_scanned = [0]
        last_progress_time = [0.0]
        stats = ScanStats()
        try:
            return self._scan_recursive(
                path, 1, 0, progress_callback, items_scanned,
                last_progress_time, stats)
        except Exception as e:
            logger.error("Single level scan failed for %s: %s", path, e)
            return None
        finally:
            self._cancel_flag.clear()

    def scan_children_realtime(
        self,
        path: str,
        child_callback: Callable[['FolderInfo'], None],
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> Optional[FolderInfo]:
        """
        Scan children of path, calling child_callback for each child folder
        as its size calculation completes (real-time updates).

        Uses parallel scanning: subdirectories are scanned concurrently
        via ThreadPoolExecutor, with callbacks emitted sequentially on
        the calling thread as each completes.

        Returns the root FolderInfo with all children.
        """
        self._cancel_flag.clear()
        self._cluster_size = _get_cluster_size(path)
        items_scanned = [0]
        stats = ScanStats()
        folder_name = os.path.basename(path) or path
        aggregate = ScanAggregate()
        children: List[FolderInfo] = []
        dirs = []
        direct_files: List[FileEntry] = []
        try:
            entry_iter = self._iter_dir_entries(path, stats)
        except Exception as e:
            logger.debug("Cannot access %s: %s", path, e)
            return self._empty_folder_info(path, folder_name, stats)

        try:
            self._scan_realtime_entries(
                entry_iter, dirs, direct_files, items_scanned, stats, aggregate
            )
        except RuntimeError:
            return None
        except Exception as e:
            logger.debug("Cannot iterate realtime entries for %s: %s", path, e)
            return self._empty_folder_info(path, folder_name, stats)

        if dirs and not self._cancel_flag.is_set():
            try:
                self._scan_realtime_directories(
                    dirs,
                    children,
                    child_callback,
                    progress_callback,
                    items_scanned,
                    stats,
                    aggregate,
                )
            except RuntimeError:
                return None

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
            direct_files=direct_files,
            scan_stats=stats,
        )

    def _scan_realtime_entries(
        self,
        entry_iter: Iterator[os.DirEntry],
        dirs: List[os.DirEntry],
        direct_files: List[FileEntry],
        items_scanned: List[int],
        stats: ScanStats,
        aggregate: ScanAggregate,
    ) -> None:
        """Process realtime scandir entries into file and directory buckets."""
        scan_realtime_entries(
            self,
            entry_iter,
            dirs,
            direct_files,
            items_scanned,
            stats,
            aggregate,
        )

    def _merge_realtime_child(
        self,
        child_info: FolderInfo,
        children: List[FolderInfo],
        child_callback: Callable[[FolderInfo], None],
        progress_callback: Optional[Callable[[str, int], None]],
        items_scanned: List[int],
        stats: ScanStats,
        aggregate: ScanAggregate,
    ) -> None:
        """Merge a realtime child result into root aggregates."""
        merge_realtime_child(
            self,
            child_info,
            children,
            child_callback,
            progress_callback,
            items_scanned,
            stats,
            aggregate,
        )

    def _scan_realtime_directories(
        self,
        dirs: List[os.DirEntry],
        children: List[FolderInfo],
        child_callback: Callable[[FolderInfo], None],
        progress_callback: Optional[Callable[[str, int], None]],
        items_scanned: List[int],
        stats: ScanStats,
        aggregate: ScanAggregate,
    ) -> None:
        """Scan child directories using parallel-first, sequential fallback behavior."""
        scan_realtime_directories_pipeline(
            self,
            dirs,
            children,
            child_callback,
            progress_callback,
            items_scanned,
            stats,
            aggregate,
        )

    def _scan_subtree(
        self,
        path: str,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        parent_stats: Optional[ScanStats] = None,
    ) -> Optional[FolderInfo]:
        """Scan a subtree with its own local progress counter.

        Used by parallel scanning to avoid race conditions on shared
        items_scanned counter (DRBFM D5).
        """
        return scan_subtree(
            self,
            path,
            progress_callback=progress_callback,
            parent_stats=parent_stats,
        )

    def _scan_recursive(
        self,
        path: str,
        max_depth: int,
        current_depth: int,
        progress_callback: Optional[Callable[[str, int], None]],
        items_scanned: List[int],
        last_progress_time: List[float],
        stats: Optional[ScanStats] = None,
    ) -> Optional[FolderInfo]:
        """Recursive folder scanning using os.scandir() for cached stat."""
        return scan_recursive(
            self,
            path,
            max_depth,
            current_depth,
            progress_callback,
            items_scanned,
            last_progress_time,
            stats,
        )

    def _get_folder_size_fast(
        self, path: str,
        items_scanned: Optional[List[int]] = None,
        stats: Optional[ScanStats] = None,
    ) -> Tuple[int, int]:
        """Get total size and allocated size using os.scandir (D6: avoid walk+stat)."""
        stats = stats or ScanStats()

        def _record_skip_and_log(exc: Exception) -> None:
            self._record_skip(stats, exc)
            logger.debug("Cannot walk/scan path %s: %s", path, exc)

        return get_folder_size_fast(
            path=path,
            cancel_flag=self._cancel_flag,
            cluster_size=self._cluster_size,
            record_skip=_record_skip_and_log,
            items_scanned=items_scanned,
            stats_scanned_entries=lambda: setattr(stats, "scanned_entries", stats.scanned_entries + 1),
            stats_scanned_files=lambda: setattr(stats, "scanned_files", stats.scanned_files + 1),
            stats_scanned_dirs=lambda: setattr(stats, "scanned_dirs", stats.scanned_dirs + 1),
        )

    def cancel(self) -> None:
        """Cancel ongoing scan."""
        try:
            self._cancel_flag.set()
            logger.info("Scan cancelled")
        except Exception as e:
            logger.error("Failed to cancel scan: %s", e)

    def is_cancelled(self) -> bool:
        """Check if scan was cancelled."""
        try:
            return self._cancel_flag.is_set()
        except Exception:
            return False
