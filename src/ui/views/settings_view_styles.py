"""Style helpers for SettingsView."""

from __future__ import annotations

from shared.constants import CHECKBOX_CHECK_ICON_PATH


def build_group_box_style() -> str:
    """Return the shared group-box style used by settings sections."""
    return """
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
    """


def build_restart_admin_button_style() -> str:
    """Return the style used by the admin restart button."""
    return """
        QPushButton {
            background-color: #FFFFFF;
            color: #0F172A;
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            padding: 8px 14px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #F8FAFC;
            border-color: #94A3B8;
        }
        QPushButton:pressed {
            background-color: #EEF2F7;
        }
    """


def build_checkbox_style() -> str:
    """Return the shared settings checkbox style."""
    icon_path = CHECKBOX_CHECK_ICON_PATH.as_posix()
    return f"""
        QCheckBox {{
            color: #1A1A1A;
            font-size: 14px;
            font-weight: 400;
            spacing: 12px;
            padding: 4px 0;
            background: transparent;
            border: none;
        }}
        QCheckBox::indicator {{
            width: 24px;
            height: 24px;
            background-color: #FFFFFF;
            border: 3px solid #3A3A3A;
            border-radius: 0;
        }}
        QCheckBox::indicator:hover {{
            border-color: #2F2F2F;
        }}
        QCheckBox::indicator:checked {{
            image: url({icon_path});
            background-color: #FFFFFF;
            border: 3px solid #3A3A3A;
        }}
    """
