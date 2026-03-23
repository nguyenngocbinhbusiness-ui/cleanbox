"""Unit tests for storage view navigation helpers."""

from features.folder_scanner.service import FolderInfo
from ui.views.storage_view_navigation import (
    navigate_back_state,
    navigate_forward_state,
    resolve_cached_node,
)


def test_navigate_back_state_no_history():
    current, history, forward = navigate_back_state("C:/A", [], [])
    assert current == "C:/A"
    assert history == []
    assert forward == []


def test_navigate_back_state_moves_current_to_forward():
    current, history, forward = navigate_back_state("C:/B", ["C:/A"], [])
    assert current == "C:/A"
    assert history == []
    assert forward == ["C:/B"]


def test_navigate_forward_state_no_forward():
    current, history, forward = navigate_forward_state("C:/A", [], [])
    assert current == "C:/A"
    assert history == []
    assert forward == []


def test_navigate_forward_state_moves_current_to_history():
    current, history, forward = navigate_forward_state("C:/A", [], ["C:/B"])
    assert current == "C:/B"
    assert history == ["C:/A"]
    assert forward == []


def test_resolve_cached_node_prefers_path_index():
    node_a = FolderInfo("C:/A", "A", 1, 1, 1, 1, "", [])
    node_b = FolderInfo("C:/A", "B", 2, 2, 2, 2, "", [])
    resolved = resolve_cached_node("C:/A", {"C:/A": node_a}, {"C:/A": node_b})
    assert resolved is node_a
