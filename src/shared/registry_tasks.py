"""Helpers for Task Scheduler command construction."""

from __future__ import annotations

from typing import List

from shared.constants import APP_NAME


def build_create_task_command(schtasks_path: str, target_command: str) -> List[str]:
    """Build schtasks command for creating the app's logon task."""
    return [
        schtasks_path,
        "/create",
        "/tn",
        APP_NAME,
        "/tr",
        target_command,
        "/sc",
        "onlogon",
        "/rl",
        "limited",
        "/f",
    ]


def build_delete_task_command(schtasks_path: str) -> List[str]:
    """Build schtasks command for deleting the app's fallback task."""
    return [schtasks_path, "/delete", "/tn", APP_NAME, "/f"]
