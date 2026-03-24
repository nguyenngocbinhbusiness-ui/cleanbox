"""Tests for storage monitor polling helpers."""
from __future__ import annotations

from types import SimpleNamespace

from features.storage_monitor.polling import check_drives, periodic_maintenance
from features.storage_monitor.utils import DriveInfo


def test_check_drives_emits_and_clears():
    events = []
    cleared = []
    monitor = SimpleNamespace(
        _threshold_gb=10,
        _notified_drives={"C:": 0.0},
        _poll_cycle_count=0,
        _GC_INTERVAL=100,
        _COOLDOWN_SECONDS=24 * 3600,
        low_space_detected=SimpleNamespace(emit=lambda d: events.append(d.letter)),
        low_space_cleared=SimpleNamespace(emit=lambda d: cleared.append(d)),
        _periodic_maintenance=lambda: None,
    )
    drives = [
        DriveInfo("C:", 100.0, 20.0, 80.0, 80.0),
        DriveInfo("D:", 100.0, 3.0, 97.0, 97.0),
    ]

    class _Logger:
        def warning(self, *_args, **_kwargs):
            return None

        def info(self, *_args, **_kwargs):
            return None

    check_drives(monitor, lambda: drives, _Logger())

    assert "C:" not in monitor._notified_drives
    assert "D:" in monitor._notified_drives
    assert events == ["D:"]
    assert cleared == ["C:"]


def test_check_drives_runs_periodic_maintenance():
    called = {"count": 0}
    monitor = SimpleNamespace(
        _threshold_gb=10,
        _notified_drives={},
        _poll_cycle_count=99,
        _GC_INTERVAL=100,
        _COOLDOWN_SECONDS=24 * 3600,
        low_space_detected=SimpleNamespace(emit=lambda _d: None),
        low_space_cleared=SimpleNamespace(emit=lambda _d: None),
        _periodic_maintenance=lambda: called.__setitem__("count", called["count"] + 1),
    )

    class _Logger:
        def warning(self, *_args, **_kwargs):
            return None

        def info(self, *_args, **_kwargs):
            return None

    check_drives(monitor, lambda: [], _Logger())
    assert called["count"] == 1
    assert monitor._poll_cycle_count == 0


def test_periodic_maintenance_starts_thread(monkeypatch):
    started = {"count": 0}

    class _Thread:
        def __init__(self, target, daemon):
            self._target = target
            self._daemon = daemon

        def start(self):
            started["count"] += 1
            self._target()

    class _Psutil:
        class Process:
            def __init__(self, _pid):
                return None

            class _Mem:
                rss = 1024 * 1024

            def memory_info(self):
                return self._Mem()

    class _Logger:
        def info(self, *_args, **_kwargs):
            return None

        def error(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr("features.storage_monitor.polling.threading.Thread", _Thread)
    periodic_maintenance(_Logger(), _Psutil)
    assert started["count"] == 1
