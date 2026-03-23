"""Unit tests for shared.registry_tasks helpers."""

from shared.constants import APP_NAME
from shared.registry_tasks import build_create_task_command, build_delete_task_command


def test_build_create_task_command():
    cmd = build_create_task_command(r"C:\Windows\System32\schtasks.exe", "python app.py")
    assert cmd[0].lower().endswith("schtasks.exe")
    assert "/create" in cmd
    assert APP_NAME in cmd
    assert "/tr" in cmd
    assert "python app.py" in cmd


def test_build_delete_task_command():
    cmd = build_delete_task_command(r"C:\Windows\System32\schtasks.exe")
    assert cmd[0].lower().endswith("schtasks.exe")
    assert "/delete" in cmd
    assert APP_NAME in cmd
