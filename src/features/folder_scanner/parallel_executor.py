"""Parallel scan orchestration helpers for FolderScanner."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Iterable, Set


def scan_realtime_directories(
    dirs: Iterable[Any],
    parallel_workers: int,
    is_cancelled: Callable[[], bool],
    scan_entry: Callable[[Any], Any],
    merge_child: Callable[[Any], None],
    on_parallel_error: Callable[[Exception], None],
) -> None:
    """
    Parallel-first scan with sequential fallback.

    RuntimeError is reserved for cancellation and is intentionally bubbled up.
    """
    completed_paths: Set[str] = set()
    dir_list = list(dirs)

    try:
        with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
            future_to_entry = {}
            for entry in dir_list:
                if is_cancelled():
                    break
                future_to_entry[executor.submit(scan_entry, entry)] = entry

            for future in as_completed(future_to_entry):
                if is_cancelled():
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise RuntimeError("scan cancelled")
                child_info = future.result()
                if child_info is None:
                    continue
                entry = future_to_entry[future]
                completed_paths.add(getattr(entry, "path", ""))
                merge_child(child_info)
    except Exception as exc:
        if isinstance(exc, RuntimeError) and str(exc) == "scan cancelled":
            raise
        on_parallel_error(exc)
        for entry in dir_list:
            if is_cancelled():
                raise RuntimeError("scan cancelled")
            entry_path = getattr(entry, "path", "")
            if entry_path in completed_paths:
                continue
            child_info = scan_entry(entry)
            if child_info is not None:
                merge_child(child_info)
