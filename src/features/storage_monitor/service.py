"""Storage monitor service - Poll disk space and detect low space."""
import gc
import logging
import os
import threading
import time
from typing import Dict, List, Optional

import psutil
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from features.storage_monitor.utils import DriveInfo, get_all_drives

logger = logging.getLogger(__name__)


class StorageMonitor(QObject):
    """Service for monitoring disk space."""

    # Signal emitted when low space is detected
    low_space_detected = pyqtSignal(DriveInfo)

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

    def set_notified_drives(self, drives: List[str]) -> None:
        """Set list of already notified drives (stored with current timestamp)."""
        try:
            now = time.time()
            self._notified_drives = {d: now for d in drives}
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
                    last_notified = self._notified_drives.get(drive.letter)
                    now = time.time()
                    if last_notified is None or (now - last_notified) >= self._COOLDOWN_SECONDS:
                        logger.warning(
                            "Low space detected on %s: %.1f GB free",
                            drive.letter,
                            drive.free_gb,
                        )
                        self._notified_drives[drive.letter] = now
                        self.low_space_detected.emit(drive)
                else:
                    # Drive has enough space, remove from notified list
                    if drive.letter in self._notified_drives:
                        del self._notified_drives[drive.letter]
                        logger.info(
                            "Drive %s now has sufficient space: %.1f GB",
                            drive.letter,
                            drive.free_gb,
                        )

            del drives  # Explicit cleanup (D-CB-016)

            # Periodic GC and self-monitoring (D-CB-015/017)
            self._poll_cycle_count += 1
            if self._poll_cycle_count >= self._GC_INTERVAL:
                self._poll_cycle_count = 0
                self._periodic_maintenance()
        except Exception as e:
            logger.error("Error checking drives: %s", e)

    def _periodic_maintenance(self) -> None:
        """Run gc.collect off main thread and log RSS (D-CB-015/017)."""
        def _maintenance() -> None:
            try:
                gc.collect()
                rss_mb = psutil.Process(os.getpid()).memory_info().rss / (1024 ** 2)
                logger.info("StorageMonitor maintenance: gc.collect() done, RSS=%.1f MB", rss_mb)
            except Exception as e:
                logger.error("Periodic maintenance error: %s", e)

        threading.Thread(target=_maintenance, daemon=True).start()
