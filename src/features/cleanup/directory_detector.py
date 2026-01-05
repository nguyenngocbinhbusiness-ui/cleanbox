"""Directory detector - Auto-detect default cleanup directories."""
import logging
from pathlib import Path
from typing import List

from shared.constants import RECYCLE_BIN_MARKER

logger = logging.getLogger(__name__)


def get_downloads_folder() -> str:
    """
    Get the Downloads folder path for current user.
    Works on any Windows machine regardless of username.
    """
    try:
        downloads = Path.home() / "Downloads"
        if downloads.exists():
            logger.info("Detected Downloads folder: %s", downloads)
            return str(downloads)
        logger.warning("Downloads folder not found at %s", downloads)
        return ""
    except Exception as e:
        logger.error("Failed to detect Downloads folder: %s", e)
        return ""


def get_default_directories() -> List[str]:
    """
    Get list of default cleanup directories.
    Includes Downloads folder and Recycle Bin marker.
    """
    try:
        directories = []

        # Add Downloads folder
        downloads = get_downloads_folder()
        if downloads:
            directories.append(downloads)

        # Add Recycle Bin marker (handled specially by cleanup service)
        directories.append(RECYCLE_BIN_MARKER)

        logger.info("Default directories detected: %s", directories)
        return directories
    except Exception as e:
        logger.error("Failed to get default directories: %s", e)
        return [RECYCLE_BIN_MARKER]
