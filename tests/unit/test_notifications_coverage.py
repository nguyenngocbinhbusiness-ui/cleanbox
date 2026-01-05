"""Tests for NotificationService coverage - targeting exception paths."""
import pytest
from unittest.mock import patch, MagicMock
import sys


class TestNotificationServiceCoverage:
    """Tests for NotificationService exception paths."""

    def test_notify_low_space_success(self):
        """Test notify_low_space normal operation."""
        from features.notifications.service import NotificationService
        service = NotificationService()
        
        with patch.object(service, '_show_toast') as mock_toast:
            service.notify_low_space("C:", 5.5)
            mock_toast.assert_called_once()

    def test_notify_low_space_exception(self):
        """Test notify_low_space exception handling."""
        from features.notifications.service import NotificationService
        service = NotificationService()
        
        with patch.object(service, '_show_toast', side_effect=Exception("Toast failed")):
            # Should not raise, just log error
            service.notify_low_space("C:", 5.5)

    def test_notify_cleanup_result_no_files(self):
        """Test notify_cleanup_result with no files deleted."""
        from features.notifications.service import NotificationService
        service = NotificationService()
        
        with patch.object(service, '_show_toast') as mock_toast:
            service.notify_cleanup_result(0, 0, 0.0)
            mock_toast.assert_called_once()
            call_args = mock_toast.call_args[0]
            assert "No files to clean up" in call_args[1]

    def test_notify_cleanup_result_with_files(self):
        """Test notify_cleanup_result with files deleted."""
        from features.notifications.service import NotificationService
        service = NotificationService()
        
        with patch.object(service, '_show_toast') as mock_toast:
            service.notify_cleanup_result(10, 2, 50.5)
            mock_toast.assert_called_once()
            call_args = mock_toast.call_args[0]
            assert "Freed" in call_args[1]

    def test_notify_cleanup_result_with_errors(self):
        """Test notify_cleanup_result with errors."""
        from features.notifications.service import NotificationService
        service = NotificationService()
        
        with patch.object(service, '_show_toast') as mock_toast:
            service.notify_cleanup_result(10, 2, 50.5, errors=3)
            mock_toast.assert_called_once()
            call_args = mock_toast.call_args[0]
            assert "skipped" in call_args[1]

    def test_notify_cleanup_result_exception(self):
        """Test notify_cleanup_result exception handling."""
        from features.notifications.service import NotificationService
        service = NotificationService()
        
        with patch.object(service, '_show_toast', side_effect=Exception("Toast failed")):
            # Should not raise
            service.notify_cleanup_result(10, 2, 50.5)

    def test_notify_error_success(self):
        """Test notify_error normal operation."""
        from features.notifications.service import NotificationService
        service = NotificationService()
        
        with patch.object(service, '_show_toast') as mock_toast:
            service.notify_error("Something went wrong")
            mock_toast.assert_called_once()

    def test_notify_error_exception(self):
        """Test notify_error exception handling."""
        from features.notifications.service import NotificationService
        service = NotificationService()
        
        with patch.object(service, '_show_toast', side_effect=Exception("Toast failed")):
            # Should not raise
            service.notify_error("Something went wrong")

    def test_show_toast_no_module(self):
        """Test _show_toast when win11toast is None."""
        from features.notifications import service as ns
        original_toast = ns.toast
        
        try:
            ns.toast = None
            svc = ns.NotificationService()
            svc._show_toast("Title", "Message")  # Should just log warning
        finally:
            ns.toast = original_toast

    def test_show_toast_exception(self):
        """Test _show_toast exception handling."""
        from features.notifications import service as ns
        
        mock_toast = MagicMock(side_effect=Exception("Toast error"))
        original_toast = ns.toast
        
        try:
            ns.toast = mock_toast
            svc = ns.NotificationService()
            svc._show_toast("Title", "Message")  # Should catch exception
        finally:
            ns.toast = original_toast

    def test_show_toast_success(self):
        """Test _show_toast successful call."""
        from features.notifications import service as ns
        
        mock_toast = MagicMock()
        original_toast = ns.toast
        
        try:
            ns.toast = mock_toast
            svc = ns.NotificationService()
            svc._show_toast("Title", "Message", duration="long")
            mock_toast.assert_called_once()
        finally:
            ns.toast = original_toast
