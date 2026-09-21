"""Raw hex console: decode, dry-run and batch-send frames.

Round 2 change
--------------
* Any ``BC0506`` brightness frame typed or pasted here is clamped against
  the Options tab's min/max before it is queued. The clamp is the single
  source of truth for the whole app; the console is not allowed to bypass
  it. If a frame is adjusted, the console says so on the same line so the
  user can see the original and the clamped value side by side.
* Colour frames (``BC0406``) and everything else pass through untouched.
  Brightness is only ever a standalone ``BC0506`` frame — it is never
  merged into a colour frame.
"""

from __future__ import annotations

import asyncio

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
from ..context import AppContext

PLACEHOLDER = """BC01010155        # power on
BC0406003C03E8000055   # hue 60, saturation 100%
BC0506040000000055     # brightness 100%
"""


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
                "Brightness frames (BC0506…) are sent exactly as typed. "
                "Set a range in Options to clamp them here too."
            )
        else:
            self.lbl_clamp.setText(
                f"Brightness frames (BC0506…) are clamped to {lo}%–{hi}% "
                f"before sending, using the Options range."
            )

    # ------------------------------------------------------------------
    # Brightness clamp
    # ------------------------------------------------------------------

    def _clamp_brightness_frame(self, frame: str) -> tuple[str, bool]:
        """Clamp a ``BC0506`` brightness frame to the Options min/max.

        Returns ``(possibly_clamped_frame, was_clamped)``.

        Frames that are not a well-formed MR Star brightness frame are
        returned untouched — the console is still allowed to send raw
        experimental bytes. Only the *documented* brightness format is
        clamped, because that is the one path that can silently push a
        strip above the user's ceiling.
        """
        info = decode_hex_command(frame)
        if info.get("family") != "mrstar_brightness":
            return frame, False
        fraction = info.get("brightness_fraction")
        if fraction is None:
            # Malformed length / reserved bytes — leave it alone so the
            # user sees the validation error on their own frame.
            return frame, False

        original = float(fraction)
        clamped = self.ctx.settings.clamp_brightness(original)
        if abs(clamped - original) < 1e-6:
            return frame, False
        return encode_brightness(clamped), True

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
            clamped, changed = self._clamp_brightness_frame(frame)
            if changed:
                self.output.append(
                    f"      <span style='color:#F59E0B'>"
                    f"clamp: {frame} → {clamped}</span>"
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
                f"<span style='color:#EF4444'>Aborted: {len(invalid)} invalid frame(s)</span>"
            )
            return

        delay = self.spin_delay.value() / 1000.0
        while True:
            for index, original in enumerate(frames, start=1):
                if self._cancel:
                    self.output.append("Stopped.")
                    return

                # Apply the Options brightness clamp to BC0506 frames.
                frame, was_clamped = self._clamp_brightness_frame(original)

                sent = await self.ctx.ble.send_hex_all(frame, "console")
                self.ctx.db.add_command(frame, label="console", ok=bool(sent))

                if was_clamped:
                    self.output.append(
                        f"[{index:>3}] {original} → clamped to {frame} "
                        f"→ {sent} device(s)"
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
