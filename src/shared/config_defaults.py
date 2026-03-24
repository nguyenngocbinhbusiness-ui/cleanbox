"""Default configuration payload helpers."""


def build_default_config(default_threshold_gb: int, default_interval_seconds: int) -> dict:
    """Return the default configuration dictionary."""
    return {
        "cleanup_directories": [],
        "first_run_complete": False,
        "low_space_threshold_gb": default_threshold_gb,
        "polling_interval_seconds": default_interval_seconds,
        "auto_start_enabled": True,
        "notified_drives": {},
    }
