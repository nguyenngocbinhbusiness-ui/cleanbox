import logging

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QSplitter,
    QStackedWidget,
    QVBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

from ui.components.sidebar import SidebarWidget
from ui.views import StorageView, CleanupView, SettingsView
from shared.constants import ICON_PATH

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main Application Window.
    Implements the 'Sidebar + Content' Split View architecture.
    """
    # Signals for external connections
    directory_added = pyqtSignal(str)
    directory_removed = pyqtSignal(str)
    autostart_changed = pyqtSignal(bool)
    cleanup_requested = pyqtSignal()
    refresh_storage = pyqtSignal()

    def __init__(self):
        """Initialize the main window and UI components."""
        try:
            super().__init__()
            self.setWindowTitle("CleanBox Professional")
            self.resize(1000, 700)

            # Set window icon
            if ICON_PATH.exists():
                self.setWindowIcon(QIcon(str(ICON_PATH)))

            # Central Widget & Main Layout
            self.central_widget = QWidget()
            self.setCentralWidget(self.central_widget)
            self.main_layout = QVBoxLayout(self.central_widget)
            self.main_layout.setContentsMargins(0, 0, 0, 0)
            self.main_layout.setSpacing(0)

            # Global stylesheet - Dark text on light background
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #FFFFFF;
                    color: #1A1A1A;
                }
                QLabel {
                    color: #1A1A1A;
                }
                QPushButton {
                    color: #1A1A1A;
                    background-color: #F0F0F0;
                    border: 1px solid #D0D0D0;
                    border-radius: 4px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #E5E5E5;
                }
                QListWidget, QTableWidget {
                    color: #1A1A1A;
                    background-color: #FFFFFF;
                }
                QHeaderView::section {
                    color: #1A1A1A;
                }
                QCheckBox, QSpinBox {
                    color: #1A1A1A;
                }
                QGroupBox {
                    color: #1A1A1A;
                }
                QGroupBox::title {
                    color: #1A1A1A;
                }
            """)

            # 1. Main Splitter (Left: Sidebar, Right: Content)
            self.splitter = QSplitter(Qt.Orientation.Horizontal)
            self.splitter.setHandleWidth(1)  # Thin separator
            self.splitter.setStyleSheet(
                "QSplitter::handle { background-color: #E0E0E0; }")

            self.main_layout.addWidget(self.splitter)

            # 2. Sidebar Setup
            self.sidebar = SidebarWidget()
            self._setup_sidebar_items()
            self.splitter.addWidget(self.sidebar)

            # 3. Content Area Setup
            self.content_stack = QStackedWidget()
            self.content_stack.setStyleSheet("background-color: #FFFFFF;")
            self.splitter.addWidget(self.content_stack)

            # Set Initial Sizes (Sidebar approx 220px, rest for Content)
            self.splitter.setSizes([220, 780])
            # Don't collapse sidebar completely
            self.splitter.setCollapsible(0, False)

            # 4. Connect Signals
            self.sidebar.selection_changed.connect(self.switch_view)

            # 5. Initialize Views
            self._init_views()

            # Default Selection
            self.sidebar.select_item("drives")
        except Exception as e:
            logger.error("Failed to init MainWindow: %s", e)

    def _setup_sidebar_items(self):
        """Define the navigation structure."""
        try:
            # Text-only navigation per UI standards
            self.sidebar.add_item("Drives", "drives")
            self.sidebar.add_item("Cleanup", "cleanup")
            self.sidebar.add_item("Settings", "settings")
        except Exception as e:
            logger.error("Failed to setup sidebar items: %s", e)

    def _init_views(self):
        """Initialize and connect all views."""
        try:
            self.views = {}

            # Storage View
            self.storage_view = StorageView()
            self.storage_view.refresh_requested.connect(
                self.refresh_storage.emit)
            self.views["drives"] = self.storage_view

            # Cleanup View
            self.cleanup_view = CleanupView()
            self.cleanup_view.directory_added.connect(
                self.directory_added.emit)
            self.cleanup_view.directory_removed.connect(
                self.directory_removed.emit)
            self.cleanup_view.cleanup_requested.connect(
                self.cleanup_requested.emit)
            self.views["cleanup"] = self.cleanup_view

            # Settings View
            self.settings_view = SettingsView()
            self.settings_view.autostart_changed.connect(
                self.autostart_changed.emit)
            self.views["settings"] = self.settings_view

            for view in self.views.values():
                self.content_stack.addWidget(view)
        except Exception as e:
            logger.error("Failed to initialize views: %s", e)

    def switch_view(self, view_id: str):
        """Switch the stacked widget to the requested view."""
        try:
            if view_id in self.views:
                self.content_stack.setCurrentWidget(self.views[view_id])
        except Exception as e:
            logger.error("Failed to switch view: %s", e)

    def update_drives(self, drives):
        """Update storage view with drive information."""
        try:
            self.storage_view.update_drives(drives)
        except Exception as e:
            logger.error("Failed to update drives: %s", e)

    def update_directories(self, directories):
        """Update cleanup view with directory list."""
        try:
            self.cleanup_view.update_directories(directories)
        except Exception as e:
            logger.error("Failed to update directories: %s", e)

    def set_autostart(self, enabled: bool):
        """Set autostart checkbox state in settings view."""
        try:
            self.settings_view.set_autostart(enabled)
        except Exception as e:
            logger.error("Failed to set autostart: %s", e)

    def set_threshold(self, value: int):
        """Set threshold value in settings view."""
        try:
            self.settings_view.set_threshold(value)
        except Exception as e:
            logger.error("Failed to set threshold: %s", e)

    def set_interval(self, value: int):
        """Set interval value in settings view."""
        try:
            self.settings_view.set_interval(value)
        except Exception as e:
            logger.error("Failed to set interval: %s", e)

    def show_cleanup_progress(self, visible: bool) -> None:
        """Show or hide cleanup progress bar.
        
        Args:
            visible: True to show progress bar, False to hide.
        """
        try:
            self.cleanup_view.show_progress_bar(visible)
        except Exception as e:
            logger.error("Failed to show cleanup progress: %s", e)

    def set_cleanup_progress(self, current: int, total: int) -> None:
        """Update cleanup progress bar value.
        
        Args:
            current: Current progress (0 to total).
            total: Total number of items.
        """
        try:
            self.cleanup_view.set_progress(current, total)
        except Exception as e:
            logger.error("Failed to set cleanup progress: %s", e)

    def closeEvent(self, event) -> None:
        """Handle window close - hide instead of close."""
        try:
            event.ignore()
            self.hide()
        except Exception as e:
            logger.error("Failed to handle close event: %s", e)

