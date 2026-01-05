"""Settings View - Application settings and preferences."""
import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel,
    QFrame, QSpinBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class SettingsView(QWidget):
    """View for application settings."""

    autostart_changed = pyqtSignal(bool)
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
            startup_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #E0E0E0;
                    border-radius: 6px;
                    margin-top: 12px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px;
                }
            """)
            startup_layout = QVBoxLayout(startup_group)

            self._autostart_cb = QCheckBox("Start CleanBox with Windows")
            self._autostart_cb.setCursor(Qt.CursorShape.PointingHandCursor)
            self._autostart_cb.stateChanged.connect(self._on_autostart_changed)
            startup_layout.addWidget(self._autostart_cb)

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
            version_label = QLabel("CleanBox v1.0.0")
            version_label.setStyleSheet("color: #666666; font-size: 11px;")
            version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(version_label)
        except Exception as e:
            logger.error("Failed to setup SettingsView UI: %s", e)

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
