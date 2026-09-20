"""On-screen mock of the physical strips so colour changes are visible without hardware."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QRadialGradient
from PySide6.QtWidgets import QWidget


class StripPreview(QWidget):
    def __init__(self, leds: int = 24, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.leds = leds
        self._color = QColor(0, 0, 0)
        self._brightness = 1.0
        self._label = ""
        self.setMinimumHeight(64)

    def set_color(self, r: int, g: int, b: int, brightness: float = 1.0, label: str = "") -> None:
        self._color = QColor(int(r), int(g), int(b))
        self._brightness = max(0.0, min(1.0, brightness))
        self._label = label
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#08080B"))

        pad = 8.0
        width = (self.width() - pad * 2) / self.leds
        height = self.height() - pad * 2
        scaled = QColor(
            int(self._color.red() * self._brightness),
            int(self._color.green() * self._brightness),
            int(self._color.blue() * self._brightness),
        )

        for index in range(self.leds):
            rect = QRectF(pad + index * width + 1.5, pad, width - 3.0, height)
            gradient = QRadialGradient(rect.center(), max(rect.width(), rect.height()))
            gradient.setColorAt(0.0, scaled.lighter(140))
            gradient.setColorAt(1.0, scaled.darker(160))
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect, 4, 4)

        if self._label:
            painter.setPen(QColor("#A1A1AA"))
            painter.drawText(self.rect().adjusted(12, 0, -12, -4), Qt.AlignBottom | Qt.AlignRight, self._label)
        painter.end()
