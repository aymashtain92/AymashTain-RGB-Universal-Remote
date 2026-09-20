"""HSV colour wheel with a value slider, emitting live RGB while dragging."""

from __future__ import annotations

import colorsys
import math

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class ColorWheel(QWidget):
    color_changed = Signal(int, int, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self._value = 1.0
        self._hue = 0.0
        self._saturation = 1.0
        self._wheel: QPixmap | None = None
        self.setCursor(Qt.CrossCursor)

    # --- public API -------------------------------------------------------

    def set_value(self, value: float) -> None:
        self._value = max(0.0, min(1.0, value))
        self._wheel = None
        self.update()

    def set_rgb(self, r: int, g: int, b: int) -> None:
        hue, saturation, value = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        self._hue, self._saturation, self._value = hue, saturation, max(value, 0.05)
        self._wheel = None
        self.update()

    def rgb(self) -> tuple[int, int, int]:
        r, g, b = colorsys.hsv_to_rgb(self._hue, self._saturation, self._value)
        return int(r * 255), int(g * 255), int(b * 255)

    # --- painting ---------------------------------------------------------

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt naming
        self._wheel = None
        super().resizeEvent(event)

    def _build_wheel(self) -> QPixmap:
        size = min(self.width(), self.height())
        image = QImage(size, size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        radius = size / 2.0

        for y in range(size):
            for x in range(size):
                dx = x - radius
                dy = y - radius
                distance = math.hypot(dx, dy)
                if distance > radius:
                    continue
                hue = (math.degrees(math.atan2(-dy, dx)) % 360) / 360.0
                saturation = min(1.0, distance / radius)
                r, g, b = colorsys.hsv_to_rgb(hue, saturation, self._value)
                image.setPixelColor(
                    x, y, QColor(int(r * 255), int(g * 255), int(b * 255))
                )
        return QPixmap.fromImage(image)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming
        if self._wheel is None or self._wheel.width() != min(self.width(), self.height()):
            self._wheel = self._build_wheel()

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        size = self._wheel.width()
        origin = QPointF((self.width() - size) / 2.0, (self.height() - size) / 2.0)
        painter.drawPixmap(origin, self._wheel)

        radius = size / 2.0
        angle = self._hue * 2 * math.pi
        marker = QPointF(
            origin.x() + radius + math.cos(angle) * self._saturation * radius,
            origin.y() + radius - math.sin(angle) * self._saturation * radius,
        )
        painter.setPen(QPen(QColor("#0B0B0F"), 3))
        painter.drawEllipse(marker, 8, 8)
        painter.setPen(QPen(QColor("#FAFAFA"), 2))
        painter.drawEllipse(marker, 8, 8)
        painter.end()

    # --- interaction ------------------------------------------------------

    def mousePressEvent(self, event) -> None:  # noqa: N802 - Qt naming
        self._pick(event.position())

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 - Qt naming
        if event.buttons() & Qt.LeftButton:
            self._pick(event.position())

    def _pick(self, position: QPointF) -> None:
        size = min(self.width(), self.height())
        radius = size / 2.0
        center = QPointF(self.width() / 2.0, self.height() / 2.0)
        dx = position.x() - center.x()
        dy = center.y() - position.y()
        distance = math.hypot(dx, dy)

        self._hue = (math.degrees(math.atan2(dy, dx)) % 360) / 360.0
        self._saturation = min(1.0, distance / radius)
        self.update()
        self.color_changed.emit(*self.rgb())
