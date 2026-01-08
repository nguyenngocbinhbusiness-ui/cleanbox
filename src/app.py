"""CleanBox Application Orchestrator."""
import atexit
import logging
import sys
import tempfile
import os
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from shared.config import ConfigManager
from shared.constants import APP_NAME
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
                return 0

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
                self._config.get_notified_drives())
            self._storage_monitor.low_space_detected.connect(
                self._on_low_space)
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
        Returns True if this is the first instance, False otherwise.
        """
        try:
            # Try to connect to existing server
            socket = QLocalSocket()
            socket.connectToServer(SINGLE_INSTANCE_KEY)
            
            if socket.waitForConnected(500):
                # Another instance is running - send 'show' command
                socket.write(b"show")
                socket.waitForBytesWritten(1000)
                socket.close()
                logger.info("Sent 'show' command to existing instance")
                return False
            
            # No other instance - create server
            self._local_server = QLocalServer()
            # Remove stale socket if exists
            QLocalServer.removeServer(SINGLE_INSTANCE_KEY)
            
            if self._local_server.listen(SINGLE_INSTANCE_KEY):
                logger.info("Single instance lock acquired")
                # Connect to handle incoming connections
                self._local_server.newConnection.connect(self._handle_new_connection)
                return True
            else:
                logger.error("Failed to create local server: %s", 
                           self._local_server.errorString())
                return True  # Allow running anyway
                
        except Exception as e:
            logger.error("Single instance check failed: %s", e)
            return True  # Allow running on error

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
            self._config.add_notified_drive(drive.letter)
        except Exception as e:
            logger.error("Failed to handle low space: %s", e)

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
        try:
            # Prevent multiple simultaneous cleanups
            if self._cleanup_worker is not None and self._cleanup_worker.isRunning():
                logger.warning("Cleanup already in progress")
                return
            
            directories = self._config.cleanup_directories
            if not directories:
                logger.info("No directories to clean")
                return
            
            logger.info("Starting cleanup with %d directories", len(directories))
            
            # Show progress UI
            if self._main_window:
                self._main_window.show_cleanup_progress(True)
            if self._tray_icon:
                self._tray_icon.set_status("Starting cleanup...")
            
            # Create and start worker
            self._cleanup_worker = CleanupProgressWorker(
                directories, parent=self
            )
            self._cleanup_worker.progress_updated.connect(self._on_cleanup_progress)
            self._cleanup_worker.cleanup_finished.connect(self._on_cleanup_finished)
            self._cleanup_worker.start()
            
        except Exception as e:
            logger.error("Failed to start cleanup: %s", e)
            # Reset UI on error
            if self._main_window:
                self._main_window.show_cleanup_progress(False)
            if self._tray_icon:
                self._tray_icon.set_status(None)

    @pyqtSlot(int, int)
    def _on_cleanup_progress(self, current: int, total: int) -> None:
        """Handle cleanup progress update from worker."""
        try:
            if self._main_window:
                self._main_window.set_cleanup_progress(current, total)
            if self._tray_icon:
                self._tray_icon.set_status(f"Cleaning {current}/{total}...")
        except Exception as e:
            logger.error("Failed to update cleanup progress: %s", e)

    @pyqtSlot(object)
    def _on_cleanup_finished(self, result) -> None:
        """Handle cleanup completion from worker."""
        try:
            logger.info("Cleanup finished: %d files, %d folders, %.2f MB",
                       result.total_files, result.total_folders, result.total_size_mb)
            
            # Hide progress UI
            if self._main_window:
                self._main_window.show_cleanup_progress(False)
            if self._tray_icon:
                self._tray_icon.set_status(None)
            
            # Show result notification
            self._notification_service.notify_cleanup_result(
                files_deleted=result.total_files,
                folders_deleted=result.total_folders,
                size_mb=result.total_size_mb,
                errors=len(result.errors),
            )
            
            # Cleanup worker reference
            self._cleanup_worker = None
            
        except Exception as e:
            logger.error("Failed to handle cleanup completion: %s", e)

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
