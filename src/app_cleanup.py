"""Cleanup flow helpers extracted from App."""
from __future__ import annotations


def do_cleanup(app, message_box_cls, cleanup_worker_cls, logger) -> None:
    """Start cleanup flow with confirmation and background worker."""
    try:
        if app._cleanup_worker is not None and app._cleanup_worker.isRunning():
            logger.warning("Cleanup already in progress")
            return

        directories = list(app._config.cleanup_directories)
        if not directories:
            logger.info("No directories to clean")
            return

        dir_list = "\n".join(f"  • {directory}" for directory in directories)
        result = message_box_cls.warning(
            app._main_window,
            "Confirm Cleanup",
            f"This will delete contents of {len(directories)} "
            f"directory(ies):\n\n{dir_list}\n\n"
            f"Are you sure you want to continue?",
            message_box_cls.StandardButton.Ok | message_box_cls.StandardButton.Cancel,
            message_box_cls.StandardButton.Cancel,
        )
        if result != message_box_cls.StandardButton.Ok:
            logger.info("Cleanup cancelled by user")
            return

        logger.info("Starting cleanup with %d directories", len(directories))

        if app._main_window:
            app._main_window.show_cleanup_progress(True)
        if app._tray_icon:
            app._tray_icon.set_status("Starting cleanup...")

        app._cleanup_worker = cleanup_worker_cls(directories, parent=app)
        app._cleanup_worker.progress_updated.connect(app._on_cleanup_progress)
        app._cleanup_worker.cleanup_finished.connect(app._on_cleanup_finished)
        app._cleanup_worker.start()
    except Exception as error:
        logger.error("Failed to start cleanup: %s", error)
        if app._main_window:
            app._main_window.show_cleanup_progress(False)
        if app._tray_icon:
            app._tray_icon.set_status(None)


def on_cleanup_progress(app, current: int, total: int, logger) -> None:
    """Update UI + tray cleanup progress."""
    try:
        if app._main_window:
            app._main_window.set_cleanup_progress(current, total)
        if app._tray_icon:
            app._tray_icon.set_status(f"Cleaning {current}/{total}...")
    except Exception as error:
        logger.error("Failed to update cleanup progress: %s", error)


def on_cleanup_finished(app, result, logger) -> None:
    """Finalize cleanup flow."""
    try:
        logger.info(
            "Cleanup finished: %d files, %d folders, %.2f MB",
            result.total_files,
            result.total_folders,
            result.total_size_mb,
        )

        if app._main_window:
            app._main_window.show_cleanup_progress(False)
        if app._tray_icon:
            app._tray_icon.set_status(None)

        app._notification_service.notify_cleanup_result(
            files_deleted=result.total_files,
            folders_deleted=result.total_folders,
            size_mb=result.total_size_mb,
            errors=len(result.errors),
        )
        app._cleanup_worker = None
    except Exception as error:
        logger.error("Failed to handle cleanup completion: %s", error)
