"""Storage monitor service - Poll disk space and detect low space."""
import logging
from typing import Dict, List, Optional

import psutil
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from features.storage_monitor.polling import check_drives, periodic_maintenance
from features.storage_monitor.utils import DriveInfo, get_all_drives

logger = logging.getLogger(__name__)


class StorageMonitor(QObject):
    """Service for monitoring disk space."""

    # Signal emitted when low space is detected
    low_space_detected = pyqtSignal(DriveInfo)
    # Signal emitted when a drive recovers from low space
    low_space_cleared = pyqtSignal(str)

    # Run gc.collect() and log RSS every N polling cycles (D-CB-015/017)
    _GC_INTERVAL = 100
    # Per-drive notification cooldown in seconds (R-007, FM-CB-006, STPA REQ-8)
    _COOLDOWN_SECONDS = 24 * 3600

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
            self._notified_drives: Dict[str, float] = {}
            self._poll_cycle_count: int = 0
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

    def set_notified_drives(self, drives) -> None:
        """Restore notified-drive cooldown state from persisted data."""
        try:
            if isinstance(drives, dict):
                self._notified_drives = {
                    str(drive): float(ts) for drive, ts in drives.items()
                }
            elif isinstance(drives, list):
                # Legacy config format (list only): allow immediate notifications.
                self._notified_drives = {str(drive): 0.0 for drive in drives}
            else:
                raise TypeError("drives must be a dict or list")
        except Exception as e:
            logger.error("Failed to set notified drives: %s", e)
            self._notified_drives = {}

    def update_threshold(self, threshold_gb: int) -> None:
        """Update low-space threshold at runtime and re-evaluate drives."""
        try:
            self._threshold_gb = max(1, int(threshold_gb))
            self._check_drives()
        except Exception as e:
            logger.error("Failed to update threshold to %s: %s", threshold_gb, e)

    def update_interval(self, interval_seconds: int) -> None:
        """Update polling interval at runtime."""
        try:
            self._interval_ms = max(1, int(interval_seconds)) * 1000
            if self._timer.isActive():
                self._timer.start(self._interval_ms)
        except Exception as e:
            logger.error("Failed to update interval to %s: %s", interval_seconds, e)

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
            check_drives(self, get_all_drives, logger)
        except Exception as e:
            logger.error("Error checking drives: %s", e)

    def _periodic_maintenance(self) -> None:
        """Run gc.collect off main thread and log RSS (D-CB-015/017)."""
        periodic_maintenance(logger, psutil)
