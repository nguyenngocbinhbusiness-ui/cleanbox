"""Windows Registry operations for auto-start."""
import logging
import os
import sys
from pathlib import Path
from subprocess import CalledProcessError, list2cmdline, run
try:
    import winreg
except ImportError:
    winreg = None

from shared.constants import APP_NAME, REGISTRY_KEY
from shared.registry_tasks import build_create_task_command, build_delete_task_command

logger = logging.getLogger(__name__)
IS_WINDOWS = sys.platform == "win32"


def _get_system_tool_path(tool_name: str) -> str:
    """Return a fully-qualified Windows system tool path when available."""
    if not IS_WINDOWS:
        return tool_name

    system_root = os.environ.get("SystemRoot") or os.environ.get("WINDIR") or r"C:\Windows"
    return str(Path(system_root) / "System32" / tool_name)


def get_executable_path() -> str:
    """Get the path to the main script or executable."""
    try:
        executable = os.path.abspath(sys.executable)
        if getattr(sys, "frozen", False):
            return list2cmdline([executable])

        script_path = os.path.abspath(sys.argv[0]) if sys.argv else ""
        if script_path and os.path.normcase(script_path) != os.path.normcase(executable):
            return list2cmdline([executable, script_path])
        return list2cmdline([executable])
    except Exception as e:
        logger.error("Failed to get executable path: %s", e)
        return list2cmdline([sys.executable])


def _create_scheduled_task() -> bool:
    """Fallback: create a logon-trigger scheduled task via schtasks."""
    exe_path = get_executable_path()
    cmd = build_create_task_command(_get_system_tool_path("schtasks.exe"), exe_path)
    try:
        run(cmd, check=True, capture_output=True, text=True, shell=False)
        logger.info("Auto-start enabled via Task Scheduler (fallback)")
        return True
    except (CalledProcessError, OSError) as e:
        logger.error("Task Scheduler fallback also failed: %s", e)
        return False


def _delete_scheduled_task() -> bool:
    """Remove the fallback scheduled task if it exists."""
    cmd = build_delete_task_command(_get_system_tool_path("schtasks.exe"))
    try:
        run(cmd, check=True, capture_output=True, text=True, shell=False)
        logger.info("Scheduled task '%s' removed", APP_NAME)
        return True
    except (CalledProcessError, OSError) as e:
        logger.warning("Could not remove scheduled task (may not exist): %s", e)
        return False


def enable_autostart() -> bool:
    """Add CleanBox to Windows startup."""
    if winreg is None:
        logger.warning("Registry not supported, trying Task Scheduler")
        return _create_scheduled_task()
    key = None
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_KEY,
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(
            key,
            APP_NAME,
            0,
            winreg.REG_SZ,
            get_executable_path())
        logger.info("Auto-start enabled in registry")
        return True
    except (PermissionError, OSError) as e:
        logger.warning("Registry write blocked: %s. Falling back to Task Scheduler.", e)
        return _create_scheduled_task()
    finally:
        if key:
            winreg.CloseKey(key)


def disable_autostart() -> bool:
    """Remove CleanBox from Windows startup."""
    registry_ok = True
    if winreg is not None:
        key = None
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                REGISTRY_KEY,
                0,
                winreg.KEY_SET_VALUE,
            )
            winreg.DeleteValue(key, APP_NAME)
            logger.info("Auto-start disabled in registry")
        except FileNotFoundError:
            logger.info("Auto-start was not enabled in registry")
        except (PermissionError, OSError) as e:
            logger.error("Failed to disable auto-start in registry: %s", e)
            registry_ok = False
        finally:
            if key:
                winreg.CloseKey(key)
    # Always attempt to clean up the scheduled task fallback
    _delete_scheduled_task()
    return registry_ok


def is_autostart_enabled() -> bool:
    """Check if auto-start is currently enabled."""
    if winreg is None:
        return False
    key = None
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_KEY,
            0,
            winreg.KEY_READ,
        )
        winreg.QueryValueEx(key, APP_NAME)
        return True
    except FileNotFoundError:
        return False
    except WindowsError:
        return False
    finally:
        if key:
            winreg.CloseKey(key)
