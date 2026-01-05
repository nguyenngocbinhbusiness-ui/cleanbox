"""ConfigManager - Load/save JSON configuration."""
import json
import logging
from typing import List

from shared.constants import (
    CONFIG_DIR,
    CONFIG_FILE,
    DEFAULT_THRESHOLD_GB,
    DEFAULT_POLLING_INTERVAL_SECONDS,
)

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
            return {
                "cleanup_directories": [],
                "first_run_complete": False,
                "low_space_threshold_gb": DEFAULT_THRESHOLD_GB,
                "polling_interval_seconds": DEFAULT_POLLING_INTERVAL_SECONDS,
                "auto_start_enabled": True,
                "notified_drives": [],
            }
        except Exception as e:
            logger.error("Failed to get default config: %s", e)
            return {}

    def load(self) -> None:
        """Load configuration from file."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                logger.info("Configuration loaded from %s", CONFIG_FILE)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Failed to load config, using defaults: %s", e)
                self._config = self._get_default_config()
        else:
            logger.info("No config file found, using defaults")
            self._config = self._get_default_config()

    def save(self) -> None:
        """Save configuration to file."""
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2)
            logger.info("Configuration saved to %s", CONFIG_FILE)
        except IOError as e:
            logger.error("Failed to save config: %s", e)

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
            return self._config.get("cleanup_directories", [])
        except Exception as e:
            logger.error("Failed to get cleanup directories: %s", e)
            return []

    def add_directory(self, path: str) -> bool:
        """Add a directory to cleanup list."""
        try:
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
            return self._config.get("notified_drives", [])
        except Exception as e:
            logger.error("Failed to get notified drives: %s", e)
            return []

    def add_notified_drive(self, drive: str) -> None:
        """Add a drive to notified list."""
        try:
            notified = self.get_notified_drives()
            if drive not in notified:
                notified.append(drive)
                self._config["notified_drives"] = notified
                self.save()
        except Exception as e:
            logger.error("Failed to add notified drive %s: %s", drive, e)

    def remove_notified_drive(self, drive: str) -> None:
        """Remove a drive from notified list."""
        try:
            notified = self.get_notified_drives()
            if drive in notified:
                notified.remove(drive)
                self._config["notified_drives"] = notified
                self.save()
        except Exception as e:
            logger.error("Failed to remove notified drive %s: %s", drive, e)

