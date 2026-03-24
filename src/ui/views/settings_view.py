"""Settings View - Application settings and preferences."""
import logging
from typing import Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel,
    QFrame, QSpinBox, QGroupBox, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from shared.elevation import is_admin
from ui.views.settings_view_styles import (
    build_checkbox_style,
    build_group_box_style,
    build_restart_admin_button_style,
)

logger = logging.getLogger(__name__)
VERSION_FILE = Path(__file__).resolve().parents[3] / "VERSION"


class SettingsView(QWidget):
    """View for application settings."""

    autostart_changed = pyqtSignal(bool)
    restart_as_admin_requested = pyqtSignal()
    threshold_changed = pyqtSignal(int)
    interval_changed = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the settings view."""
        try:
            super().__init__(parent)
            self._setup_ui()
        except Exception as e:
            logger.error("Failed to init SettingsView: %s", e)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(16)

            # Header
            title = QLabel("Settings")
            title_font = QFont()
            title_font.setPointSize(18)
            title_font.setBold(True)
            title.setFont(title_font)
            layout.addWidget(title)

            # Description
            desc = QLabel("Configure application behavior and preferences.")
            desc.setStyleSheet("color: #666666;")
            layout.addWidget(desc)

            # Separator
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setStyleSheet("background-color: #E0E0E0;")
            layout.addWidget(separator)

            # Startup Group
            startup_group = QGroupBox("Startup")
            startup_group.setStyleSheet(build_group_box_style())
            startup_layout = QVBoxLayout(startup_group)
            startup_layout.setSpacing(10)

            self._autostart_cb = QCheckBox("Start CleanBox with Windows")
            self._autostart_cb.setCursor(Qt.CursorShape.PointingHandCursor)
            self._autostart_cb.setChecked(True)
            self._autostart_cb.setStyleSheet(build_checkbox_style())
            self._autostart_cb.stateChanged.connect(self._on_autostart_changed)
            startup_layout.addWidget(self._autostart_cb)

            if not is_admin():
                self._restart_admin_btn = QPushButton("Restart now with admin")
                self._restart_admin_btn.setCursor(
                    Qt.CursorShape.PointingHandCursor)
                self._restart_admin_btn.setMinimumHeight(36)
                self._restart_admin_btn.setStyleSheet(
                    build_restart_admin_button_style())
                self._restart_admin_btn.clicked.connect(
                    self._on_restart_as_admin_requested)
                startup_layout.addWidget(self._restart_admin_btn)
            else:
                self._restart_admin_btn = None

            layout.addWidget(startup_group)

            # Monitoring Group
            monitor_group = QGroupBox("Storage Monitoring")
            monitor_group.setStyleSheet(startup_group.styleSheet())
            monitor_layout = QVBoxLayout(monitor_group)

            # Threshold setting
            threshold_layout = QHBoxLayout()
            threshold_label = QLabel("Low space warning threshold:")
            threshold_layout.addWidget(threshold_label)

            self._threshold_spin = QSpinBox()
            self._threshold_spin.setRange(1, 100)
            self._threshold_spin.setValue(10)
            self._threshold_spin.setSuffix(" GB")
            self._threshold_spin.setMinimumWidth(80)
            self._threshold_spin.valueChanged.connect(self._on_threshold_changed)
            threshold_layout.addWidget(self._threshold_spin)

            threshold_layout.addStretch()
            monitor_layout.addLayout(threshold_layout)

            # Interval setting
            interval_layout = QHBoxLayout()
            interval_label = QLabel("Check storage every:")
            interval_layout.addWidget(interval_label)

            self._interval_spin = QSpinBox()
            self._interval_spin.setRange(10, 600)
            self._interval_spin.setValue(60)
            self._interval_spin.setSuffix(" seconds")
            self._interval_spin.setMinimumWidth(100)
            self._interval_spin.valueChanged.connect(self._on_interval_changed)
            interval_layout.addWidget(self._interval_spin)

            interval_layout.addStretch()
            monitor_layout.addLayout(interval_layout)

            layout.addWidget(monitor_group)

            layout.addStretch()

            # Version info
            version_label = QLabel(f"CleanBox v{self._get_app_version()}")
            version_label.setStyleSheet("color: #666666; font-size: 11px;")
            version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(version_label)
        except Exception as e:
            logger.error("Failed to setup SettingsView UI: %s", e)

    @staticmethod
    def _get_app_version() -> str:
        """Read the application version from the repository VERSION file."""
        try:
            version = VERSION_FILE.read_text(encoding="utf-8").strip()
            return version or "unknown"
        except Exception as e:
            logger.warning("Failed to read app version from %s: %s", VERSION_FILE, e)
            return "unknown"

    def set_autostart(self, enabled: bool) -> None:
        """Set the autostart checkbox state."""
        try:
            self._autostart_cb.blockSignals(True)
            self._autostart_cb.setChecked(enabled)
            self._autostart_cb.blockSignals(False)
        except Exception as e:
            logger.error("Failed to set autostart: %s", e)

    def set_threshold(self, value: int) -> None:
        """Set the threshold spinbox value."""
        try:
            self._threshold_spin.blockSignals(True)
            self._threshold_spin.setValue(value)
            self._threshold_spin.blockSignals(False)
        except Exception as e:
            logger.error("Failed to set threshold: %s", e)

    def set_interval(self, value: int) -> None:
        """Set the interval spinbox value."""
        try:
            self._interval_spin.blockSignals(True)
            self._interval_spin.setValue(value)
            self._interval_spin.blockSignals(False)
        except Exception as e:
            logger.error("Failed to set interval: %s", e)

    def _on_autostart_changed(self, state: int) -> None:
        """Handle autostart checkbox change."""
        try:
            enabled = state == Qt.CheckState.Checked.value
            self.autostart_changed.emit(enabled)
            logger.info("Autostart changed: %s", enabled)
        except Exception as e:
            logger.error("Failed to change autostart: %s", e)

    def _on_restart_as_admin_requested(self) -> None:
        """Handle restart-as-admin button click."""
        try:
            self.restart_as_admin_requested.emit()
            logger.info("Restart as admin requested")
        except Exception as e:
            logger.error("Failed to request restart as admin: %s", e)

    def _on_threshold_changed(self, value: int) -> None:
        """Handle threshold spinbox change."""
        try:
            self.threshold_changed.emit(value)
            logger.info("Threshold changed: %d GB", value)
        except Exception as e:
            logger.error("Failed to change threshold: %s", e)

    def _on_interval_changed(self, value: int) -> None:
        """Handle interval spinbox change."""
        try:
            self.interval_changed.emit(value)
            logger.info("Interval changed: %d seconds", value)
        except Exception as e:
            logger.error("Failed to change interval: %s", e)
