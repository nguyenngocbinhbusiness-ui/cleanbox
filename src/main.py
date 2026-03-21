"""CleanBox - Main entry point."""
import ctypes
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports - MUST be before local imports
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from shared.constants import APP_NAME, CONFIG_DIR


def should_request_admin() -> bool:
    """Check persisted setting for whether startup should request admin."""
    try:
        from shared.config import ConfigManager
        return ConfigManager().run_as_admin_enabled
    except Exception:
        return True


def is_admin() -> bool:
    """Check if the current process has administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def run_as_admin() -> bool:
    """Re-launch the current process with administrator privileges.

    Returns True if elevation was requested (caller should exit),
    False if elevation failed or was declined by the user.
    """
    try:
        if getattr(sys, "frozen", False):
            # Packaged exe
            executable = sys.executable
            params = " ".join(sys.argv[1:])
        else:
            # Running from source
            executable = sys.executable
            params = f'"{os.path.abspath(sys.argv[0])}"'
            if len(sys.argv) > 1:
                params += " " + " ".join(sys.argv[1:])

        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", executable, params, None, 1
        )
        # ShellExecuteW returns > 32 on success
        return ret > 32
    except Exception:
        return False


def setup_logging() -> None:
    """Set up logging configuration."""
    try:
        log_file = CONFIG_DIR / "cleanbox.log"
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        handlers = [logging.FileHandler(log_file, encoding="utf-8")]
        # Only add console handler when running from source (not packaged)
        if not getattr(sys, "frozen", False):
            handlers.append(logging.StreamHandler())

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=handlers,
        )
    except Exception as e:
        print(f"Failed to setup logging: {e}")
        # Fallback to basic logging to stderr
        logging.basicConfig(level=logging.INFO, stream=sys.stderr)


def main() -> int:
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    # Request admin privileges if configured and not already elevated
    if should_request_admin() and not is_admin():
        logger.info("Not running as admin, requesting elevation...")
        if run_as_admin():
            logger.info("Elevation requested, exiting current process")
            return 0
        else:
            logger.warning("Admin elevation failed or declined, continuing without admin")

    try:
        logger.info("=" * 50)
        logger.info("Starting %s (admin=%s)", APP_NAME, is_admin())
        logger.info("=" * 50)

        from app import App
        app = App()
        return app.start()

    except Exception as e:
        logger.exception("Fatal error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
