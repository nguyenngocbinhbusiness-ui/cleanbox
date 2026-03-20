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
import datetime
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Tuple, Dict, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


@dataclass
class FileEntry:
    """Information about a single file."""
    name: str
    path: str
    size_bytes: int
    allocated_bytes: int

logger = logging.getLogger(__name__)

_PROGRESS_INTERVAL = 0.1  # seconds (~10 calls/sec max)
_DEFAULT_CLUSTER_SIZE = 4096
_MIN_WORKERS = 2
_MAX_WORKERS = 8
_DEFAULT_WORKERS = 4
_WORKERS_ENV = "CLEANBOX_SCANNER_WORKERS"


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


def format_size(size_bytes: int) -> str:
    """Human-readable size string (TreeSize-style)."""
    try:
        if size_bytes >= 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 ** 3):.1f} GB"
        elif size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes} Bytes"
    except Exception:
        return "0 Bytes"


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
    children: List['FolderInfo']
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
    ) -> Tuple[int, int, float]:
        """
        Process a file entry and return (size, allocated, mtime).
        Returns (0, 0, 0.0) when file cannot be accessed.
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
            return fsize, falloc, float(st.st_mtime)
        except Exception as e:
            self._record_skip(stats, e)
            logger.debug("Cannot access file %s: %s", entry, e)
            return 0, 0, 0.0

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
        last_progress_time = [0.0]
        stats = ScanStats()
        folder_name = os.path.basename(path) or path

        total_size = 0
        total_allocated = 0
        file_count = 0
        folder_count = 0
        max_mtime = 0.0
        children: List[FolderInfo] = []
        dirs = []
        direct_files: List[FileEntry] = []
        try:
            entry_iter = self._iter_dir_entries(path, stats)
        except Exception as e:
            logger.debug("Cannot access %s: %s", path, e)
            return FolderInfo(
                path=path, name=folder_name,
                size_bytes=0, allocated_bytes=0,
                file_count=0, folder_count=0,
                last_modified='', children=[],
                scan_stats=stats)

        # Separate files and directories using streaming iteration
        try:
            for entry in entry_iter:
                if self._cancel_flag.is_set():
                    return None
                items_scanned[0] += 1
                stats.scanned_entries += 1
                try:
                    if entry.is_file(follow_symlinks=False):
                        fsize, falloc, mtime = self._process_file_entry(
                            entry, direct_files, stats)
                        total_size += fsize
                        total_allocated += falloc
                        if fsize > 0:
                            file_count += 1
                        if mtime > max_mtime:
                            max_mtime = mtime
                    elif entry.is_dir(follow_symlinks=False):
                        dirs.append(entry)
                        folder_count += 1
                        stats.scanned_dirs += 1
                except Exception as e:
                    self._record_skip(stats, e)
                    logger.debug("Error processing entry %s: %s", entry, e)
        except Exception as e:
            logger.debug("Cannot iterate realtime entries for %s: %s", path, e)
            return FolderInfo(
                path=path, name=folder_name,
                size_bytes=0, allocated_bytes=0,
                file_count=0, folder_count=0,
                last_modified='', children=[],
                scan_stats=stats)

        # TreeSize Layer 2: parallel subdirectory scanning
        if dirs and not self._cancel_flag.is_set():
            try:
                with ThreadPoolExecutor(
                    max_workers=self._parallel_workers
                ) as executor:
                    future_to_dir = {}
                    for entry in dirs:
                        if self._cancel_flag.is_set():
                            break
                        fut = executor.submit(
                            self._scan_subtree,
                            entry.path, progress_callback, stats)
                        future_to_dir[fut] = entry

                    # Collect results sequentially via as_completed,
                    # emit child_callback on calling thread (DRBFM D6)
                    for future in as_completed(future_to_dir):
                        if self._cancel_flag.is_set():
                            executor.shutdown(
                                wait=False, cancel_futures=True)
                            return None

                        child_info = future.result()
                        if child_info is None:
                            continue

                        children.append(child_info)
                        total_size += child_info.size_bytes
                        total_allocated += child_info.allocated_bytes
                        file_count += child_info.file_count
                        folder_count += child_info.folder_count
                        stats.merge(child_info.scan_stats)

                        # Aggregate items_scanned from subtree
                        with self._progress_lock:
                            if progress_callback:
                                progress_callback(
                                    child_info.path, items_scanned[0])

                        try:
                            if child_info.last_modified:
                                child_mtime = datetime.datetime.strptime(
                                    child_info.last_modified, '%m/%d/%Y'
                                ).timestamp()
                                if child_mtime > max_mtime:
                                    max_mtime = child_mtime
                        except Exception:
                            pass

                        child_callback(child_info)
            except Exception as e:
                logger.error("Parallel scan failed: %s", e)
                self._record_skip(stats, e)
                # Fallback: sequential scan for remaining dirs
                for entry in dirs:
                    if self._cancel_flag.is_set():
                        return None
                    already = {c.path for c in children}
                    if entry.path in already:
                        continue
                    child_info = self._scan_subtree(
                        entry.path, progress_callback, stats)
                    if child_info is None:
                        continue
                    children.append(child_info)
                    total_size += child_info.size_bytes
                    total_allocated += child_info.allocated_bytes
                    file_count += child_info.file_count
                    folder_count += child_info.folder_count
                    stats.merge(child_info.scan_stats)
                    child_callback(child_info)

        children.sort(key=lambda x: x.size_bytes, reverse=True)
        direct_files.sort(key=lambda x: x.size_bytes, reverse=True)
        root_modified = (
            datetime.datetime.fromtimestamp(max_mtime).strftime('%m/%d/%Y')
            if max_mtime > 0 else '')

        return FolderInfo(
            path=path,
            name=folder_name,
            size_bytes=total_size,
            allocated_bytes=total_allocated,
            file_count=file_count,
            folder_count=folder_count,
            last_modified=root_modified,
            children=children,
            direct_files=direct_files,
            scan_stats=stats,
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
        local_scanned = [0]
        local_progress_time = [0.0]
        local_stats = ScanStats()
        try:
            result = self._scan_recursive(
                path, 999, 0, progress_callback,
                local_scanned, local_progress_time, local_stats)
            if result and parent_stats:
                parent_stats.merge(result.scan_stats)
            return result
        except Exception as e:
            logger.error("Subtree scan failed for %s: %s", path, e)
            if parent_stats:
                self._record_skip(parent_stats, e)
            return None

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
        stats = stats or ScanStats()
        if self._cancel_flag.is_set():
            return None

        folder_name = os.path.basename(path) or path

        total_size = 0
        total_allocated = 0
        file_count = 0
        folder_count = 0
        max_mtime = 0.0
        children: List[FolderInfo] = []
        direct_files: List[FileEntry] = []
        has_unscanned = False

        try:
            entries = self._iter_dir_entries(path, stats)
        except Exception as e:
            logger.debug("Cannot access %s: %s", path, e)
            return FolderInfo(
                path=path, name=folder_name,
                size_bytes=0, allocated_bytes=0,
                file_count=0, folder_count=0,
                last_modified='', children=[],
                scan_stats=stats)

        try:
            for entry in entries:
                if self._cancel_flag.is_set():
                    return None

                items_scanned[0] += 1
                stats.scanned_entries += 1

                if progress_callback:
                    now = time.monotonic()
                    if now - last_progress_time[0] >= _PROGRESS_INTERVAL:
                        last_progress_time[0] = now
                        progress_callback(entry.path, items_scanned[0])

                try:
                    # Cached attributes from os.scandir – no extra syscalls
                    if entry.is_file(follow_symlinks=False):
                        fsize, falloc, mtime = self._process_file_entry(
                            entry, direct_files, stats)
                        total_size += fsize
                        total_allocated += falloc
                        if fsize > 0:
                            file_count += 1
                        if mtime > max_mtime:
                            max_mtime = mtime

                    elif entry.is_dir(follow_symlinks=False):
                        folder_count += 1
                        stats.scanned_dirs += 1

                        if current_depth < max_depth:
                            child_info = self._scan_recursive(
                                entry.path,
                                max_depth,
                                current_depth + 1,
                                progress_callback,
                                items_scanned,
                                last_progress_time,
                                ScanStats(),
                            )
                            if child_info:
                                children.append(child_info)
                                total_size += child_info.size_bytes
                                total_allocated += child_info.allocated_bytes
                                file_count += child_info.file_count
                                folder_count += child_info.folder_count
                                stats.merge(child_info.scan_stats)
                                try:
                                    if child_info.last_modified:
                                        child_mt = datetime.datetime.strptime(
                                            child_info.last_modified, '%m/%d/%Y'
                                        ).timestamp()
                                        if child_mt > max_mtime:
                                            max_mtime = child_mt
                                except Exception:
                                    stats.record_skip("mtime_parse_error")
                        else:
                            child_size, child_alloc = self._get_folder_size_fast(
                                entry.path, items_scanned, stats)
                            entry_mtime = 0.0
                            try:
                                entry_mtime = float(
                                    entry.stat(
                                        follow_symlinks=False).st_mtime)
                            except Exception as e:
                                self._record_skip(stats, e)
                            try:
                                child_modified = (
                                    datetime.datetime.fromtimestamp(
                                        entry_mtime).strftime('%m/%d/%Y')
                                    if entry_mtime > 0 else '')
                            except Exception:
                                stats.record_skip("mtime_format_error")
                                child_modified = ''
                            child_info = FolderInfo(
                                path=entry.path,
                                name=entry.name,
                                size_bytes=child_size,
                                allocated_bytes=child_alloc,
                                file_count=0,
                                folder_count=0,
                                last_modified=child_modified,
                                children=[],
                                has_unscanned_children=True,
                                scan_stats=ScanStats(),
                            )
                            children.append(child_info)
                            total_size += child_size
                            total_allocated += child_alloc
                            has_unscanned = True
                            if entry_mtime > max_mtime:
                                max_mtime = entry_mtime
                except Exception as e:
                    self._record_skip(stats, e)
                    logger.debug("Error processing entry %s: %s", entry, e)
        except Exception as e:
            logger.debug("Cannot iterate entries for %s: %s", path, e)
            return FolderInfo(
                path=path, name=folder_name,
                size_bytes=0, allocated_bytes=0,
                file_count=0, folder_count=0,
                last_modified='', children=[],
                scan_stats=stats)

        # Sort children by size (largest first)
        children.sort(key=lambda x: x.size_bytes, reverse=True)
        direct_files.sort(key=lambda x: x.size_bytes, reverse=True)

        folder_modified = (
            datetime.datetime.fromtimestamp(max_mtime).strftime('%m/%d/%Y')
            if max_mtime > 0 else '')

        return FolderInfo(
            path=path,
            name=folder_name,
            size_bytes=total_size,
            allocated_bytes=total_allocated,
            file_count=file_count,
            folder_count=folder_count,
            last_modified=folder_modified,
            children=children,
            has_unscanned_children=has_unscanned,
            direct_files=direct_files,
            scan_stats=stats,
        )

    def _get_folder_size_fast(
        self, path: str,
        items_scanned: Optional[List[int]] = None,
        stats: Optional[ScanStats] = None,
    ) -> Tuple[int, int]:
        """Get total size and allocated size using os.scandir (D6: avoid walk+stat)."""
        total = 0
        allocated = 0
        stack = [path]
        stats = stats or ScanStats()
        try:
            while stack:
                if self._cancel_flag.is_set():
                    return total, allocated
                current = stack.pop()
                try:
                    with os.scandir(current) as it:
                        for entry in it:
                            if self._cancel_flag.is_set():
                                return total, allocated
                            if items_scanned is not None:
                                items_scanned[0] += 1
                            stats.scanned_entries += 1
                            try:
                                if entry.is_file(follow_symlinks=False):
                                    fsize = entry.stat(
                                        follow_symlinks=False).st_size
                                    total += fsize
                                    allocated += _calc_allocated(
                                        fsize, self._cluster_size)
                                    stats.scanned_files += 1
                                elif entry.is_dir(follow_symlinks=False):
                                    stack.append(entry.path)
                                    stats.scanned_dirs += 1
                            except Exception as e:
                                self._record_skip(stats, e)
                except Exception as e:
                    self._record_skip(stats, e)
                    logger.debug("Cannot scan %s: %s", current, e)
        except Exception as e:
            self._record_skip(stats, e)
            logger.debug("Cannot walk path %s: %s", path, e)
        return total, allocated

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
