"""System tray icon - pystray integration."""
import logging
import threading
from typing import Optional, Callable

from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem, Icon

from shared.constants import APP_NAME, ICON_PATH

logger = logging.getLogger(__name__)


def load_icon() -> Image.Image:
    """Load icon from file or create fallback."""
    if ICON_PATH.exists():
        try:
            return Image.open(ICON_PATH)
        except Exception as e:
            logger.warning("Failed to load icon: %s", e)

    # Fallback: create simple icon
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle([8, 8, 56, 56], fill=(34, 197, 94),
                   outline=(255, 255, 255), width=2)
    return image


class TrayIcon:
    """System tray icon manager."""

    def __init__(
        self,
        on_cleanup: Optional[Callable] = None,
        on_settings: Optional[Callable] = None,
        on_exit: Optional[Callable] = None,
    ):
        """Initialize the tray icon manager."""
        try:
            self._on_cleanup = on_cleanup
            self._on_settings = on_settings
            self._on_exit = on_exit
            self._icon: Optional[Icon] = None
            self._thread: Optional[threading.Thread] = None
        except Exception as e:
            logger.error("Failed to init TrayIcon: %s", e)

    def _create_menu(self) -> pystray.Menu:
        """Create the context menu."""
        try:
            return pystray.Menu(
                MenuItem("Cleanup Now", self._handle_cleanup, default=False),
                MenuItem("Settings", self._handle_settings, default=True),
                pystray.Menu.SEPARATOR,
                MenuItem("Exit", self._handle_exit),
            )
        except Exception as e:
            logger.error("Failed to create tray menu: %s", e)
            return pystray.Menu(MenuItem("Exit", self._handle_exit))

    def _handle_cleanup(self, icon, item) -> None:
        """Handle cleanup menu click."""
        try:
            logger.info("Cleanup requested from tray")
            if self._on_cleanup:
                self._on_cleanup()
        except Exception as e:
            logger.error("Failed to handle cleanup from tray: %s", e)

    def _handle_settings(self, icon, item) -> None:
        """Handle settings menu click."""
        try:
            logger.info("Settings requested from tray")
            if self._on_settings:
                self._on_settings()
        except Exception as e:
            logger.error("Failed to handle settings from tray: %s", e)

    def _handle_exit(self, icon, item) -> None:
        """Handle exit menu click."""
        try:
            logger.info("Exit requested from tray")
            self.stop()
            if self._on_exit:
                self._on_exit()
        except Exception as e:
            logger.error("Failed to handle exit from tray: %s", e)

    def start(self) -> None:
        """Start the tray icon in a separate thread."""
        try:
            image = load_icon()
            menu = self._create_menu()

            self._icon = Icon(
                name=APP_NAME,
                icon=image,
                title=APP_NAME,
                menu=menu,
            )

            # Run in separate thread so it doesn't block
            self._thread = threading.Thread(target=self._icon.run, daemon=True)
            self._thread.start()
            logger.info("Tray icon started")
        except Exception as e:
            logger.error("Failed to start tray icon: %s", e)

    def stop(self) -> None:
        """Stop the tray icon."""
        try:
            if self._icon:
                self._icon.stop()
                logger.info("Tray icon stopped")
        except Exception as e:
            logger.error("Failed to stop tray icon: %s", e)
        finally:
            self._icon = None
            self._thread = None
            logger.debug("Tray icon resources cleaned up")

    def set_status(self, status: Optional[str] = None) -> None:
        """Update tray icon tooltip to show current status.
        
        Args:
            status: Status text to show (e.g., "Cleaning 2/5...").
                    Pass None to reset to default app name.
        """
        try:
            if self._icon:
                if status:
                    self._icon.title = f"{APP_NAME} - {status}"
                else:
                    self._icon.title = APP_NAME
        except Exception as e:
            logger.error("Failed to set tray status: %s", e)
