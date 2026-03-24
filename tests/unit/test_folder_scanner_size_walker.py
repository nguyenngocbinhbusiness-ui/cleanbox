from threading import Event

from features.folder_scanner.size_walker import get_folder_size_fast


def test_get_folder_size_fast_scans_nested_files(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    child = root / "child"
    child.mkdir()
    (root / "a.bin").write_bytes(b"1234")
    (child / "b.bin").write_bytes(b"12345")

    skipped = []
    scanned = [0]
    entries = {"value": 0}
    files = {"value": 0}
    dirs = {"value": 0}

    total, allocated = get_folder_size_fast(
        path=str(root),
        cancel_flag=Event(),
        cluster_size=4096,
        record_skip=lambda exc: skipped.append(exc),
        items_scanned=scanned,
        stats_scanned_entries=lambda: entries.__setitem__("value", entries["value"] + 1),
        stats_scanned_files=lambda: files.__setitem__("value", files["value"] + 1),
        stats_scanned_dirs=lambda: dirs.__setitem__("value", dirs["value"] + 1),
    )

    assert total == 9
    assert allocated == 8192
    assert skipped == []
    assert scanned[0] >= 3
    assert entries["value"] >= 3
    assert files["value"] == 2
    assert dirs["value"] >= 1


def test_get_folder_size_fast_honors_cancel(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "x.bin").write_bytes(b"x")

    cancel = Event()
    cancel.set()

    total, allocated = get_folder_size_fast(
        path=str(root),
        cancel_flag=cancel,
        cluster_size=4096,
        record_skip=lambda exc: None,
    )
    assert total == 0
    assert allocated == 0
