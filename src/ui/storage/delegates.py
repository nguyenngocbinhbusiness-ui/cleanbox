"""Delegates used by StorageView tree rendering."""

from __future__ import annotations

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QIcon, QLinearGradient, QPalette
from PyQt6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem

from ui.views.storage_view_tree import ROLE_IS_ROOT, ROLE_PERCENT_BAR


class NameColumnDelegate(QStyledItemDelegate):
    """Custom delegate for Name column with yellow size-proportional bar."""

    def paint(self, painter, option, index):
        """Paint yellow bar background then icon + text."""
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        painter.save()
        painter.setClipRect(opt.rect)

        is_root = index.data(ROLE_IS_ROOT)
        if is_root:
            painter.fillRect(opt.rect, QColor("#E8F0FE"))

        if not (opt.state & QStyle.StateFlag.State_Selected):
            percent = index.data(ROLE_PERCENT_BAR) or 0.0
            if percent > 0:
                bar_w = max(1, int(opt.rect.width() * min(percent, 100) / 100))
                bar_rect = QRect(opt.rect.x(), opt.rect.y(), bar_w, opt.rect.height())
                gradient = QLinearGradient(bar_rect.left(), 0, bar_rect.right(), 0)
                gradient.setColorAt(0, QColor(255, 220, 80, 180))
                gradient.setColorAt(1, QColor(255, 190, 40, 140))
                painter.fillRect(bar_rect, gradient)

        if opt.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(opt.rect, opt.palette.highlight())

        icon_x = opt.rect.x() + 2
        icon_size = opt.decorationSize
        icon_y = opt.rect.y() + (opt.rect.height() - icon_size.height()) // 2
        text_x = opt.rect.x() + 4
        if not opt.icon.isNull():
            mode = QIcon.Mode.Normal
            if opt.state & QStyle.StateFlag.State_Selected:
                mode = QIcon.Mode.Selected
            opt.icon.paint(
                painter,
                icon_x,
                icon_y,
                icon_size.width(),
                icon_size.height(),
                Qt.AlignmentFlag.AlignCenter,
                mode,
            )
            text_x = icon_x + icon_size.width() + 4

        text_rect = QRect(text_x, opt.rect.y(), opt.rect.right() - text_x, opt.rect.height())
        if opt.state & QStyle.StateFlag.State_Selected:
            painter.setPen(opt.palette.color(QPalette.ColorRole.HighlightedText))
        else:
            painter.setPen(opt.palette.color(QPalette.ColorRole.Text))
        painter.setFont(opt.font)
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            opt.text,
        )
        painter.restore()


class PercentBarDelegate(QStyledItemDelegate):
    """Custom delegate for % of Parent column with gradient bar."""

    def paint(self, painter, option, index):
        """Paint purple gradient bar with percent text overlay."""
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        painter.save()
        painter.setClipRect(opt.rect)

        painter.fillRect(opt.rect, QColor(255, 255, 255))

        percent = index.data(Qt.ItemDataRole.UserRole) or 0.0
        if percent > 0:
            bar_w = max(1, int(opt.rect.width() * min(percent, 100) / 100))
            bar_rect = QRect(opt.rect.x(), opt.rect.y(), bar_w, opt.rect.height())
            gradient = QLinearGradient(bar_rect.left(), 0, bar_rect.right(), 0)
            gradient.setColorAt(0, QColor(160, 150, 220, 200))
            gradient.setColorAt(1, QColor(120, 100, 200, 220))
            painter.fillRect(bar_rect, gradient)

        if opt.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(opt.rect, opt.palette.highlight())
            painter.setPen(opt.palette.color(QPalette.ColorRole.HighlightedText))
        else:
            painter.setPen(QColor(0, 0, 0))

        painter.setFont(opt.font)
        text = f"{percent:.1f} %" if percent > 0 else opt.text
        painter.drawText(
            opt.rect.adjusted(0, 0, -4, 0),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            text,
        )
        painter.restore()
