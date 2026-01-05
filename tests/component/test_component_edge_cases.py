"""
Additional Component Tests for CleanBox UI
Tests: Error states, edge cases, accessibility
Target: 2 additional tests to reach 30 component tests
"""
import sys
import os
from unittest.mock import Mock, MagicMock, patch

import pytest
from PyQt6.QtCore import Qt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))


class TestComponentEdgeCases:
    """Component tests for edge cases and error states."""
    
    def test_cleanup_view_empty_state(self, qapp):
        """Test CleanupView displays correctly with no directories."""
        from ui.views import CleanupView
        view = CleanupView()
        view.update_directories([])
        assert view._dir_list.count() == 0
        # Cleanup button should still be clickable
        assert view._cleanup_btn.isEnabled()
    
    def test_storage_view_no_drives(self, qapp):
        """Test StorageView handles zero drives gracefully."""
        from ui.views import StorageView
        view = StorageView()
        view.update_drives([])
        assert view._drive_combo.count() == 0
