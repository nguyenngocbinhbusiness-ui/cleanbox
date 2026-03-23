"""Unit tests for folder scanner parallel executor helper."""

from types import SimpleNamespace

from features.folder_scanner.parallel_executor import scan_realtime_directories


def test_parallel_executor_merges_children():
    dirs = [SimpleNamespace(path="a"), SimpleNamespace(path="b")]
    merged = []

    def scan_entry(entry):
        return SimpleNamespace(path=entry.path)

    scan_realtime_directories(
        dirs=dirs,
        parallel_workers=2,
        is_cancelled=lambda: False,
        scan_entry=scan_entry,
        merge_child=merged.append,
        on_parallel_error=lambda exc: None,
    )

    assert sorted(child.path for child in merged) == ["a", "b"]


def test_parallel_executor_fallback_on_parallel_error():
    dirs = [SimpleNamespace(path="a")]
    merged = []
    errors = []
    calls = {"n": 0}

    def scan_entry(entry):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("first pass failure")
        return SimpleNamespace(path=entry.path)

    scan_realtime_directories(
        dirs=dirs,
        parallel_workers=1,
        is_cancelled=lambda: False,
        scan_entry=scan_entry,
        merge_child=merged.append,
        on_parallel_error=errors.append,
    )

    assert errors
    assert [child.path for child in merged] == ["a"]
