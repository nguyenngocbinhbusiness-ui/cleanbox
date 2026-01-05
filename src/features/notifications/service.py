"""Notification service - Windows toast notifications using win11toast."""
import logging

try:
    from win11toast import toast
except ImportError:
    toast = None

from shared.constants import APP_NAME

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for showing Windows toast notifications."""

    def notify_low_space(self, drive_letter: str, free_gb: float) -> None:
        """Show notification for low disk space."""
        try:
            title = f"{APP_NAME} - Low Disk Space"
            message = f"Drive {drive_letter} has only {
                free_gb:.1f} GB free space."

            logger.info("Showing low space notification for %s", drive_letter)
            self._show_toast(title, message)
        except Exception as e:
            logger.error("Failed to show low space notification: %s", e)

    def notify_cleanup_result(
        self,
        files_deleted: int,
        folders_deleted: int,
        size_mb: float,
        errors: int = 0,
    ) -> None:
        """Show notification for cleanup result."""
        try:
            title = f"{APP_NAME} - Cleanup Complete"

            if files_deleted == 0 and folders_deleted == 0:
                message = "No files to clean up."
            else:
                message = f"Freed {
                    size_mb:.1f} MB ({files_deleted} files, {folders_deleted} folders)"
                if errors > 0:
                    message += f" - {errors} items skipped"

            logger.info("Showing cleanup result notification")
            self._show_toast(title, message)
        except Exception as e:
            logger.error("Failed to notify cleanup result: %s", e)

    def notify_error(self, message: str) -> None:
        """Show error notification."""
        try:
            title = f"{APP_NAME} - Error"
            logger.error("Showing error notification: %s", message)
            self._show_toast(title, message)
        except Exception as e:
            logger.error("Failed to show error notification: %s", e)

    def _show_toast(
        self,
        title: str,
        message: str,
        duration: str = "short",  # "short" = 2s, "long" = 25s
    ) -> None:
        """Show a Windows toast notification."""
        if toast is None:
            logger.warning("Toast notifications not supported (win11toast missing)")
            return

        try:
            toast(title, message, app_id=APP_NAME, duration=duration)
        except Exception as e:
            logger.error("Failed to show notification: %s", e)

