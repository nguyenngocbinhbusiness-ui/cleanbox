"""Cleanup progress worker - Background thread for cleanup with progress signals."""
import logging
from typing import List

from PyQt6.QtCore import QThread, pyqtSignal

from shared.constants import RECYCLE_BIN_MARKER
from features.cleanup.service import CleanupService, CleanupResult

logger = logging.getLogger(__name__)


class CleanupProgressWorker(QThread):
    """Background worker for cleanup operations with progress reporting.
    
    Runs cleanup in a separate thread to keep UI responsive.
    Emits progress signals as each directory is processed.
    """
    
    # Signals
    progress_updated = pyqtSignal(int, int)  # (current_index, total_count)
    cleanup_finished = pyqtSignal(object)    # CleanupResult
    
    def __init__(self, directories: List[str], parent=None):
        """Initialize the cleanup worker.
        
        Args:
            directories: List of directory paths to clean up.
            parent: Optional parent QObject.
        """
        try:
            super().__init__(parent)
            self._directories = directories
            self._service = CleanupService()
        except Exception as e:
            logger.error("Failed to init CleanupProgressWorker: %s", e)
    
    def run(self) -> None:
        """Execute cleanup in background thread."""
        total = len(self._directories)
        total_result = CleanupResult()
        
        try:
            for i, directory in enumerate(self._directories):
                # Emit progress before processing
                self.progress_updated.emit(i, total)
                
                try:
                    if directory == RECYCLE_BIN_MARKER:
                        result = self._service.empty_recycle_bin()
                    else:
                        result = self._service.cleanup_directory(directory)
                    
                    # Accumulate results
                    total_result.total_files += result.total_files
                    total_result.total_folders += result.total_folders
                    total_result.total_size_bytes += result.total_size_bytes
                    total_result.errors.extend(result.errors)
                except Exception as e:
                    logger.error("Error cleaning directory %s: %s", directory, e)
                    total_result.errors.append(f"Error: {directory} - {e}")
            
            # Final progress (100%)
            self.progress_updated.emit(total, total)
            
        except Exception as e:
            logger.error("Cleanup worker failed: %s", e)
            total_result.errors.append(f"Cleanup failed: {e}")
        
        # Emit finished signal with result
        self.cleanup_finished.emit(total_result)
