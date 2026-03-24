"""Polling and maintenance helpers for StorageMonitor."""
from __future__ import annotations

import gc
import os
import threading
import time


def check_drives(monitor, get_all_drives_fn, logger) -> None:
    """Check drives and emit low-space / recovered signals."""
    drives = get_all_drives_fn()

    for drive in drives:
        if drive.free_gb < monitor._threshold_gb:
            last_notified = monitor._notified_drives.get(drive.letter)
            now = time.time()
            if (
                last_notified is None
                or (now - last_notified) >= monitor._COOLDOWN_SECONDS
            ):
                logger.warning(
                    "Low space detected on %s: %.1f GB free",
                    drive.letter,
                    drive.free_gb,
                )
                monitor._notified_drives[drive.letter] = now
                monitor.low_space_detected.emit(drive)
        else:
            if drive.letter in monitor._notified_drives:
                del monitor._notified_drives[drive.letter]
                monitor.low_space_cleared.emit(drive.letter)
                logger.info(
                    "Drive %s now has sufficient space: %.1f GB",
                    drive.letter,
                    drive.free_gb,
                )

    del drives
    monitor._poll_cycle_count += 1
    if monitor._poll_cycle_count >= monitor._GC_INTERVAL:
        monitor._poll_cycle_count = 0
        monitor._periodic_maintenance()


def periodic_maintenance(logger, psutil_module) -> None:
    """Run gc.collect off main thread and log RSS."""

    def _maintenance() -> None:
        try:
            gc.collect()
            rss_mb = psutil_module.Process(os.getpid()).memory_info().rss / (1024 ** 2)
            logger.info("StorageMonitor maintenance: gc.collect() done, RSS=%.1f MB", rss_mb)
        except Exception as error:
            logger.error("Periodic maintenance error: %s", error)

    threading.Thread(target=_maintenance, daemon=True).start()
