"""Unit tests for extracted shared helper modules."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from shared.constants_assets import resolve_assets_dir
from shared.execution import retry, safe_execute
from shared.protected_paths import build_protected_path_sets


def test_resolve_assets_dir_script_mode():
    if hasattr(sys, "frozen"):
        delattr(sys, "frozen")
    module_file = r"D:\repo\src\shared\constants.py"
    assert resolve_assets_dir(module_file) == Path(r"D:\repo\src\assets")


def test_resolve_assets_dir_frozen_mode():
    with patch.object(sys, "frozen", True, create=True):
        with patch.object(sys, "_MEIPASS", r"C:\bundle", create=True):
            assert resolve_assets_dir("ignored.py") == Path(r"C:\bundle\assets")


def test_build_protected_path_sets_includes_prefix_for_system_roots():
    fake_env = {
        "WINDIR": r"C:\Windows",
        "SYSTEMDRIVE": "C:",
        "PROGRAMFILES": r"C:\Program Files",
    }
    with patch.dict("os.environ", fake_env, clear=True):
        exact, prefixes = build_protected_path_sets()
    assert r"c:\windows\system32" in exact
    assert r"c:\windows\system32" in prefixes
    assert r"c:\program files" in exact


def test_retry_from_execution_module_retries_then_succeeds():
    state = {"count": 0}

    @retry(max_attempts=2, delay=0, exceptions=(ValueError,))
    def flaky():
        state["count"] += 1
        if state["count"] == 1:
            raise ValueError("boom")
        return "ok"

    assert flaky() == "ok"
    assert state["count"] == 2


def test_safe_execute_from_execution_module_returns_default():
    def explode():
        raise RuntimeError("x")

    assert safe_execute(explode, default=123, log_error=False) == 123


def test_retry_from_execution_module_raises_at_max_attempts():
    @retry(max_attempts=2, delay=0, exceptions=(ValueError,))
    def always_fail():
        raise ValueError("fail")

    with pytest.raises(ValueError):
        always_fail()
