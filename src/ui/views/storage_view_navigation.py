"""Pure navigation helpers for StorageView history management."""

from __future__ import annotations

from typing import List, Optional, Tuple

from features.folder_scanner import FolderInfo


def navigate_back_state(
    current_path: Optional[str],
    history: List[str],
    forward: List[str],
) -> Tuple[Optional[str], List[str], List[str]]:
    """Compute state transition for back navigation."""
    if not history:
        return current_path, history, forward

    new_history = history.copy()
    prev_path = new_history.pop()
    new_forward = forward.copy()
    if current_path:
        new_forward.append(current_path)
    return prev_path, new_history, new_forward


def navigate_forward_state(
    current_path: Optional[str],
    history: List[str],
    forward: List[str],
) -> Tuple[Optional[str], List[str], List[str]]:
    """Compute state transition for forward navigation."""
    if not forward:
        return current_path, history, forward

    new_forward = forward.copy()
    next_path = new_forward.pop()
    new_history = history.copy()
    if current_path:
        new_history.append(current_path)
    return next_path, new_history, new_forward


def resolve_cached_node(
    path: str,
    path_index: dict[str, FolderInfo],
    scan_cache: dict[str, FolderInfo],
) -> Optional[FolderInfo]:
    """Resolve cached FolderInfo using the same precedence as StorageView."""
    return path_index.get(path) or scan_cache.get(path)
