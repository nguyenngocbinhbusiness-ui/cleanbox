"""ConfigManager - Load/save JSON configuration."""
import logging
import os
import time
from typing import Dict, List

from shared.config_defaults import build_default_config
from shared.config_io import cleanup_stale_tmp_files, load_json_config, save_json_config
from shared.constants import (
    CONFIG_DIR,
    CONFIG_FILE,
    DEFAULT_THRESHOLD_GB,
    DEFAULT_POLLING_INTERVAL_SECONDS,
)
from shared.config.schema import (
    filter_protected_cleanup_directories,
    normalize_notified_drives,
)
from shared.utils import is_protected_path

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration with JSON persistence."""

    def __init__(self):
        """Initialize and load configuration."""
        try:
            self._config: dict = {}
            self._ensure_config_dir()
            self.load()
        except Exception as e:
            logger.error("Failed to initialize ConfigManager: %s", e)
            self._config = self._get_default_config()

    def _ensure_config_dir(self) -> None:
        """Create config directory if not exists."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error("Failed to create config directory: %s", e)

    def _get_default_config(self) -> dict:
        """Return default configuration."""
        try:
            return build_default_config(
                default_threshold_gb=DEFAULT_THRESHOLD_GB,
                default_interval_seconds=DEFAULT_POLLING_INTERVAL_SECONDS,
            )
        except Exception as e:
            logger.error("Failed to get default config: %s", e)
            return {}

    def _cleanup_stale_tmp(self) -> None:
        """Remove leftover .tmp files from config directory (DRBFM D-CB-014)."""
        cleanup_stale_tmp_files(CONFIG_DIR, logger)

    def load(self) -> None:
        """Load configuration from file."""
        self._cleanup_stale_tmp()
        loaded, from_backup = load_json_config(CONFIG_FILE, logger)

        if loaded is None:
            if CONFIG_FILE.exists():
                logger.warning("Falling back to default config")
            else:
                logger.info("No config file found, using defaults")
            self._config = self._get_default_config()
            return

        self._config = loaded
        self._config.pop("run_as_admin_enabled", None)
        self._normalize_notified_drives()
        self._filter_protected_paths()
        if from_backup:
            logger.warning(
                "Recovered config from backup %s",
                CONFIG_FILE.with_suffix(".json.bak"),
            )
        else:
            logger.info("Configuration loaded from %s", CONFIG_FILE)

    def _normalize_notified_drives(self) -> None:
        """Normalize notified drive state to a drive->timestamp mapping."""
        raw = self._config.get("notified_drives", {})
        self._config["notified_drives"] = normalize_notified_drives(raw)

    def save(self) -> None:
        """Save configuration atomically with backup (DRBFM D-CB-011/012)."""
        save_json_config(CONFIG_FILE, self._config, logger, replace_func=os.replace)

    def _filter_protected_paths(self) -> None:
        """Remove any protected system paths from cleanup_directories."""
        filtered, removed = filter_protected_cleanup_directories(
            self._config.get("cleanup_directories", [])
        )
        if removed:
            for p in removed:
                logger.warning("Removed protected path from config: %s", p)
            self._config["cleanup_directories"] = filtered
            self.save()

    @property
    def is_first_run(self) -> bool:
        """Check if this is the first run."""
        try:
            return not self._config.get("first_run_complete", False)
        except Exception as e:
            logger.error("Failed to check first run: %s", e)
            return True

    def mark_first_run_complete(self) -> None:
        """Mark first run as complete."""
        try:
            self._config["first_run_complete"] = True
            self.save()
        except Exception as e:
            logger.error("Failed to mark first run complete: %s", e)

    @property
    def cleanup_directories(self) -> List[str]:
        """Get list of cleanup directories."""
        try:
            directories = self._config.get("cleanup_directories", [])
            if isinstance(directories, list):
                return list(directories)
            return []
        except Exception as e:
            logger.error("Failed to get cleanup directories: %s", e)
            return []

    def add_directory(self, path: str) -> bool:
        """Add a directory to cleanup list."""
        try:
            if is_protected_path(path):
                logger.warning("Blocked adding protected path to config: %s", path)
                return False

            # Ensure list exists
            if "cleanup_directories" not in self._config:
                self._config["cleanup_directories"] = []

            if path not in self.cleanup_directories:
                self._config["cleanup_directories"].append(path)
                self.save()
                return True
            return False
        except Exception as e:
            logger.error("Failed to add directory %s: %s", path, e)
            return False

    def remove_directory(self, path: str) -> bool:
        """Remove a directory from cleanup list."""
        try:
            if path in self.cleanup_directories:
                self._config["cleanup_directories"].remove(path)
                self.save()
                return True
            return False
        except Exception as e:
            logger.error("Failed to remove directory %s: %s", path, e)
            return False

    @property
    def threshold_gb(self) -> int:
        """Get low space threshold in GB."""
        try:
            return self._config.get("low_space_threshold_gb", DEFAULT_THRESHOLD_GB)
        except Exception as e:
            logger.error("Failed to get threshold: %s", e)
            return DEFAULT_THRESHOLD_GB

    @threshold_gb.setter
    def threshold_gb(self, value: int) -> None:
        """Persist low space threshold in GB."""
        try:
            self._config["low_space_threshold_gb"] = max(1, int(value))
            self.save()
        except Exception as e:
            logger.error("Failed to set threshold: %s", e)

    @property
    def polling_interval(self) -> int:
        """Get polling interval in seconds."""
        try:
            return self._config.get(
                "polling_interval_seconds",
                DEFAULT_POLLING_INTERVAL_SECONDS)
        except Exception as e:
            logger.error("Failed to get polling interval: %s", e)
            return DEFAULT_POLLING_INTERVAL_SECONDS

    @polling_interval.setter
    def polling_interval(self, value: int) -> None:
        """Persist polling interval in seconds."""
        try:
            self._config["polling_interval_seconds"] = max(1, int(value))
            self.save()
        except Exception as e:
            logger.error("Failed to set polling interval: %s", e)

    @property
    def auto_start_enabled(self) -> bool:
        """Check if auto-start is enabled."""
        try:
            return self._config.get("auto_start_enabled", True)
        except Exception as e:
            logger.error("Failed to check auto start: %s", e)
            return True

    @auto_start_enabled.setter
    def auto_start_enabled(self, value: bool) -> None:
        """Set auto-start enabled."""
        try:
            self._config["auto_start_enabled"] = value
            self.save()
        except Exception as e:
            logger.error("Failed to set auto start: %s", e)

    def get_notified_drives(self) -> List[str]:
        """Get list of drives that have been notified."""
        try:
            self._normalize_notified_drives()
            return list(self._config.get("notified_drives", {}).keys())
        except Exception as e:
            logger.error("Failed to get notified drives: %s", e)
            return []

    def get_notified_drive_timestamps(self) -> Dict[str, float]:
        """Get notified drives and last notification timestamps."""
        try:
            self._normalize_notified_drives()
            return dict(self._config.get("notified_drives", {}))
        except Exception as e:
            logger.error("Failed to get notified drive timestamps: %s", e)
            return {}

    def add_notified_drive(
        self,
        drive: str,
        timestamp: float | None = None,
    ) -> None:
        """Add a drive to notified list."""
        try:
            self._normalize_notified_drives()
            notified = self._config.get("notified_drives", {})
            notified[drive] = float(timestamp) if timestamp is not None else time.time()
            self._config["notified_drives"] = notified
            self.save()
        except Exception as e:
            logger.error("Failed to add notified drive %s: %s", drive, e)

    def remove_notified_drive(self, drive: str) -> None:
        """Remove a drive from notified list."""
        try:
            self._normalize_notified_drives()
            notified = self._config.get("notified_drives", {})
            if drive in notified:
                del notified[drive]
                self._config["notified_drives"] = notified
                self.save()
        except Exception as e:
            logger.error("Failed to remove notified drive %s: %s", drive, e)
