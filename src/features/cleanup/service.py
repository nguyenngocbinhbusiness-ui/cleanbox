"""Cleanup service - Delete files from configured directories."""
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List

import winshell

from shared.constants import RECYCLE_BIN_MARKER

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

    def cleanup_directory(self, path: str) -> CleanupResult:
        """
        Clean up a single directory by deleting all its contents.
        The directory itself is preserved.
        """
        result = CleanupResult()
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
                    item.unlink()
                    result.total_files += 1
                    result.total_size_bytes += size
                elif item.is_dir():
                    size = self._get_dir_size(item)
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
            # Get size before emptying (approximate)
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
            logger.info("Recycle Bin emptied")
            result.total_folders = 1  # Count as 1 "folder" for stats
        except Exception as e:
            logger.error("Failed to empty Recycle Bin: %s", e)
            result.errors.append(f"Recycle Bin error: {e}")
        return result

    def cleanup_all(self, directories: List[str]) -> CleanupResult:
        """Clean up all configured directories."""
        total_result = CleanupResult()

        try:
            for directory in directories:
                if directory == RECYCLE_BIN_MARKER:
                    result = self.empty_recycle_bin()
                else:
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
