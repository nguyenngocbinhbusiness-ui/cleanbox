"""CleanBox Application Orchestrator."""
import atexit
import logging
import sys
import time
from typing import Optional

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from app_cleanup import do_cleanup, on_cleanup_finished, on_cleanup_progress
from app_single_instance import acquire_single_instance
from shared.config import ConfigManager
from shared.constants import APP_NAME
from shared.elevation import request_admin_restart
from shared import registry
from features.cleanup import CleanupService, CleanupProgressWorker, get_default_directories
from features.storage_monitor import StorageMonitor, DriveInfo
from features.notifications import NotificationService
# from features.settings import SettingsWindow # Repaced by MainWindow
from ui.main_window import MainWindow
from ui.tray_icon import TrayIcon

logger = logging.getLogger(__name__)

# Single instance server name
SINGLE_INSTANCE_KEY = "CleanBox_SingleInstance_Lock"


class App(QObject):
    """Main application orchestrator."""

    # Signals for thread-safe UI operations (pystray runs in different thread)
    _show_settings_signal = pyqtSignal()
    _cleanup_signal = pyqtSignal()
    _exit_signal = pyqtSignal()

    def __init__(self):
        """Initialize the application components."""
        try:
            super().__init__()

            # Connect signals to slots (for thread-safe calls from pystray)
            self._show_settings_signal.connect(self._do_show_settings)
            self._cleanup_signal.connect(self._do_cleanup)
            self._exit_signal.connect(self._do_exit)

            # Initialize services
            self._config = ConfigManager()
            self._cleanup_service = CleanupService()
            self._notification_service = NotificationService()
            self._storage_monitor: Optional[StorageMonitor] = None
            self._main_window: Optional[MainWindow] = None
            self._tray_icon: Optional[TrayIcon] = None
            self._qt_app: Optional[QApplication] = None
            self._cleanup_worker: Optional[CleanupProgressWorker] = None
            self._startup_error: Optional[str] = None
        except Exception as e:
            logger.error("Failed to init App: %s", e)

    def start(self) -> int:
        """Start the application."""
        logger.info("Starting %s", APP_NAME)

        # Register cleanup handler for graceful shutdown
        atexit.register(self._cleanup_on_exit)

        try:
            # Create Qt application
            self._qt_app = QApplication(sys.argv)
            self._qt_app.setQuitOnLastWindowClosed(
                False)  # Keep running in tray

            # Check for existing instance
            if not self._acquire_single_instance():
                logger.warning("Another instance is already running")
                return 1 if self._startup_error else 0

            # Handle first run - detect default directories
            if self._config.is_first_run:
                self._handle_first_run()

            # Set up auto-start if enabled
            if self._config.auto_start_enabled:
                registry.enable_autostart()

            # Initialize storage monitor
            self._storage_monitor = StorageMonitor(
                threshold_gb=self._config.threshold_gb,
                interval_seconds=self._config.polling_interval,
            )
            self._storage_monitor.set_notified_drives(
                self._config.get_notified_drive_timestamps())
            self._storage_monitor.low_space_detected.connect(
                self._on_low_space)
            self._storage_monitor.low_space_cleared.connect(
                self._on_low_space_cleared)
            self._storage_monitor.start()

            # Initialize Main Window and show on startup
            self._main_window = MainWindow()
            self._main_window.show()  # Show UI on startup

            # Connect MainWindow signals to App handlers
            self._main_window.directory_added.connect(self._on_directory_added)
            self._main_window.directory_removed.connect(
                self._on_directory_removed)
            self._main_window.autostart_changed.connect(
                self._on_autostart_changed)
            self._main_window.threshold_changed.connect(
                self._on_threshold_changed)
            self._main_window.interval_changed.connect(
                self._on_interval_changed)
            self._main_window.restart_as_admin_requested.connect(
                self._restart_with_admin)
            self._main_window.cleanup_requested.connect(self._do_cleanup)
            self._main_window.refresh_storage.connect(
                self._refresh_storage_data)

            # Initialize views with current data
            self._main_window.update_directories(
                self._config.cleanup_directories)
            self._main_window.set_autostart(self._config.auto_start_enabled)
            self._main_window.set_threshold(self._config.threshold_gb)
            self._main_window.set_interval(self._config.polling_interval)

            # Get initial drive data
            self._refresh_storage_data()

            # Initialize tray icon (use signal emitters for thread-safe calls)
            self._tray_icon = TrayIcon(
                on_cleanup=self._emit_cleanup,
                on_settings=self._emit_show_settings,
                on_exit=self._emit_exit,
            )
            self._tray_icon.start()

            # Give notification service access to tray icon for fallback
            if self._tray_icon._icon is not None:
                self._notification_service.set_tray_icon(self._tray_icon._icon)

            logger.info("%s started successfully", APP_NAME)

            # Run Qt event loop
            return self._qt_app.exec()

        except Exception as e:
            logger.exception("Failed to start application: %s", e)
            self._cleanup_on_exit()
            return 1

    def _acquire_single_instance(self) -> bool:
        """Check if this is the only instance running.

        Uses QLocalServer to ensure only one instance runs at a time.
        If another instance exists, sends a 'show' command to it.
        Detects and removes stale locks left by crashed instances (R-008, FM-CB-012).
        Returns True if this is the first instance, False otherwise.
        """
        return acquire_single_instance(
            app=self,
            single_instance_key=SINGLE_INSTANCE_KEY,
            logger=logger,
            socket_cls=QLocalSocket,
            server_cls=QLocalServer,
        )

    def _handle_new_connection(self) -> None:
        """Handle incoming connection from another instance."""
        try:
            socket = self._local_server.nextPendingConnection()
            if socket:
                socket.waitForReadyRead(1000)
                data = socket.readAll().data().decode()
                socket.close()

                if data == "show":
                    logger.info("Received 'show' command from another instance")
                    self._do_show_settings()  # Show the main window
        except Exception as e:
            logger.error("Failed to handle new connection: %s", e)

    def _cleanup_on_exit(self) -> None:
        """Cleanup resources on exit (called by atexit)."""
        logger.info("Cleaning up resources...")
        try:
            if hasattr(self, '_local_server') and self._local_server:
                self._local_server.close()
            if self._storage_monitor:
                self._storage_monitor.stop()
            if self._tray_icon:
                self._tray_icon.stop()
        except Exception as e:
            logger.warning("Error during cleanup: %s", e)

    def _handle_first_run(self) -> None:
        """Handle first run setup."""
        try:
            logger.info("First run detected, setting up defaults")

            # Detect and add default directories
            default_dirs = get_default_directories()
            for directory in default_dirs:
                self._config.add_directory(directory)

            # Mark first run complete
            self._config.mark_first_run_complete()
            logger.info("First run setup complete")
        except Exception as e:
            logger.error("Failed to handle first run: %s", e)

    @pyqtSlot(DriveInfo)
    def _on_low_space(self, drive: DriveInfo) -> None:
        """Handle low space detection."""
        try:
            self._notification_service.notify_low_space(
                drive.letter, drive.free_gb)
            self._config.add_notified_drive(drive.letter, time.time())
        except Exception as e:
            logger.error("Failed to handle low space: %s", e)

    @pyqtSlot(str)
    def _on_low_space_cleared(self, drive_letter: str) -> None:
        """Handle low space recovery and clear persisted notification state."""
        try:
            self._config.remove_notified_drive(drive_letter)
        except Exception as e:
            logger.error("Failed to handle low space recovery for %s: %s", drive_letter, e)

    # Signal emitters (called from pystray thread)
    def _emit_cleanup(self) -> None:
        """Emit cleanup signal (thread-safe)."""
        try:
            self._cleanup_signal.emit()
        except Exception as e:
            logger.error("Failed to emit cleanup signal: %s", e)

    def _emit_show_settings(self) -> None:
        """Emit show settings signal (thread-safe)."""
        try:
            self._show_settings_signal.emit()
        except Exception as e:
            logger.error("Failed to emit show settings signal: %s", e)

    def _emit_exit(self) -> None:
        """Emit exit signal (thread-safe)."""
        try:
            self._exit_signal.emit()
        except Exception as e:
            logger.error("Failed to emit exit signal: %s", e)

    @pyqtSlot()
    def _do_cleanup(self) -> None:
        """Handle cleanup request using background worker."""
        do_cleanup(self, QMessageBox, CleanupProgressWorker, logger)

    @pyqtSlot(int, int)
    def _on_cleanup_progress(self, current: int, total: int) -> None:
        """Handle cleanup progress update from worker."""
        on_cleanup_progress(self, current, total, logger)

    @pyqtSlot(object)
    def _on_cleanup_finished(self, result) -> None:
        """Handle cleanup completion from worker."""
        on_cleanup_finished(self, result, logger)

    @pyqtSlot()
    def _do_show_settings(self) -> None:
        """Show the main window (formerly settings)."""
        try:
            if self._main_window:
                self._main_window.show()
                self._main_window.raise_()
                self._main_window.activateWindow()
        except Exception as e:
            logger.error("Failed to show settings: %s", e)

    @pyqtSlot()
    def _do_exit(self) -> None:
        """Handle exit request."""
        try:
            logger.info("Exiting %s", APP_NAME)
            if self._storage_monitor:
                self._storage_monitor.stop()
            if self._tray_icon:
                self._tray_icon.stop()
            if self._qt_app:
                self._qt_app.quit()
        except Exception as e:
            logger.error("Failed to exit properly: %s", e)

    @pyqtSlot(str)
    def _on_directory_added(self, path: str) -> None:
        """Handle directory added."""
        try:
            self._config.add_directory(path)
        except Exception as e:
            logger.error("Failed to add directory %s: %s", path, e)

    @pyqtSlot(str)
    def _on_directory_removed(self, path: str) -> None:
        """Handle directory removed."""
        try:
            self._config.remove_directory(path)
        except Exception as e:
            logger.error("Failed to remove directory %s: %s", path, e)

    @pyqtSlot(bool)
    def _on_autostart_changed(self, enabled: bool) -> None:
        """Handle auto-start toggle."""
        try:
            self._config.auto_start_enabled = enabled
            if enabled:
                registry.enable_autostart()
            else:
                registry.disable_autostart()
        except Exception as e:
            logger.error("Failed to change autostart to %s: %s", enabled, e)

    @pyqtSlot(int)
    def _on_threshold_changed(self, value: int) -> None:
        """Handle low-space threshold updates from settings."""
        try:
            self._config.threshold_gb = value
            if self._storage_monitor:
                self._storage_monitor.update_threshold(value)
        except Exception as e:
            logger.error("Failed to change threshold to %s: %s", value, e)

    @pyqtSlot(int)
    def _on_interval_changed(self, value: int) -> None:
        """Handle polling interval updates from settings."""
        try:
            self._config.polling_interval = value
            if self._storage_monitor:
                self._storage_monitor.update_interval(value)
        except Exception as e:
            logger.error("Failed to change polling interval to %s: %s", value, e)

    @pyqtSlot()
    def _restart_with_admin(self) -> None:
        """Restart the app and request admin rights for the new process."""
        try:
            ret = request_admin_restart()
            if ret <= 32:
                QMessageBox.warning(
                    self._main_window,
                    "Restart Failed",
                    (
                        "Could not restart CleanBox with administrator rights. "
                        f"Windows error code: {ret}."
                    ),
                )
                return

            logger.info("Restarted CleanBox with admin request")
            self._do_exit()
        except Exception as e:
            logger.error("Failed to restart with admin: %s", e)
            QMessageBox.warning(
                self._main_window,
                "Restart Failed",
                f"Could not restart CleanBox with administrator rights: {e}",
            )

    @pyqtSlot()
    def _refresh_storage_data(self) -> None:
        """Refresh storage data and update UI."""
        try:
            if self._storage_monitor and self._main_window:
                drives = self._storage_monitor.get_all_drives()
                self._main_window.update_drives(drives)
                logger.info("Storage data refreshed")
        except Exception as e:
            logger.error("Failed to refresh storage data: %s", e)
