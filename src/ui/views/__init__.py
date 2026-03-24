"""UI Views package."""

from __future__ import annotations

from importlib import import_module

__all__ = ["StorageView", "CleanupView", "SettingsView"]


def __getattr__(name: str):
    if name == "StorageView":
        return getattr(import_module("ui.views.storage_view"), name)
    if name == "CleanupView":
        return getattr(import_module("ui.views.cleanup_view"), name)
    if name == "SettingsView":
        return getattr(import_module("ui.views.settings_view"), name)
    raise AttributeError(name)
