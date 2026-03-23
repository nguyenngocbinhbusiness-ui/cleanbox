"""Unit tests for shared.elevation and argument helpers."""

from pathlib import Path

from shared.elevation_args import build_frozen_params, build_script_launch
from shared.elevation import get_elevation_launch_args


def test_build_frozen_params_empty():
    assert build_frozen_params(["app.exe"]) is None


def test_build_frozen_params_with_args():
    params = build_frozen_params(["app.exe", "--mode", "safe"])
    assert params is not None
    assert "--mode" in params
    assert "safe" in params


def test_build_script_launch():
    executable, params = build_script_launch("python", ["main.py", "--x", "1"])
    assert executable.endswith("python") or executable.endswith("python.exe")
    assert params is not None
    assert "main.py" in params
    assert "--x" in params


def test_get_elevation_launch_args_script_mode(monkeypatch):
    monkeypatch.setattr("shared.elevation.sys.argv", ["main.py", "--demo"])
    monkeypatch.setattr("shared.elevation.sys.executable", "python")
    monkeypatch.setattr("shared.elevation.sys.frozen", False, raising=False)

    executable, params, working_dir = get_elevation_launch_args()
    assert Path(executable).name.lower().startswith("python")
    assert params is not None and "--demo" in params
    assert working_dir


def test_get_elevation_launch_args_exe_mode(monkeypatch):
    monkeypatch.setattr("shared.elevation.sys.argv", ["cleanbox.exe", "--demo"])
    monkeypatch.setattr(
        "shared.elevation._get_current_process_image_path",
        lambda: r"C:\\Program Files\\CleanBox\\cleanbox.exe",
    )
    monkeypatch.setattr("shared.elevation.sys.frozen", False, raising=False)

    executable, params, working_dir = get_elevation_launch_args()
    assert executable.lower().endswith("cleanbox.exe")
    assert params is not None and "--demo" in params
    assert working_dir.lower().endswith("cleanbox")
