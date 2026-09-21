"""Protocol lab: history, byte diffing, promote to remote, plus a
hidden-feature laboratory that sends candidate hex frames one at a time,
waits, optionally captures a camera sample, and logs everything.
"""

from __future__ import annotations

import asyncio
import csv
import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...protocol import SCROLL_MACRO, decode_hex_command, validate_hex
from ..context import AppContext


def diff_frames(left: str, right: str) -> list[tuple[int, str, str]]:
    """Byte-by-byte differences as (index, left_byte, right_byte)."""
    left_bytes = [left[i : i + 2] for i in range(0, len(left), 2)]
    right_bytes = [right[i : i + 2] for i in range(0, len(right), 2)]
    width = max(len(left_bytes), len(right_bytes))
    out: list[tuple[int, str, str]] = []
    for index in range(width):
        a = left_bytes[index] if index < len(left_bytes) else "--"
        b = right_bytes[index] if index < len(right_bytes) else "--"
        if a != b:
            out.append((index, a, b))
    return out


class LabTab(QWidget):
    def __init__(
        self,
        ctx: AppContext,
        remote_tab=None,
        camera_tab=None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.remote_tab = remote_tab
        self.camera_tab = camera_tab

        # Hidden lab state
        self._running = False
        self._cancel = False
        self._results: list[dict] = []

        outer = QVBoxLayout(self)

        # ==================================================================
        # 1. History / diff / promote  (existing features)
        # ==================================================================
        history_box = QGroupBox("History and analysis")
        history_layout = QVBoxLayout(history_box)

        actions = QHBoxLayout()
        for label, slot, accent in (
            ("Refresh", self.refresh, False),
            ("Diff selected (2 rows)", self._diff, True),
            ("Add selected to remote", self._promote, False),
            ("Save selection as macro", self._save_macro, False),
            ("Load scroll capture", self._load_scroll, False),
            ("Clear history", self._clear, False),
        ):
            button = QPushButton(label)
            button.setProperty("accent", accent)
            button.clicked.connect(slot)
            actions.addWidget(button)
        actions.addStretch()
        history_layout.addLayout(actions)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Time", "Hex", "Label", "Family", "Meaning"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        history_layout.addWidget(self.table, stretch=1)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        history_layout.addWidget(self.output, stretch=1)

        outer.addWidget(history_box, stretch=1)

        # ==================================================================
        # 2. Hidden-feature laboratory  (new)
        # ==================================================================
        lab_box = QGroupBox("Hidden-feature laboratory")
        lab_layout = QVBoxLayout(lab_box)

        lab_layout.addWidget(
            QLabel(
                "Send candidate frames one at a time, wait, optionally capture a "
                "camera sample, and record what happened. Use this to unlock "
                "hidden modes. Emergency stop is the big red button and the Esc key."
            )
        )

        # Template generator
        template_row = QHBoxLayout()
        template_row.addWidget(QLabel("Template:"))
        self.lab_template = QLineEdit()
        self.lab_template.setPlaceholderText(
            "e.g. BC060200XX55   (use XX for the swept byte)"
        )
        template_row.addWidget(self.lab_template, stretch=3)

        template_row.addWidget(QLabel("Start:"))
        self.lab_start = QSpinBox()
        self.lab_start.setRange(0, 255)
        self.lab_start.setValue(0)
        template_row.addWidget(self.lab_start)

        template_row.addWidget(QLabel("End:"))
        self.lab_end = QSpinBox()
        self.lab_end.setRange(0, 255)
        self.lab_end.setValue(15)
        template_row.addWidget(self.lab_end)

        template_row.addWidget(QLabel("Step:"))
        self.lab_step = QSpinBox()
        self.lab_step.setRange(1, 16)
        self.lab_step.setValue(1)
        template_row.addWidget(self.lab_step)

        gen_btn = QPushButton("Generate")
        gen_btn.clicked.connect(self._generate_candidates)
        template_row.addWidget(gen_btn)

        clear_btn = QPushButton("Clear candidates")
        clear_btn.clicked.connect(lambda: self.lab_candidates.clear())
        template_row.addWidget(clear_btn)

        lab_layout.addLayout(template_row)

        # Candidate list
        lab_layout.addWidget(QLabel("Candidates (one hex per line):"))
        self.lab_candidates = QPlainTextEdit()
        self.lab_candidates.setPlaceholderText(
            "BC0602000055\nBC0602000155\nBC0602000255\n..."
        )
        self.lab_candidates.setMaximumHeight(140)
        lab_layout.addWidget(self.lab_candidates)

        # Controls
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Delay between candidates (ms):"))
        self.lab_delay = QSpinBox()
        self.lab_delay.setRange(200, 5000)
        self.lab_delay.setValue(500)
        controls.addWidget(self.lab_delay)

        controls.addWidget(QLabel("Hold after send (ms):"))
        self.lab_hold = QSpinBox()
        self.lab_hold.setRange(200, 10000)
        self.lab_hold.setValue(2000)
        controls.addWidget(self.lab_hold)

        self.lab_capture = QCheckBox("Capture camera sample")
        self.lab_capture.setChecked(
            bool(self.camera_tab and getattr(self.camera_tab.verifier, "is_open", False))
        )
        controls.addWidget(self.lab_capture)

        controls.addStretch()
        lab_layout.addLayout(controls)

        # Progress
        progress_row = QHBoxLayout()
        self.lab_progress = QProgressBar()
        self.lab_progress.setRange(0, 1)
        self.lab_progress.setValue(0)
        progress_row.addWidget(self.lab_progress, stretch=1)
        self.lab_status = QLabel("Idle.")
        progress_row.addWidget(self.lab_status)
        lab_layout.addLayout(progress_row)

        # Run buttons
        run_row = QHBoxLayout()
        self.lab_start_btn = QPushButton("Start sweep")
        self.lab_start_btn.setProperty("accent", True)
        self.lab_start_btn.clicked.connect(self._lab_start)
        run_row.addWidget(self.lab_start_btn)

        self.lab_test_first_btn = QPushButton("Test first candidate only")
        self.lab_test_first_btn.clicked.connect(self._lab_test_first)
        run_row.addWidget(self.lab_test_first_btn)

        self.lab_stop_btn = QPushButton("Emergency stop")
        self.lab_stop_btn.setProperty("danger", True)
        self.lab_stop_btn.clicked.connect(self._lab_stop)
        self.lab_stop_btn.setEnabled(False)
        run_row.addWidget(self.lab_stop_btn)

        run_row.addStretch()

        export_csv = QPushButton("Export results CSV")
        export_csv.clicked.connect(lambda: self._export_results("csv"))
        run_row.addWidget(export_csv)

        export_json = QPushButton("Export results JSON")
        export_json.clicked.connect(lambda: self._export_results("json"))
        run_row.addWidget(export_json)

        clear_results = QPushButton("Clear results")
        clear_results.clicked.connect(self._lab_clear_results)
        run_row.addWidget(clear_results)

        lab_layout.addLayout(run_row)

        # Results table
        self.lab_table = QTableWidget(0, 8)
        self.lab_table.setHorizontalHeaderLabels(
            ["#", "Time", "Hex", "Family", "Sent", "Observed RGB", "White %", "Note"]
        )
        self.lab_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.lab_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lab_table.setAlternatingRowColors(True)
        self.lab_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lab_table.doubleClicked.connect(self._edit_result_note)
        lab_layout.addWidget(self.lab_table, stretch=2)

        outer.addWidget(lab_box, stretch=2)

        self.refresh()

    # ==================================================================
    # Existing history features
    # ==================================================================

    def refresh(self) -> None:
        rows = self.ctx.db.get_commands(400)
        self.table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            info = decode_hex_command(row["hex"])
            for column, text in enumerate(
                [row["ts"], row["hex"], row["label"], info["family"], info["meaning"]]
            ):
                self.table.setItem(index, column, QTableWidgetItem(str(text)))

    def _selected_hex(self) -> list[str]:
        return [
            self.table.item(index.row(), 1).text()
            for index in self.table.selectionModel().selectedRows()
        ]

    def _diff(self) -> None:
        selection = self._selected_hex()
        if len(selection) != 2:
            self.output.setPlainText("Select exactly two rows to diff.")
            return
        left, right = selection
        differences = diff_frames(left, right)
        lines = [f"A: {left}", f"B: {right}", ""]
        if not differences:
            lines.append("Frames are identical.")
        for index, a, b in differences:
            lines.append(f"byte {index:>2}: {a} -> {b}")
        self.output.setPlainText("\n".join(lines))

    def _promote(self) -> None:
        if self.remote_tab is None:
            return
        profile_id = self.remote_tab.current_profile_id()
        if profile_id is None:
            return
        for hex_cmd in self._selected_hex():
            info = decode_hex_command(hex_cmd)
            self.ctx.db.add_button(
                profile_id, info["meaning"][:28], hex_cmd, group_name="From lab"
            )
        self.remote_tab.refresh_buttons()
        self.output.append("Added selection to the current remote profile.")

    def _save_macro(self) -> None:
        if self.remote_tab is None:
            return
        frames = self._selected_hex()
        if not frames:
            return
        name, ok = QInputDialog.getText(self, "Save macro", "Macro name")
        if not ok or not name.strip():
            return
        profile_id = self.remote_tab.current_profile_id()
        if profile_id is None:
            return
        self.ctx.db.add_button(
            profile_id,
            name.strip(),
            frames[0],
            group_name="Macros",
            macro_frames=frames,
        )
        self.remote_tab.refresh_buttons()
        self.output.append(f"Saved macro '{name.strip()}' with {len(frames)} frames.")

    def _load_scroll(self) -> None:
        for frame in SCROLL_MACRO:
            self.ctx.db.add_command(frame, label="scroll capture")
        self.refresh()
        self.output.append(f"Loaded {len(SCROLL_MACRO)} captured scroll frames.")

    def _clear(self) -> None:
        if QMessageBox.question(self, "Clear history", "Delete all history?") == QMessageBox.Yes:
            self.ctx.db.clear_commands()
            self.refresh()

    # ==================================================================
    # Hidden-feature laboratory
    # ==================================================================

    def _generate_candidates(self) -> None:
        template = self.lab_template.text().strip().upper()
        if "XX" not in template:
            QMessageBox.warning(
                self,
                "Template",
                "Template must contain XX where the swept byte goes.",
            )
            return

        start = self.lab_start.value()
        end = self.lab_end.value()
        step = self.lab_step.value()
        if start > end:
            QMessageBox.warning(self, "Range", "Start must be less than or equal to End.")
            return

        generated: list[str] = []
        for value in range(start, end + 1, step):
            hex_byte = f"{value:02X}"
            candidate = template.replace("XX", hex_byte)
            valid, _ = validate_hex(candidate)
            if valid:
                generated.append(candidate)

        if not generated:
            QMessageBox.warning(self, "Generate", "No valid candidates generated.")
            return

        existing = self.lab_candidates.toPlainText().strip()
        all_candidates = (existing + "\n" + "\n".join(generated)).strip()
        self.lab_candidates.setPlainText(all_candidates)
        self.lab_status.setText(f"Generated {len(generated)} candidates.")

    def _parse_candidates(self) -> list[str]:
        raw = self.lab_candidates.toPlainText()
        out: list[str] = []
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            valid, _ = validate_hex(line)
            if valid:
                out.append(line.upper())
        return out

    def _lab_start(self) -> None:
        if self._running:
            return
        candidates = self._parse_candidates()
        if not candidates:
            QMessageBox.information(self, "Lab", "No candidates to send.")
            return

        if len(candidates) > 50:
            reply = QMessageBox.question(
                self,
                "Large sweep",
                f"You are about to send {len(candidates)} candidates.\n"
                f"That's a lot. Continue?",
            )
            if reply != QMessageBox.Yes:
                return

        self._running = True
        self._cancel = False
        self.lab_start_btn.setEnabled(False)
        self.lab_stop_btn.setEnabled(True)
        self.lab_progress.setRange(0, len(candidates))
        self.lab_progress.setValue(0)
        self.lab_status.setText(f"Sending {len(candidates)} candidates...")
        self.ctx.run(self._lab_run(candidates))

    def _lab_test_first(self) -> None:
        if self._running:
            return
        candidates = self._parse_candidates()
        if not candidates:
            QMessageBox.information(self, "Lab", "No candidates to send.")
            return
        self._running = True
        self._cancel = False
        self.lab_start_btn.setEnabled(False)
        self.lab_stop_btn.setEnabled(True)
        self.lab_progress.setRange(0, 1)
        self.lab_progress.setValue(0)
        self.lab_status.setText("Testing first candidate only...")
        self.ctx.run(self._lab_run(candidates[:1]))

    def _lab_stop(self) -> None:
        self._cancel = True
        self.lab_status.setText("Stopping...")

    async def _lab_run(self, candidates: list[str]) -> None:
        delay_ms = self.lab_delay.value()
        hold_ms = self.lab_hold.value()
        capture_camera = self.lab_checkbox_state()

        try:
            for index, hex_cmd in enumerate(candidates, start=1):
                if self._cancel:
                    self.ctx.log("info", "Hidden lab: cancelled by user")
                    break

                info = decode_hex_command(hex_cmd)
                sent = await self.ctx.ble.send_hex_all(hex_cmd, label="lab")

                # Wait the hold time so the strip can react.
                await asyncio.sleep(hold_ms / 1000.0)

                rgb_measured: tuple[int, int, int] | None = None
                white: float | None = None
                brightness: float | None = None

                if capture_camera and self.camera_tab is not None:
                    if getattr(self.camera_tab.verifier, "is_open", False):
                        sample = self.camera_tab.capture_sample(
                            expected_rgb=None,
                            label=f"lab-{index}",
                        )
                        if sample is not None:
                            rgb_measured = sample.rgb
                            white = sample.white_contamination
                            brightness = sample.brightness

                self._record_result(
                    index=index,
                    hex_cmd=hex_cmd,
                    family=info.get("family", "unknown"),
                    meaning=info.get("meaning", ""),
                    sent=sent,
                    rgb=rgb_measured,
                    white=white,
                    brightness=brightness,
                )

                self.lab_progress.setValue(index)
                self.lab_status.setText(
                    f"{index}/{len(candidates)} — {hex_cmd} — sent to {sent} device(s)"
                )

                # Gap between candidates.
                if index < len(candidates):
                    await asyncio.sleep(delay_ms / 1000.0)

            if not self._cancel:
                self.lab_status.setText("Done.")
                self.ctx.log("info", f"Hidden lab finished ({len(candidates)} candidates)")

        except Exception as exc:
            self.ctx.log("error", f"Hidden lab failed: {exc}")
            self.lab_status.setText(f"Error: {exc}")
        finally:
            self._running = False
            self.lab_start_btn.setEnabled(True)
            self.lab_stop_btn.setEnabled(False)

    def lab_checkbox_state(self) -> bool:
        return self.lab_capture.isChecked()

    def _record_result(
        self,
        index: int,
        hex_cmd: str,
        family: str,
        meaning: str,
        sent: int,
        rgb: tuple[int, int, int] | None,
        white: float | None,
        brightness: float | None,
        note: str = "",
    ) -> None:
        record = {
            "index": index,
            "timestamp": datetime.now().isoformat(timespec="milliseconds"),
            "hex": hex_cmd,
            "family": family,
            "meaning": meaning,
            "sent": sent,
            "rgb": list(rgb) if rgb is not None else None,
            "white": white,
            "brightness": brightness,
            "note": note,
        }
        self._results.append(record)
        self._refresh_results_table()

    def _refresh_results_table(self) -> None:
        self.lab_table.setRowCount(len(self._results))
        for row_index, record in enumerate(self._results):
            rgb_text = "—"
            if record["rgb"] is not None:
                rgb_text = f"({record['rgb'][0]}, {record['rgb'][1]}, {record['rgb'][2]})"

            white_text = "—"
            if record["white"] is not None:
                white_text = f"{record['white'] * 100:.0f}%"

            cells = [
                str(record["index"]),
                record["timestamp"][11:19],
                record["hex"],
                record["family"],
                str(record["sent"]),
                rgb_text,
                white_text,
                record["note"],
            ]
            for column, text in enumerate(cells):
                self.lab_table.setItem(row_index, column, QTableWidgetItem(text))

        self.lab_table.scrollToBottom()

    def _edit_result_note(self) -> None:
        row = self.lab_table.currentRow()
        if row < 0 or row >= len(self._results):
            return
        current = self._results[row].get("note", "")
        text, ok = QInputDialog.getText(self, "Note", "Note for this result:", text=current)
        if not ok:
            return
        self._results[row]["note"] = text
        self._refresh_results_table()

    def _lab_clear_results(self) -> None:
        if not self._results:
            return
        if QMessageBox.question(self, "Clear results", "Delete all lab results?") != QMessageBox.Yes:
            return
        self._results.clear()
        self._refresh_results_table()

    def _export_results(self, fmt: str) -> None:
        if not self._results:
            QMessageBox.information(self, "Export", "No results to export.")
            return

        default_name = f"hidden_lab_results_{datetime.now():%Y%m%d_%H%M%S}.{fmt}"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export hidden lab results",
            default_name,
            "CSV (*.csv)" if fmt == "csv" else "JSON (*.json)",
        )
        if not path:
            return

        try:
            if fmt == "csv":
                with open(path, "w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(
                        handle,
                        fieldnames=[
                            "index",
                            "timestamp",
                            "hex",
                            "family",
                            "meaning",
                            "sent",
                            "rgb",
                            "white",
                            "brightness",
                            "note",
                        ],
                    )
                    writer.writeheader()
                    for record in self._results:
                        flat = dict(record)
                        flat["rgb"] = (
                            ",".join(str(v) for v in record["rgb"])
                            if record["rgb"] is not None
                            else ""
                        )
                        writer.writerow(flat)
            else:
                Path(path).write_text(
                    json.dumps(self._results, indent=2),
                    encoding="utf-8",
                )
            self.ctx.log("info", f"Hidden lab results exported: {path}")
        except Exception as exc:
            self.ctx.log("error", f"Export failed: {exc}")
            QMessageBox.critical(self, "Export failed", str(exc))
