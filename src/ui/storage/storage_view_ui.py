"""UI construction helpers for StorageView."""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from ui.storage.delegates import NameColumnDelegate, PercentBarDelegate
from ui.views.storage_view_tree import (
    COL_ALLOCATED,
    COL_FILES,
    COL_FOLDERS,
    COL_NAME,
    COL_PERCENT,
    COL_SIZE,
)

logger = logging.getLogger(__name__)


def setup_ui(view) -> None:
    """Build StorageView UI controls and wire handlers."""
    try:
        layout = QVBoxLayout(view)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header_layout = QHBoxLayout()
        title = QLabel("Storage Analyzer")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        desc = QLabel("Analyze disk space usage by folder. Select a drive and click Scan.")
        desc.setStyleSheet("color: #666666;")
        layout.addWidget(desc)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #E0E0E0;")
        layout.addWidget(separator)

        drive_layout = QHBoxLayout()
        drive_label = QLabel("Drive:")
        drive_layout.addWidget(drive_label)

        view._drive_combo = QComboBox()
        view._drive_combo.setMinimumWidth(150)
        view._drive_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        drive_layout.addWidget(view._drive_combo)

        view._scan_btn = QPushButton("Scan")
        view._scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view._scan_btn.clicked.connect(view._on_scan)
        view._scan_btn.setStyleSheet(
            """
                QPushButton {
                    background-color: #0078D4;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #005A9E;
                }
                QPushButton:disabled {
                    background-color: #CCCCCC;
                }
            """
        )
        drive_layout.addWidget(view._scan_btn)

        view._cancel_btn = QPushButton("Cancel")
        view._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view._cancel_btn.clicked.connect(view._on_cancel)
        view._cancel_btn.setEnabled(False)
        drive_layout.addWidget(view._cancel_btn)

        view._refresh_btn = QPushButton("Refresh Drives")
        view._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view._refresh_btn.clicked.connect(view._on_refresh)
        drive_layout.addWidget(view._refresh_btn)
        drive_layout.addStretch()

        view._back_btn = QPushButton("◀ Back")
        view._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view._back_btn.clicked.connect(view._on_navigate_back)
        view._back_btn.setEnabled(False)
        view._back_btn.setStyleSheet(
            """
                QPushButton {
                    background-color: #F0F0F0;
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #E0E0E0; }
                QPushButton:disabled { color: #AAAAAA; }
            """
        )
        drive_layout.addWidget(view._back_btn)

        view._forward_btn = QPushButton("Forward ▶")
        view._forward_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view._forward_btn.clicked.connect(view._on_navigate_forward)
        view._forward_btn.setEnabled(False)
        view._forward_btn.setStyleSheet(
            """
                QPushButton {
                    background-color: #F0F0F0;
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #E0E0E0; }
                QPushButton:disabled { color: #AAAAAA; }
            """
        )
        drive_layout.addWidget(view._forward_btn)
        layout.addLayout(drive_layout)

        view._progress_bar = QProgressBar()
        view._progress_bar.setTextVisible(True)
        view._progress_bar.setFormat("Scanning... %v items")
        view._progress_bar.setMaximum(0)
        view._progress_bar.hide()
        layout.addWidget(view._progress_bar)

        view._status_label = QLabel("")
        view._status_label.setStyleSheet("color: #666666; font-size: 11px;")
        view._status_label.setWordWrap(True)
        view._status_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        view._status_label.setMaximumHeight(
            view._status_label.fontMetrics().lineSpacing() * 2 + 4
        )
        layout.addWidget(view._status_label)

        view._summary_frame = QFrame()
        view._summary_frame.setStyleSheet(
            """
                QFrame#SummaryFrame {
                    background-color: #F8F9FA;
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                }
            """
        )
        view._summary_frame.setObjectName("SummaryFrame")
        view._summary_layout = QVBoxLayout(view._summary_frame)
        view._summary_layout.setContentsMargins(12, 12, 12, 12)
        view._summary_layout.setSpacing(8)

        summary_title = QLabel("Drive Summary")
        summary_title.setStyleSheet("font-weight: bold; color: #333333;")
        view._summary_layout.addWidget(summary_title)

        view._drive_bars_widget = QWidget()
        view._drive_bars_layout = QVBoxLayout(view._drive_bars_widget)
        view._drive_bars_layout.setContentsMargins(0, 0, 0, 0)
        view._drive_bars_layout.setSpacing(8)
        view._summary_layout.addWidget(view._drive_bars_widget)
        layout.addWidget(view._summary_frame)

        view._tree = QTreeWidget()
        view._tree.setHeaderLabels(
            ["Name", "Size", "Allocated", "Files", "Folders", "% of Parent (Size)"]
        )
        view._tree.setAlternatingRowColors(True)
        view._tree.setRootIsDecorated(True)
        view._tree.setSortingEnabled(True)
        view._tree.sortByColumn(COL_PERCENT, Qt.SortOrder.DescendingOrder)

        header = view._tree.header()
        header.setSectionResizeMode(COL_NAME, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(COL_SIZE, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(COL_ALLOCATED, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(COL_FILES, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(COL_FOLDERS, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(COL_PERCENT, QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        header.resizeSection(COL_NAME, 260)
        header.resizeSection(COL_SIZE, 90)
        header.resizeSection(COL_ALLOCATED, 90)
        header.resizeSection(COL_FILES, 80)
        header.resizeSection(COL_FOLDERS, 80)
        header.resizeSection(COL_PERCENT, 130)

        view._name_delegate = NameColumnDelegate(view._tree)
        view._tree.setItemDelegateForColumn(COL_NAME, view._name_delegate)
        view._percent_delegate = PercentBarDelegate(view._tree)
        view._tree.setItemDelegateForColumn(COL_PERCENT, view._percent_delegate)

        view._tree.setStyleSheet(
            """
                QTreeWidget {
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                    background-color: white;
                }
                QTreeWidget::item {
                    padding: 4px;
                }
                QHeaderView::section {
                    background-color: #F5F5F5;
                    padding: 8px;
                    border: none;
                    border-bottom: 1px solid #E0E0E0;
                    font-weight: bold;
                }
            """
        )

        view._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        view._tree.customContextMenuRequested.connect(view._on_tree_context_menu)
        view._tree.itemExpanded.connect(view._on_item_expanded)
        view._tree.itemDoubleClicked.connect(view._on_item_double_clicked)
        layout.addWidget(view._tree)
    except Exception as exc:
        logger.error("Failed to setup StorageView UI: %s", exc)
