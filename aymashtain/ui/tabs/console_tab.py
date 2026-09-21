# Original Path: aymashtain/ui/tabs/console_tab.py

"""Raw hex console: decode, dry-run and batch-send frames.

Round 3 Phase 0 fixes
---------------------
* **The clamp actually fires now.** The old code trusted
  ``decode_hex_command()`` to fill ``brightness_fraction``, but that
  helper only parses the *20-character* canonical brightness frame. The
  vendor documentation and the user both use the *16-character* short
  form (``BC0506040000000055``). The decoder returned ``None`` for the
  short form, the clamp thought the frame was unparseable, and 100 %
  went through untouched even when Options said 60 %. Fixed by parsing
  the brightness value directly out of any well-formed ``BC0506`` frame,
  regardless of how many reserved bytes it carries.
* **Canonical re-encode.** A clamped frame is re-encoded with the
  normal 20-character encoder, so every other consumer (DB, lab, other
  tabs, hardware) sees a consistent format.
* **Info label refreshes.** ``sync_clamp_notice()`` is wired to the
  Options brightness range via the main window.
* **Strip targeting.** Sends now go through ``ctx.resolve_targets()`` so
  the new multi-strip selection is honoured.
"""

from __future__ import annotations

import asyncio
import re

from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...protocol import (
    decode_hex_command,
    encode_brightness,
    validate_hex,
)
from ...protocol.mrstar import BRIGHTNESS_MAX
from ..context import AppContext

PLACEHOLDER = """BC01010155             # power on
BC0406003C03E8000055   # hue 60, saturation 100%
BC0506040000000055     # brightness 100% (short form)
"""

#: Any frame starting with this prefix is treated as an MR Star
#: brightness frame, no matter how many reserved bytes it carries.
_BRIGHTNESS_PREFIX = "BC0506"


