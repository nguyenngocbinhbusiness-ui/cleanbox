"""Windows Registry operations for auto-start."""
import logging
import sys
try:
    import winreg
except ImportError:
    winreg = None

from shared.constants import APP_NAME, REGISTRY_KEY

logger = logging.getLogger(__name__)
IS_WINDOWS = sys.platform == "win32"


def get_executable_path() -> str:
    """Get the path to the main script or executable.

    When running as a frozen PyInstaller executable, returns the exe path
    directly.  When running as a plain Python script, substitutes pythonw.exe
    for python.exe so that no console window is created on startup.
    """
    try:
        if getattr(sys, 'frozen', False):
            # Running as a compiled executable (PyInstaller) – use it directly.
            return f'"{sys.executable}"'
        # Running as a script – prefer pythonw.exe to suppress console window.
        import os
        python_exe = sys.executable
        if os.path.basename(python_exe).lower() == 'python.exe':
            python_exe = os.path.join(os.path.dirname(python_exe), 'pythonw.exe')
        return f'"{python_exe}" "{sys.argv[0]}"'
    except Exception as e:
        logger.error("Failed to get executable path: %s", e)
        return sys.executable


def enable_autostart() -> bool:
    """Add CleanBox to Windows startup."""
    if winreg is None:
        logger.warning("Registry not supported")
        return False
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
    except WindowsError as e:
        logger.error("Failed to enable auto-start: %s", e)
        return False
    finally:
        if key:
            winreg.CloseKey(key)


def disable_autostart() -> bool:
    """Remove CleanBox from Windows startup."""
    if winreg is None:
        return True
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
        return True
    except FileNotFoundError:
        logger.info("Auto-start was not enabled")
        return True
    except WindowsError as e:
        logger.error("Failed to disable auto-start: %s", e)
        return False
    finally:
        if key:
            winreg.CloseKey(key)


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
