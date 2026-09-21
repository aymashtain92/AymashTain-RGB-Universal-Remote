"""Neon-strip preview: grey backing, one soft capsule per LED.

Round 2 redesign
----------------
* Grey background so the whole thing reads as a physical strip.
* Each LED is a small capsule, not a filled box.
* Off LEDs are dark grey with no glow.
* On LEDs are full colour with a soft halo behind the capsule.
* Every LED can carry its own colour. When the caller only knows one colour
  (which is what the protocol actually sends), ``set_color`` repeats it
  across all LEDs. When an animation frame has per-LED data, feed it with
  ``set_led_colors`` and each capsule will show its own value.

The API stays compatible with the old class: ``set_color(r, g, b, brightness,
label)`` still works exactly as before, so nothing that already calls it
breaks.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget

#: Grey backing. Sits between the dark off-LED colour and the light caption,
#: so capsules stand out whether the app is in light or dark mode.
BACKGROUND = QColor("#3F3F46")
OFF_FILL = QColor("#18181B")
OFF_EDGE = QColor("#27272A")
LABEL_COLOR = QColor("#E4E4E7")

#: Treat anything with an average channel value at or below this as "off".
_OFF_THRESHOLD = 6.0


class StripPreview(QWidget):
    """Horizontal strip of LED capsules with a soft neon glow."""

    def __init__(self, leds: int = 30, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._leds = max(1, int(leds))
        self._led_colors: list[tuple[int, int, int]] = [(0, 0, 0)] * self._leds
        self._brightness = 1.0
        self._label = ""
        self.setMinimumHeight(84)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def leds(self) -> int:
        return self._leds

    def set_leds(self, count: int) -> None:
        """Change how many capsules are drawn."""
        count = max(1, int(count))
        if count == self._leds:
            return
        self._leds = count
        # Resize the colour list, repeating the last known colour.
        last = self._led_colors[-1] if self._led_colors else (0, 0, 0)
        if len(self._led_colors) < count:
            self._led_colors.extend([last] * (count - len(self._led_colors)))
        else:
            del self._led_colors[count:]
        self.update()

    def set_color(
        self,
        r: int,
        g: int,
        b: int,
        brightness: float = 1.0,
        label: str = "",
    ) -> None:
        """Set one colour across every LED. Kept for backwards compatibility."""
        colour = (int(r), int(g), int(b))
        self.set_led_colors([colour] * self._leds, brightness, label)

    def set_led_colors(
        self,
        colors: Iterable[Sequence[int]],
        brightness: float = 1.0,
        label: str = "",
    ) -> None:
        """Feed a per-LED colour list.

        * If fewer colours are supplied than there are LEDs, the last one is
          repeated across the remainder.
        * If more are supplied, the extras are dropped.
        """
        parsed: list[tuple[int, int, int]] = []
        for entry in colors:
            try:
                r, g, b = (int(entry[0]), int(entry[1]), int(entry[2]))
            except (TypeError, ValueError, IndexError):
                r, g, b = 0, 0, 0
            parsed.append((r, g, b))

        if not parsed:
            parsed = [(0, 0, 0)]

        if len(parsed) < self._leds:
            parsed.extend([parsed[-1]] * (self._leds - len(parsed)))
        elif len(parsed) > self._leds:
            parsed = parsed[: self._leds]

        self._led_colors = parsed
        self._brightness = max(0.0, min(1.0, float(brightness)))
        self._label = label
        self.update()

    def clear(self) -> None:
        """Turn every LED off."""
        self._led_colors = [(0, 0, 0)] * self._leds
        self._brightness = 1.0
        self._label = ""
        self.update()

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        # --- grey backing ---------------------------------------------
        painter.fillRect(self.rect(), BACKGROUND)

        # --- geometry -------------------------------------------------
        pad = 12.0
        slot = (self.width() - pad * 2) / self._leds
        capsule_w = max(3.0, slot * 0.62)
        capsule_h = min(self.height() * 0.42, 34.0)
        radius = min(capsule_w, capsule_h) / 2.0
        centre_y = self.height() / 2.0

        for index in range(self._leds):
            cx = pad + slot * (index + 0.5)
            r, g, b = self._led_colors[index]
            lit = (r + g + b) / 3.0 > _OFF_THRESHOLD and self._brightness > 0.0

            if lit:
                scaled = self._scaled(r, g, b)
                self._paint_glow(painter, cx, centre_y, slot, scaled)
                self._paint_lit_capsule(
                    painter, cx, centre_y, capsule_w, capsule_h, radius, scaled
                )
            else:
                self._paint_off_capsule(
                    painter, cx, centre_y, capsule_w, capsule_h, radius
                )

        # --- caption --------------------------------------------------
        if self._label:
            painter.setPen(LABEL_COLOR)
            painter.drawText(
                self.rect().adjusted(12, 0, -12, -4),
                Qt.AlignBottom | Qt.AlignRight,
                self._label,
            )

        painter.end()

    def _scaled(self, r: int, g: int, b: int) -> tuple[int, int, int]:
        factor = self._brightness
        return (
            max(0, min(255, int(round(r * factor)))),
            max(0, min(255, int(round(g * factor)))),
            max(0, min(255, int(round(b * factor)))),
        )

    def _paint_glow(
        self,
        painter: QPainter,
        cx: float,
        cy: float,
        slot: float,
        rgb: tuple[int, int, int],
    ) -> None:
        r, g, b = rgb
        # Glow alpha scales with brightness, so dim LEDs stay quiet.
        inner_alpha = int(170 * self._brightness)
        mid_alpha = int(55 * self._brightness)
        if inner_alpha <= 0:
            return

        radius = max(slot * 1.15, 8.0)
        glow = QRadialGradient(QPointF(cx, cy), radius)
        glow.setColorAt(0.0, QColor(r, g, b, inner_alpha))
        glow.setColorAt(0.45, QColor(r, g, b, mid_alpha))
        glow.setColorAt(1.0, QColor(r, g, b, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

    def _paint_lit_capsule(
        self,
        painter: QPainter,
        cx: float,
        cy: float,
        width: float,
        height: float,
        radius: float,
        rgb: tuple[int, int, int],
    ) -> None:
        rect = QRectF(cx - width / 2.0, cy - height / 2.0, width, height)
        base = QColor(*rgb)

        # Vertical gradient: bright at the top, colour in the middle,
        # slightly darker at the bottom → the diffuser look.
        body = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        body.setColorAt(0.0, base.lighter(155))
        body.setColorAt(0.45, base)
        body.setColorAt(1.0, base.darker(140))

        edge = base.lighter(170)
        edge.setAlpha(220)
        painter.setBrush(body)
        painter.setPen(QPen(edge, 1.0))
        painter.drawRoundedRect(rect, radius, radius)

        # Small inner highlight so the capsule looks like glass, not paint.
        highlight = QRectF(
            rect.x() + width * 0.18,
            rect.y() + height * 0.16,
            width * 0.34,
            height * 0.22,
        )
        h_radius = highlight.height() / 2.0
        painter.setBrush(QColor(255, 255, 255, 85))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(highlight, h_radius, h_radius)

    def _paint_off_capsule(
        self,
        painter: QPainter,
        cx: float,
        cy: float,
        width: float,
        height: float,
        radius: float,
    ) -> None:
        rect = QRectF(cx - width / 2.0, cy - height / 2.0, width, height)
        painter.setBrush(OFF_FILL)
        painter.setPen(QPen(OFF_EDGE, 1.0))
        painter.drawRoundedRect(rect, radius, radius)
