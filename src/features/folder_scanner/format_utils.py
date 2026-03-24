"""Formatting helpers for folder scanner output."""

from __future__ import annotations


def format_size(size_bytes: int) -> str:
    """Human-readable size string (TreeSize-style)."""
    try:
        if size_bytes >= 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 ** 3):.1f} GB"
        if size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
        if size_bytes >= 1024:
            return f"{size_bytes / 1024:.1f} KB"
        return f"{size_bytes} Bytes"
    except Exception:
        return "0 Bytes"
