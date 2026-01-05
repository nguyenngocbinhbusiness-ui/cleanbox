"""Storage monitor utilities."""
import logging
from dataclasses import dataclass
from typing import List

import psutil

logger = logging.getLogger(__name__)


@dataclass
class DriveInfo:
    """Information about a drive."""
    letter: str
    total_gb: float
    free_gb: float
    used_gb: float
    percent_used: float

    @property
    def is_low_space(self) -> bool:
        """Check if drive has low space (< threshold)."""
        try:
            # Default threshold, will be overridden by config
            return self.free_gb < 10
        except Exception:
            return False


def get_all_drives() -> List[DriveInfo]:
    """Get information about all fixed drives."""
    drives = []

    try:
        for partition in psutil.disk_partitions():
            # Skip removable and network drives
            if "fixed" not in partition.opts.lower() and "cdrom" not in partition.opts.lower():
                # On Windows, check if it's a local drive
                if not partition.device.startswith(
                        ("C:", "D:", "E:", "F:", "G:", "H:")):
                    continue

            try:
                usage = psutil.disk_usage(partition.mountpoint)
                drive = DriveInfo(
                    letter=partition.device[:2],
                    total_gb=usage.total / (1024**3),
                    free_gb=usage.free / (1024**3),
                    used_gb=usage.used / (1024**3),
                    percent_used=usage.percent,
                )
                drives.append(drive)
                logger.debug(
                    "Drive %s: %.1f GB free / %.1f GB total",
                    drive.letter,
                    drive.free_gb,
                    drive.total_gb,
                )
            except (PermissionError, OSError) as e:
                logger.warning(
                    "Cannot access drive %s: %s",
                    partition.device,
                    e)
    except Exception as e:
        logger.error("Failed to enumerate drives: %s", e)

    return drives
