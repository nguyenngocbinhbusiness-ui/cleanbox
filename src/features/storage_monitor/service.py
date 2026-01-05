"""Storage monitor service - Poll disk space and detect low space."""
import logging
from typing import List, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from features.storage_monitor.utils import DriveInfo, get_all_drives

logger = logging.getLogger(__name__)


class StorageMonitor(QObject):
    """Service for monitoring disk space."""

    # Signal emitted when low space is detected
    low_space_detected = pyqtSignal(DriveInfo)

    def __init__(
        self,
        threshold_gb: int = 10,
        interval_seconds: int = 60,
        parent: Optional[QObject] = None,
    ):
        try:
            super().__init__(parent)
            self._threshold_gb = threshold_gb
            self._interval_ms = interval_seconds * 1000
            self._notified_drives: List[str] = []
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._check_drives)
        except Exception as e:
            logger.error("Failed to init StorageMonitor: %s", e)

    def start(self) -> None:
        """Start monitoring."""
        try:
            logger.info(
                "Starting storage monitor (threshold: %dGB, interval: %ds)",
                self._threshold_gb,
                self._interval_ms // 1000,
            )
            self._check_drives()  # Initial check
            self._timer.start(self._interval_ms)
        except Exception as e:
            logger.error("Failed to start storage monitor: %s", e)

    def stop(self) -> None:
        """Stop monitoring."""
        try:
            logger.info("Stopping storage monitor")
            self._timer.stop()
        except Exception as e:
            logger.error("Failed to stop storage monitor: %s", e)
        finally:
            self._notified_drives.clear()
            logger.debug("Storage monitor resources cleaned up")

    def set_notified_drives(self, drives: List[str]) -> None:
        """Set list of already notified drives."""
        try:
            self._notified_drives = drives.copy()
        except Exception as e:
            logger.error("Failed to set notified drives: %s", e)

    def get_low_space_drives(self) -> List[DriveInfo]:
        """Get all drives with low space."""
        try:
            drives = get_all_drives()
            return [d for d in drives if d.free_gb < self._threshold_gb]
        except Exception as e:
            logger.error("Failed to get low space drives: %s", e)
            return []

    def get_all_drives(self) -> List[DriveInfo]:
        """Get information for all drives."""
        try:
            return get_all_drives()
        except Exception as e:
            logger.error("Failed to get all drives: %s", e)
            return []

    def _check_drives(self) -> None:
        """Check all drives for low space."""
        try:
            drives = get_all_drives()

            for drive in drives:
                if drive.free_gb < self._threshold_gb:
                    if drive.letter not in self._notified_drives:
                        logger.warning(
                            "Low space detected on %s: %.1f GB free",
                            drive.letter,
                            drive.free_gb,
                        )
                        self._notified_drives.append(drive.letter)
                        self.low_space_detected.emit(drive)
                else:
                    # Drive has enough space, remove from notified list
                    if drive.letter in self._notified_drives:
                        self._notified_drives.remove(drive.letter)
                        logger.info(
                            "Drive %s now has sufficient space: %.1f GB",
                            drive.letter,
                            drive.free_gb,
                        )
        except Exception as e:
            logger.error("Error checking drives: %s", e)
