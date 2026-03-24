"""QThread worker classes used by StorageView scan flows."""

from __future__ import annotations

import logging

from PyQt6.QtCore import QThread, pyqtSignal

from features.folder_scanner import FolderInfo, FolderScanner

logger = logging.getLogger(__name__)


class ScanWorker(QThread):
    """Worker thread for folder scanning."""

    progress = pyqtSignal(str, int)  # current_path, items_scanned
    finished = pyqtSignal(object)  # FolderInfo or None

    def __init__(self, scanner: FolderScanner, path: str, max_depth: int = 1):
        """Initialize worker with scanner and parameters."""
        try:
            super().__init__()
            self.scanner = scanner
            self.path = path
            self.max_depth = max_depth
        except Exception as exc:
            logger.error("Failed to init ScanWorker: %s", exc)

    def run(self):
        """Execute the folder scan in a separate thread."""
        try:
            result = self.scanner.scan_folder(
                self.path,
                max_depth=self.max_depth,
                progress_callback=self._on_progress,
            )
            self.finished.emit(result)
        except Exception as exc:
            logger.error("Scan worker failed: %s", exc)
            self.finished.emit(None)

    def _on_progress(self, current_path: str, items_scanned: int):
        """Emit progress signal with scan updates."""
        try:
            self.progress.emit(current_path, items_scanned)
        except Exception as exc:
            logger.error("Failed to emit progress: %s", exc)


class ExpandScanWorker(QThread):
    """Worker thread for lazy-expand sub-folder scanning."""

    progress = pyqtSignal(str, int)
    finished = pyqtSignal(object)  # FolderInfo or None

    def __init__(self, scanner: FolderScanner, path: str):
        """Initialize expand worker."""
        try:
            super().__init__()
            self.scanner = scanner
            self.path = path
        except Exception as exc:
            logger.error("Failed to init ExpandScanWorker: %s", exc)

    def run(self):
        """Scan single level for expand."""
        try:
            result = self.scanner.scan_single_level(
                self.path,
                progress_callback=self._on_progress,
            )
            self.finished.emit(result)
        except Exception as exc:
            logger.error("Expand scan worker failed: %s", exc)
            self.finished.emit(None)

    def _on_progress(self, current_path: str, items_scanned: int):
        """Emit progress signal."""
        try:
            self.progress.emit(current_path, items_scanned)
        except Exception as exc:
            logger.error("Failed to emit expand progress: %s", exc)


class RealtimeScanWorker(QThread):
    """Worker thread that emits per-child results for real-time UI updates."""

    child_scanned = pyqtSignal(object)  # FolderInfo for one child
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(object, object)  # (root FolderInfo, path_index dict)

    def __init__(self, scanner: FolderScanner, path: str):
        """Initialize realtime scan worker."""
        try:
            super().__init__()
            self.scanner = scanner
            self.path = path
        except Exception as exc:
            logger.error("Failed to init RealtimeScanWorker: %s", exc)

    def run(self):
        """Scan children and emit each as completed."""
        try:
            result = self.scanner.scan_children_realtime(
                self.path,
                child_callback=self._on_child,
                progress_callback=self._on_progress,
            )
            path_index: dict[str, FolderInfo] = {}
            if result is not None:
                self._build_index(result, path_index)
            self.finished.emit(result, path_index)
        except Exception as exc:
            logger.error("Realtime scan worker failed: %s", exc)
            self.finished.emit(None, {})

    @staticmethod
    def _build_index(node: FolderInfo, index: dict) -> None:
        """Build flat path->FolderInfo index off the UI thread."""
        stack = [node]
        while stack:
            current = stack.pop()
            index[current.path] = current
            stack.extend(current.children)

    def _on_child(self, child_info: FolderInfo):
        """Emit child_scanned signal."""
        try:
            self.child_scanned.emit(child_info)
        except Exception as exc:
            logger.error("Failed to emit child_scanned: %s", exc)

    def _on_progress(self, current_path: str, items_scanned: int):
        """Emit progress signal."""
        try:
            self.progress.emit(current_path, items_scanned)
        except Exception as exc:
            logger.error("Failed to emit realtime progress: %s", exc)
