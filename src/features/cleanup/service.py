"""Cleanup service - Delete files from configured directories."""
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List

import winshell

from shared.constants import RECYCLE_BIN_MARKER
from shared.utils import is_protected_path, ProtectedPathError

logger = logging.getLogger(__name__)


@dataclass
class CleanupResult:
    """Result of a cleanup operation."""
    total_files: int = 0
    total_folders: int = 0
    total_size_bytes: int = 0
    errors: List[str] = None

    def __post_init__(self):
        """Initialize default values and handle errors."""
        try:
            if self.errors is None:
                self.errors = []
        except Exception:
            self.errors = []

    @property
    def total_size_mb(self) -> float:
        """Get total size in MB."""
        try:
            return self.total_size_bytes / (1024 * 1024)
        except Exception:
            return 0.0


class CleanupService:
    """Service for cleaning up directories."""

    def _recycle_item(self, item: Path) -> bool:
        """Move an item to the Recycle Bin when Windows supports it."""
        try:
            winshell.delete_file(
                str(item),
                allow_undo=True,
                no_confirm=True,
                silent=True,
            )
            return True
        except Exception as e:
            logger.debug("Recycle Bin move failed for %s: %s", item, e)
            return False

    def cleanup_directory(self, path: str) -> CleanupResult:
        """
        Clean up a single directory by deleting all its contents.
        The directory itself is preserved.
        """
        result = CleanupResult()

        if is_protected_path(path):
            logger.warning("Blocked cleanup of protected path: %s", path)
            raise ProtectedPathError(
                f"Cannot clean protected system directory: {path}"
            )

        dir_path = Path(path)

        if not dir_path.exists():
            logger.warning("Directory not found: %s", path)
            result.errors.append(f"Directory not found: {path}")
            return result

        if not dir_path.is_dir():
            logger.warning("Path is not a directory: %s", path)
            result.errors.append(f"Not a directory: {path}")
            return result

        for item in dir_path.iterdir():
            try:
                if item.is_file():
                    size = item.stat().st_size
                    recycled = self._recycle_item(item)
                    # Some recycle APIs can silently no-op; verify source is gone.
                    if (not recycled) or item.exists():
                        item.unlink()
                    result.total_files += 1
                    result.total_size_bytes += size
                elif item.is_dir():
                    size = self._get_dir_size(item)
                    recycled = self._recycle_item(item)
                    # Ensure directory is actually removed even if recycle reports success.
                    if (not recycled) or item.exists():
                        shutil.rmtree(item)
                    result.total_folders += 1
                    result.total_size_bytes += size
            except PermissionError:
                logger.warning("Permission denied: %s", item)
                result.errors.append(f"Permission denied: {item}")
            except Exception as e:
                logger.error("Error deleting %s: %s", item, e)
                result.errors.append(f"Error: {item} - {e}")

        logger.info(
            "Cleaned %s: %d files, %d folders, %.2f MB",
            path,
            result.total_files,
            result.total_folders,
            result.total_size_mb,
        )
        return result

    def empty_recycle_bin(self) -> CleanupResult:
        """Empty the Windows Recycle Bin."""
        result = CleanupResult()
        try:
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
            logger.info("Recycle Bin emptied")
            result.total_folders = 1  # Count as 1 "folder" for stats
        except Exception as e:
            logger.warning("winshell failed to empty Recycle Bin: %s. Trying ctypes fallback.", e)
            try:
                import ctypes
                # SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x0007)
                logger.info("Recycle Bin emptied via ctypes fallback")
                result.total_folders = 1
            except Exception as fallback_err:
                logger.error("Both winshell and ctypes failed to empty Recycle Bin: %s", fallback_err)
                result.errors.append(f"Recycle Bin error: winshell={e}, ctypes={fallback_err}")
        return result

    def cleanup_all(self, directories: List[str]) -> CleanupResult:
        """Clean up all configured directories."""
        total_result = CleanupResult()

        try:
            for directory in directories:
                if directory == RECYCLE_BIN_MARKER:
                    result = self.empty_recycle_bin()
                else:
                    if not Path(directory).exists():
                        logger.warning("Skipping non-existent path: %s", directory)
                        total_result.errors.append(
                            f"Skipped (path not found): {directory}"
                        )
                        continue
                    result = self.cleanup_directory(directory)

                total_result.total_files += result.total_files
                total_result.total_folders += result.total_folders
                total_result.total_size_bytes += result.total_size_bytes
                total_result.errors.extend(result.errors)
        except Exception as e:
            logger.error("Cleanup failed: %s", e)
            total_result.errors.append(f"Cleanup failed: {e}")

        return total_result

    def _get_dir_size(self, path: Path) -> int:
        """Calculate total size of a directory."""
        total = 0
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    try:
                        total += item.stat().st_size
                    except (PermissionError, OSError) as e:
                        logger.debug("Cannot stat file %s: %s", item, e)
        except (PermissionError, OSError) as e:
            logger.debug("Cannot walk directory %s: %s", path, e)
        return total
