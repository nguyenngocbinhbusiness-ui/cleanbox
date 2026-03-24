"""Single-instance startup lock helpers for App."""

from __future__ import annotations

from typing import Any

from PyQt6.QtNetwork import QLocalServer, QLocalSocket


def acquire_single_instance(
    app,
    single_instance_key: str,
    logger,
    socket_cls: Any = QLocalSocket,
    server_cls: Any = QLocalServer,
) -> bool:
    """Acquire single-instance lock or signal existing instance to show."""
    app._startup_error = None
    try:
        socket = socket_cls()
        socket.connectToServer(single_instance_key)

        if socket.waitForConnected(500):
            socket.write(b"show")
            socket.waitForBytesWritten(1000)
            socket.close()
            logger.info("Sent 'show' command to existing instance")
            return False

        socket.close()

        app._local_server = server_cls()

        if app._local_server.listen(single_instance_key):
            logger.info("Single instance lock acquired")
            app._local_server.newConnection.connect(app._handle_new_connection)
            return True

        logger.warning(
            "Cannot listen on '%s': %s. Checking for stale lock...",
            single_instance_key,
            app._local_server.errorString(),
        )

        stale_check = socket_cls()
        stale_check.connectToServer(single_instance_key)

        if stale_check.waitForConnected(2000):
            stale_check.write(b"show")
            stale_check.waitForBytesWritten(1000)
            stale_check.close()
            logger.info("Confirmed another instance is running")
            return False

        stale_check.close()

        logger.warning(
            "Stale lock detected for '%s'. Removing and retrying...",
            single_instance_key,
        )
        server_cls.removeServer(single_instance_key)

        if app._local_server.listen(single_instance_key):
            logger.info("Single instance lock acquired after stale lock cleanup")
            app._local_server.newConnection.connect(app._handle_new_connection)
            return True

        app._startup_error = (
            "Failed to acquire single-instance lock after stale lock cleanup: "
            f"{app._local_server.errorString()}"
        )
        logger.error(app._startup_error)
        return False
    except Exception as exc:
        app._startup_error = f"Single instance check failed: {exc}"
        logger.error(app._startup_error)
        return False
