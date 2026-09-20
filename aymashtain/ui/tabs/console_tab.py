"""Raw hex console: decode, dry-run and batch-send frames."""

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

from ...protocol import decode_hex_command, validate_hex
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

    def _decode(self) -> None:
        self.output.clear()
        for index, frame in enumerate(self.frames(), start=1):
            info = decode_hex_command(frame)
            colour = "#10B981" if info["valid"] else "#EF4444"
            self.output.append(
                f"<span style='color:{colour}'>[{index:>3}] {info['hex']}</span> "
                f"— {info['family']}: {info['meaning']} ({info.get('confidence', '?')})"
            )

    def _stop(self) -> None:
        self._cancel = True

    def _run(self, limit: int | None = None) -> None:
        self._cancel = False
        self.ctx.run(self._run_async(limit))

    async def _run_async(self, limit: int | None) -> None:
        frames = self.frames()[: limit or None]
        invalid = [f for f in frames if not validate_hex(f)[0]]
        if invalid:
            self.output.append(f"<span style='color:#EF4444'>Aborted: {len(invalid)} invalid frame(s)</span>")
            return

        delay = self.spin_delay.value() / 1000.0
        while True:
            for index, frame in enumerate(frames, start=1):
                if self._cancel:
                    self.output.append("Stopped.")
                    return
                sent = await self.ctx.ble.send_hex_all(frame, "console")
                self.ctx.db.add_command(frame, label="console", ok=bool(sent))
                self.output.append(f"[{index:>3}] {frame} → {sent} device(s)")
                if delay:
                    await asyncio.sleep(delay)
            if not self.chk_loop.isChecked() or self._cancel:
                break
        self.output.append("Done.")
