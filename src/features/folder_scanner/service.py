"""Folder Scanner - Recursive folder size calculation."""
import os
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Callable, List
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)


@dataclass
class FolderInfo:
    """Information about a folder's size and contents."""
    path: str
    name: str
    size_bytes: int
    file_count: int
    folder_count: int
    children: List['FolderInfo']

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
        try:
            if self.size_bytes >= 1024 * 1024 * 1024:
                return f"{self.size_gb:.2f} GB"
            elif self.size_bytes >= 1024 * 1024:
                return f"{self.size_mb:.2f} MB"
            elif self.size_bytes >= 1024:
                return f"{self.size_bytes / 1024:.2f} KB"
            else:
                return f"{self.size_bytes} B"
        except Exception:
            return "0 B"


class FolderScanner:
    """
    Service for recursively scanning folder sizes.

    Supports:
    - Async scanning with progress callbacks
    - Scan cancellation
    - Error handling for inaccessible folders
    """

    def __init__(self):
        """Initialize the folder scanner service."""
        try:
            self._cancel_flag = threading.Event()
            self._executor: Optional[ThreadPoolExecutor] = None
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
        items_scanned = [0]

        try:
            return self._scan_recursive(
                path, max_depth, 0, progress_callback, items_scanned)
        except Exception as e:
            logger.error("Scan failed for %s: %s", path, e)
            return None
        finally:
            self._cancel_flag.clear()
            logger.debug("Scan resources cleaned up")

    def _scan_recursive(
        self,
        path: str,
        max_depth: int,
        current_depth: int,
        progress_callback: Optional[Callable[[str, int], None]],
        items_scanned: List[int],
    ) -> Optional[FolderInfo]:
        """Recursive folder scanning."""
        if self._cancel_flag.is_set():
            return None

        path_obj = Path(path)
        total_size = 0
        file_count = 0
        folder_count = 0
        children: List[FolderInfo] = []

        try:
            entries = list(path_obj.iterdir())
        except PermissionError:
            logger.debug("Permission denied: %s", path)
            return FolderInfo(
                path=path,
                name=path_obj.name or path,
                size_bytes=0,
                file_count=0,
                folder_count=0,
                children=[],
            )
        except Exception as e:
            logger.debug("Cannot access %s: %s", path, e)
            return FolderInfo(
                path=path,
                name=path_obj.name or path,
                size_bytes=0,
                file_count=0,
                folder_count=0,
                children=[],
            )

        for entry in entries:
            if self._cancel_flag.is_set():
                return None

            items_scanned[0] += 1

            if progress_callback and items_scanned[0] % 100 == 0:
                progress_callback(str(entry), items_scanned[0])

            try:
                if entry.is_file():
                    try:
                        total_size += entry.stat().st_size
                        file_count += 1
                    except (PermissionError, OSError) as e:
                        logger.debug("Cannot access file %s: %s", entry, e)

                elif entry.is_dir():
                    folder_count += 1

                    if current_depth < max_depth:
                        # Recurse into subfolder
                        child_info = self._scan_recursive(
                            str(entry),
                            max_depth,
                            current_depth + 1,
                            progress_callback,
                            items_scanned,
                        )
                        if child_info:
                            children.append(child_info)
                            total_size += child_info.size_bytes
                            file_count += child_info.file_count
                            folder_count += child_info.folder_count
                    else:
                        # Just get size without children
                        child_size = self._get_folder_size_fast(str(entry))
                        child_info = FolderInfo(
                            path=str(entry),
                            name=entry.name,
                            size_bytes=child_size,
                            file_count=0,
                            folder_count=0,
                            children=[],
                        )
                        children.append(child_info)
                        total_size += child_size
            except Exception as e:
                logger.debug("Error processing entry %s: %s", entry, e)

        # Sort children by size (largest first)
        children.sort(key=lambda x: x.size_bytes, reverse=True)

        return FolderInfo(
            path=path,
            name=path_obj.name or path,
            size_bytes=total_size,
            file_count=file_count,
            folder_count=folder_count,
            children=children,
        )

    def _get_folder_size_fast(self, path: str) -> int:
        """Get total size of folder without tracking children."""
        total = 0
        try:
            for root, dirs, files in os.walk(path):
                if self._cancel_flag.is_set():
                    return total
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except (PermissionError, OSError) as e:
                        logger.debug("Cannot get size of %s: %s", f, e)
        except (PermissionError, OSError) as e:
            logger.debug("Cannot walk path %s: %s", path, e)
        return total

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