class ConsoleTab(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self._cancel = False

        layout = QVBoxLayout(self)

        editor_box = QGroupBox("Frames (one per line, '#' starts a comment)")
        editor_layout = QVBoxLayout(editor_box)
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(PLACEHOLDER)
        editor_layout.addWidget(self.editor)
        layout.addWidget(editor_box, stretch=2)

        controls = QHBoxLayout()
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(0, 5000)
        self.spin_delay.setValue(120)
        self.spin_delay.setSuffix(" ms")
        self.chk_loop = QCheckBox("Loop")
        btn_decode = QPushButton("Decode only")
        btn_decode.clicked.connect(self._decode)
        btn_first = QPushButton("Send first frame")
        btn_first.clicked.connect(lambda: self._run(limit=1))
        btn_run = QPushButton("Send all")
        btn_run.setProperty("accent", True)
        btn_run.clicked.connect(lambda: self._run())
        btn_stop = QPushButton("Stop")
        btn_stop.setProperty("danger", True)
        btn_stop.clicked.connect(self._stop)
        controls.addWidget(QLabel("Delay"))
        controls.addWidget(self.spin_delay)
        controls.addWidget(self.chk_loop)
        controls.addWidget(btn_decode)
        controls.addWidget(btn_first)
        controls.addWidget(btn_run)
        controls.addWidget(btn_stop)
        controls.addStretch()
        layout.addLayout(controls)

        # Small notice so the user knows the clamp applies here too.
        self.lbl_clamp = QLabel("")
        self.lbl_clamp.setWordWrap(True)
        self.lbl_clamp.setStyleSheet("color: #71717A;")
        layout.addWidget(self.lbl_clamp)
        self._refresh_clamp_notice()

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output, stretch=2)

    # --- helpers ----------------------------------------------------------

    def frames(self) -> list[str]:
        out = []
        for line in self.editor.toPlainText().splitlines():
            frame = line.split("#", 1)[0].strip()
            if frame:
                out.append(frame)
        return out

    def _refresh_clamp_notice(self) -> None:
        lo = self.ctx.settings.brightness_min
        hi = self.ctx.settings.brightness_max
        if lo <= 0 and hi >= 100:
            self.lbl_clamp.setText(
                "Brightness frames (BC0506...) are sent exactly as typed. "
                "Set a range in Options to clamp them here too."
            )
        else:
            self.lbl_clamp.setText(
                f"Brightness frames (BC0506...) are clamped to {lo}%-{hi}% "
                f"before sending, using the Options range."
            )

    # ------------------------------------------------------------------
    # Brightness clamp
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_brightness_value(frame: str) -> int | None:
        """Return the 0..1024 brightness value from any ``BC0506`` frame.

        Accepts both the *16-character* short form used in the vendor
        documentation (``BC0506040000000055``) and the *20-character*
        canonical form the encoder produces
        (``BC050604000000000055``). Returns ``None`` when the frame does
        not look like a brightness frame at all, or when the value is
        out of range -- in both cases the caller leaves the frame alone
        so the user sees their raw bytes instead of a silent rewrite.
        """
        cleaned = re.sub(r"[^0-9A-Fa-f]", "", frame or "").upper()
        if not cleaned.startswith(_BRIGHTNESS_PREFIX):
            return None
        if len(cleaned) < len(_BRIGHTNESS_PREFIX) + 4:
            return None
        try:
            value = int(
                cleaned[len(_BRIGHTNESS_PREFIX):len(_BRIGHTNESS_PREFIX) + 4], 16
            )
        except ValueError:
            return None
        if value > BRIGHTNESS_MAX:
            return None
        return value

    def _clamp_brightness_frame(
        self, frame: str
    ) -> tuple[str, bool, str | None]:
        """Clamp a ``BC0506`` brightness frame to the Options min/max.

        Returns ``(possibly_clamped_frame, was_clamped, note)``. The note
        is a short human-readable string (e.g. ``"100% -> 60%"``) for
        the output pane, or ``None`` when no change was made.
        """
        value = self._extract_brightness_value(frame)
        if value is None:
            return frame, False, None

        original_fraction = value / float(BRIGHTNESS_MAX)
        clamped_fraction = self.ctx.settings.clamp_brightness(original_fraction)
        if abs(clamped_fraction - original_fraction) < 1e-6:
            return frame, False, None

        new_frame = encode_brightness(clamped_fraction)
        note = (
            f"{int(round(original_fraction * 100))}% -> "
            f"{int(round(clamped_fraction * 100))}%"
        )
        return new_frame, True, note

    # ------------------------------------------------------------------
    # Decode (dry run)
    # ------------------------------------------------------------------

    def _decode(self) -> None:
        self.output.clear()
        for index, frame in enumerate(self.frames(), start=1):
            info = decode_hex_command(frame)
            colour = "#10B981" if info["valid"] else "#EF4444"
            self.output.append(
                f"<span style='color:{colour}'>[{index:>3}] {info['hex']}</span> "
                f"— {info['family']}: {info['meaning']} ({info.get('confidence', '?')})"
            )

            # Show what the clamp would do, without sending anything.
            clamped, changed, note = self._clamp_brightness_frame(frame)
            if changed:
                self.output.append(
                    f"      <span style='color:#F59E0B'>"
                    f"clamp: {frame} → {clamped}  ({note})</span>"
                )

    # ------------------------------------------------------------------
    # Send
    # ------------------------------------------------------------------

    def _stop(self) -> None:
        self._cancel = True

    def _run(self, limit: int | None = None) -> None:
        self._cancel = False
        self.ctx.run(self._run_async(limit))

    async def _run_async(self, limit: int | None) -> None:
        frames = self.frames()[: limit or None]
        invalid = [f for f in frames if not validate_hex(f)[0]]
        if invalid:
            self.output.append(
                f"<span style='color:#EF4444'>Aborted: {len(invalid)} "
                f"invalid frame(s)</span>"
            )
            return

        delay = self.spin_delay.value() / 1000.0
        targets = self.ctx.resolve_targets()
        while True:
            for index, original in enumerate(frames, start=1):
                if self._cancel:
                    self.output.append("Stopped.")
                    return

                # Apply the Options brightness clamp to BC0506 frames.
                frame, was_clamped, note = self._clamp_brightness_frame(original)

                sent = await self.ctx.ble.send_hex_all(
                    frame, "console", addresses=targets
                )
                self.ctx.db.add_command(frame, label="console", ok=bool(sent))

                if was_clamped:
                    self.output.append(
                        f"[{index:>3}] {original} → clamped to {frame} "
                        f"({note}) → {sent} device(s)"
                    )
                else:
                    self.output.append(f"[{index:>3}] {frame} → {sent} device(s)")

                if delay:
                    await asyncio.sleep(delay)
            if not self.chk_loop.isChecked() or self._cancel:
                break
        self.output.append("Done.")

    # ------------------------------------------------------------------
    # External hook
    # ------------------------------------------------------------------

    def sync_clamp_notice(self) -> None:
        """Called by the main window when Options changes the brightness range."""
        self._refresh_clamp_notice()
