"""File IO helpers for ConfigManager persistence."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path


def cleanup_stale_tmp_files(config_dir: Path, logger) -> None:
    """Remove leftover .tmp files from the config directory."""
    try:
        for entry in config_dir.iterdir():
            if entry.suffix == ".tmp" and entry.is_file():
                entry.unlink()
                logger.info("Cleaned up stale tmp file: %s", entry)
    except Exception as error:
        logger.warning("Failed to clean stale tmp files: %s", error)


def load_json_config(config_file: Path, logger) -> tuple[dict | None, bool]:
    """Load config from primary file or backup. Returns (config, from_backup)."""
    bak_file = config_file.with_suffix(".json.bak")

    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as handle:
                return json.load(handle), False
        except (json.JSONDecodeError, IOError) as error:
            logger.warning("Failed to load config: %s", error)

        if bak_file.exists():
            try:
                with open(bak_file, "r", encoding="utf-8") as handle:
                    return json.load(handle), True
            except (json.JSONDecodeError, IOError) as backup_error:
                logger.warning("Backup also invalid: %s", backup_error)
    return None, False


def save_json_config(config_file: Path, config: dict, logger, replace_func=os.replace) -> bool:
    """Persist config with backup + atomic write; fallback to direct write."""
    try:
        if config_file.exists():
            bak_file = config_file.with_suffix(".json.bak")
            try:
                shutil.copy2(config_file, bak_file)
            except Exception as error:
                logger.warning("Failed to create config backup: %s", error)

        tmp_file = config_file.with_suffix(".json.tmp")
        try:
            with open(tmp_file, "w", encoding="utf-8") as handle:
                json.dump(config, handle, indent=2)
            replace_func(str(tmp_file), str(config_file))
            logger.info("Configuration saved to %s", config_file)
            return True
        except PermissionError as error:
            logger.warning(
                "Atomic write failed (PermissionError), falling back to direct write: %s",
                error,
            )
            with open(config_file, "w", encoding="utf-8") as handle:
                json.dump(config, handle, indent=2)
            logger.info("Configuration saved (direct) to %s", config_file)
            return True
    except IOError as error:
        logger.error("Failed to save config: %s", error)
        return False
