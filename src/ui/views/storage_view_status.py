"""Status-text helpers for StorageView."""

from __future__ import annotations

from features.folder_scanner import FolderInfo


def build_scan_complete_text(result: FolderInfo) -> str:
    """Build completion text and include completeness accounting when present."""
    base = (
        f"Scan complete: {result.size_formatted()} in "
        f"{result.file_count:,} files, "
        f"{result.folder_count:,} folders"
    )

    stats = getattr(result, "scan_stats", None)
    if stats is None:
        return base

    scanned_files = getattr(stats, "scanned_files", None)
    scanned_dirs = getattr(stats, "scanned_dirs", None)
    skipped = getattr(stats, "skipped_count", None)
    reasons = getattr(stats, "skipped_reasons", None)

    parts = []
    if isinstance(scanned_files, int):
        parts.append(f"scanned_files={scanned_files}")
    if isinstance(scanned_dirs, int):
        parts.append(f"scanned_dirs={scanned_dirs}")
    if isinstance(skipped, int):
        parts.append(f"skipped={skipped}")
    if isinstance(reasons, dict) and reasons:
        reason_items = [f"{k}:{v}" for k, v in sorted(reasons.items())]
        extra_count = max(0, len(reason_items) - 2)
        compact_reasons = ", ".join(reason_items[:2])
        if extra_count:
            compact_reasons += f", +{extra_count} more"
        parts.append(f"skip_reasons={compact_reasons}")

    if not parts:
        return base
    return f"{base}\n{'; '.join(parts)}"
