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
from typing import Optional, Callable, List, Tuple
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
_PARALLEL_WORKERS = 4  # thread pool size for parallel subdirectory scanning


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
        except Exception as e:
            logger.error("Failed to init FolderScanner: %s", e)

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

        try:
            return self._scan_recursive(
                path, max_depth, 0, progress_callback, items_scanned,
                last_progress_time)
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
        try:
            return self._scan_recursive(
                path, 1, 0, progress_callback, items_scanned,
                last_progress_time)
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
        folder_name = os.path.basename(path) or path

        total_size = 0
        total_allocated = 0
        file_count = 0
        folder_count = 0
        max_mtime = 0.0
        children: List[FolderInfo] = []

        # TreeSize Layer 1: os.scandir() – cached stat, no extra syscalls
        try:
            entries = list(os.scandir(path))
        except (PermissionError, OSError) as e:
            logger.debug("Cannot access %s: %s", path, e)
            return FolderInfo(
                path=path, name=folder_name,
                size_bytes=0, allocated_bytes=0,
                file_count=0, folder_count=0,
                last_modified='', children=[])

        # Separate files and directories using cached attributes
        dirs = []
        direct_files: List[FileEntry] = []
        for entry in entries:
            if self._cancel_flag.is_set():
                return None
            try:
                if entry.is_file(follow_symlinks=False):
                    try:
                        st = entry.stat(follow_symlinks=False)
                        fsize = st.st_size
                        falloc = _calc_allocated(fsize, self._cluster_size)
                        total_size += fsize
                        total_allocated += falloc
                        file_count += 1
                        direct_files.append(FileEntry(
                            name=entry.name, path=entry.path,
                            size_bytes=fsize, allocated_bytes=falloc))
                        if st.st_mtime > max_mtime:
                            max_mtime = st.st_mtime
                    except (PermissionError, OSError):
                        pass
                elif entry.is_dir(follow_symlinks=False):
                    dirs.append(entry)
                    folder_count += 1
            except Exception:
                pass
            items_scanned[0] += 1

        # TreeSize Layer 2: parallel subdirectory scanning
        if dirs and not self._cancel_flag.is_set():
            try:
                with ThreadPoolExecutor(
                    max_workers=_PARALLEL_WORKERS
                ) as executor:
                    future_to_dir = {}
                    for entry in dirs:
                        if self._cancel_flag.is_set():
                            break
                        fut = executor.submit(
                            self._scan_subtree,
                            entry.path, progress_callback)
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
                # Fallback: sequential scan for remaining dirs
                for entry in dirs:
                    if self._cancel_flag.is_set():
                        return None
                    already = {c.path for c in children}
                    if entry.path in already:
                        continue
                    child_info = self._scan_subtree(
                        entry.path, progress_callback)
                    if child_info is None:
                        continue
                    children.append(child_info)
                    total_size += child_info.size_bytes
                    total_allocated += child_info.allocated_bytes
                    file_count += child_info.file_count
                    folder_count += child_info.folder_count
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
        )

    def _scan_subtree(
        self,
        path: str,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> Optional[FolderInfo]:
        """Scan a subtree with its own local progress counter.

        Used by parallel scanning to avoid race conditions on shared
        items_scanned counter (DRBFM D5).
        """
        local_scanned = [0]
        local_progress_time = [0.0]
        try:
            return self._scan_recursive(
                path, 999, 0, progress_callback,
                local_scanned, local_progress_time)
        except Exception as e:
            logger.error("Subtree scan failed for %s: %s", path, e)
            return None

    def _scan_recursive(
        self,
        path: str,
        max_depth: int,
        current_depth: int,
        progress_callback: Optional[Callable[[str, int], None]],
        items_scanned: List[int],
        last_progress_time: List[float],
    ) -> Optional[FolderInfo]:
        """Recursive folder scanning using os.scandir() for cached stat."""
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

        # TreeSize Layer 1: os.scandir() – releases handle immediately
        try:
            entries = list(os.scandir(path))
        except PermissionError:
            logger.debug("Permission denied: %s", path)
            return FolderInfo(
                path=path, name=folder_name,
                size_bytes=0, allocated_bytes=0,
                file_count=0, folder_count=0,
                last_modified='', children=[])
        except Exception as e:
            logger.debug("Cannot access %s: %s", path, e)
            return FolderInfo(
                path=path, name=folder_name,
                size_bytes=0, allocated_bytes=0,
                file_count=0, folder_count=0,
                last_modified='', children=[])

        for entry in entries:
            if self._cancel_flag.is_set():
                return None

            items_scanned[0] += 1

            if progress_callback:
                now = time.monotonic()
                if now - last_progress_time[0] >= _PROGRESS_INTERVAL:
                    last_progress_time[0] = now
                    progress_callback(entry.path, items_scanned[0])

            try:
                # Cached attributes from os.scandir – no extra syscalls
                if entry.is_file(follow_symlinks=False):
                    try:
                        st = entry.stat(follow_symlinks=False)
                        fsize = st.st_size
                        falloc = _calc_allocated(fsize, self._cluster_size)
                        total_size += fsize
                        total_allocated += falloc
                        file_count += 1
                        direct_files.append(FileEntry(
                            name=entry.name, path=entry.path,
                            size_bytes=fsize, allocated_bytes=falloc))
                        if st.st_mtime > max_mtime:
                            max_mtime = st.st_mtime
                    except (PermissionError, OSError) as e:
                        logger.debug("Cannot access file %s: %s", entry, e)

                elif entry.is_dir(follow_symlinks=False):
                    folder_count += 1

                    if current_depth < max_depth:
                        child_info = self._scan_recursive(
                            entry.path,
                            max_depth,
                            current_depth + 1,
                            progress_callback,
                            items_scanned,
                            last_progress_time,
                        )
                        if child_info:
                            children.append(child_info)
                            total_size += child_info.size_bytes
                            total_allocated += child_info.allocated_bytes
                            file_count += child_info.file_count
                            folder_count += child_info.folder_count
                            try:
                                if child_info.last_modified:
                                    child_mt = datetime.datetime.strptime(
                                        child_info.last_modified, '%m/%d/%Y'
                                    ).timestamp()
                                    if child_mt > max_mtime:
                                        max_mtime = child_mt
                            except Exception:
                                pass
                    else:
                        child_size, child_alloc = self._get_folder_size_fast(
                            entry.path, items_scanned)
                        entry_mtime = 0.0
                        try:
                            entry_mtime = float(
                                entry.stat(
                                    follow_symlinks=False).st_mtime)
                        except Exception:
                            pass
                        try:
                            child_modified = (
                                datetime.datetime.fromtimestamp(
                                    entry_mtime).strftime('%m/%d/%Y')
                                if entry_mtime > 0 else '')
                        except Exception:
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
                        )
                        children.append(child_info)
                        total_size += child_size
                        total_allocated += child_alloc
                        has_unscanned = True
                        if entry_mtime > max_mtime:
                            max_mtime = entry_mtime
            except Exception as e:
                logger.debug("Error processing entry %s: %s", entry, e)

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
        )

    def _get_folder_size_fast(
        self, path: str,
        items_scanned: Optional[List[int]] = None,
    ) -> Tuple[int, int]:
        """Get total size and allocated size using os.scandir (D6: avoid walk+stat)."""
        total = 0
        allocated = 0
        stack = [path]
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
                            try:
                                if entry.is_file(follow_symlinks=False):
                                    fsize = entry.stat(
                                        follow_symlinks=False).st_size
                                    total += fsize
                                    allocated += _calc_allocated(
                                        fsize, self._cluster_size)
                                    if items_scanned is not None:
                                        items_scanned[0] += 1
                                elif entry.is_dir(follow_symlinks=False):
                                    stack.append(entry.path)
                            except (PermissionError, OSError):
                                pass
                except (PermissionError, OSError) as e:
                    logger.debug("Cannot scan %s: %s", current, e)
        except Exception as e:
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
