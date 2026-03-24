"""Tests for SettingsView style helpers."""

from __future__ import annotations


def test_build_group_box_style_contains_section_rules():
    from ui.views.settings_view_styles import build_group_box_style

    style = build_group_box_style()

    assert "QGroupBox" in style
    assert "font-weight: bold;" in style
    assert "border-radius: 6px;" in style
    assert "QGroupBox::title" in style


def test_build_restart_admin_button_style_contains_button_rules():
    from ui.views.settings_view_styles import build_restart_admin_button_style

    style = build_restart_admin_button_style()

    assert "QPushButton" in style
    assert "background-color: #FFFFFF;" in style
    assert "QPushButton:hover" in style
    assert "QPushButton:pressed" in style


def test_build_checkbox_style_includes_check_icon_path():
    from shared.constants import CHECKBOX_CHECK_ICON_PATH
    from ui.views.settings_view_styles import build_checkbox_style

    style = build_checkbox_style()

    assert "QCheckBox::indicator:checked" in style
    assert CHECKBOX_CHECK_ICON_PATH.as_posix() in style
