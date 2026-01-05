import logging

from PyQt6.QtWidgets import (
    QVBoxLayout, QPushButton, QButtonGroup, QFrame
)
from PyQt6.QtCore import pyqtSignal, QSize, Qt

logger = logging.getLogger(__name__)


class SidebarButton(QPushButton):
    """Custom button for sidebar with specific styling."""

    def __init__(self, text, icon_name=None, parent=None):
        try:
            super().__init__(text, parent)
            self.setCheckable(True)
            self.setMinimumHeight(40)
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setIconSize(QSize(20, 20))
            # Icon handling would go here (using easy-to-access standard icons or
            # resources)

            # Stylesheet for this specific button type to match "TreeSize" look
            self.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding-left: 15px;
                    background-color: transparent;
                    border: none;
                    border-left: 4px solid transparent;
                    color: #1A1A1A;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #E6F2FF;
                    color: #1A1A1A;
                }
                QPushButton:checked {
                    background-color: #CEE7FF;
                    border-left: 4px solid #0078D4; /* Windows Blue Accent */
                    color: #000000;
                    font-weight: bold;
                }
            """)
        except Exception as e:
            logger.error("Failed to init SidebarButton: %s", e)


class SidebarWidget(QFrame):
    """
    Vertical navigation sidebar matching the reference image style.
    Emits `selection_changed(str)` with the ID of the selected item.
    """
    selection_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        """Initialize the sidebar widget."""
        try:
            super().__init__(parent)
            self.setObjectName("Sidebar")
            self.setStyleSheet(
                "QFrame#Sidebar { background-color: #F8F9FA; border-right: 1px solid #E0E0E0; }")

            self.layout = QVBoxLayout(self)
            self.layout.setContentsMargins(0, 10, 0, 10)
            self.layout.setSpacing(2)

            self.button_group = QButtonGroup(self)
            self.button_group.setExclusive(True)
            self.button_group.buttonClicked.connect(self._on_button_clicked)

            self.buttons = {}

            # Add spacer at bottom to push items up
            self.layout.addStretch()
        except Exception as e:
            logger.error("Failed to init SidebarWidget: %s", e)

    def add_item(self, text: str, id: str, icon=None):
        """Add a navigation item to the sidebar."""
        try:
            # Insert before the stretch (which is the last item)
            btn = SidebarButton(text)

            # Temporarily use QStyle standard icons if no icon provided
            if icon:
                btn.setIcon(icon)

            self.layout.insertWidget(self.layout.count() - 1, btn)
            self.button_group.addButton(btn)

            # Store mapping if needed, or stick to direct button access
            self.buttons[id] = btn

            # Mapping button -> ID for signal emission (using property or
            # parallel dict)
            btn.setProperty("nav_id", id)
        except Exception as e:
            logger.error("Failed to add sidebar item: %s", e)

    def _on_button_clicked(self, btn):
        """Handle sidebar button click."""
        try:
            nav_id = btn.property("nav_id")
            if nav_id:
                self.selection_changed.emit(nav_id)
        except Exception as e:
            logger.error("Failed to handle button click: %s", e)

    def select_item(self, id: str):
        """Programmatically select an item."""
        try:
            if id in self.buttons:
                self.buttons[id].setChecked(True)
                self.selection_changed.emit(id)
        except Exception as e:
            logger.error("Failed to select item: %s", e)
