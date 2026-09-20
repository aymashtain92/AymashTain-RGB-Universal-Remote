"""Protocol lab: history, byte diffing and promoting findings to remote buttons."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...protocol import SCROLL_MACRO, decode_hex_command
from ..context import AppContext


def diff_frames(left: str, right: str) -> list[tuple[int, str, str]]:
    """Byte-by-byte differences as ``(index, left_byte, right_byte)``."""
    left_bytes = [left[i : i + 2] for i in range(0, len(left), 2)]
    right_bytes = [right[i : i + 2] for i in range(0, len(right), 2)]
    width = max(len(left_bytes), len(right_bytes))
    out = []
    for index in range(width):
        a = left_bytes[index] if index < len(left_bytes) else "--"
        b = right_bytes[index] if index < len(right_bytes) else "--"
        if a != b:
            out.append((index, a, b))
    return out


class LabTab(QWidget):
    def __init__(self, ctx: AppContext, remote_tab=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.remote_tab = remote_tab

        layout = QVBoxLayout(self)

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
        layout.addLayout(actions)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Time", "Hex", "Label", "Family", "Meaning"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table, stretch=2)

        diff_box = QGroupBox("Analysis")
        diff_layout = QVBoxLayout(diff_box)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        diff_layout.addWidget(self.output)
        layout.addWidget(diff_box, stretch=1)

        layout.addWidget(
            QLabel(
                "Tip: send two variants from the console, then diff them here to find "
                "which byte a vendor app is actually changing."
            )
        )
        self.refresh()

    # --- data -------------------------------------------------------------

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

    # --- actions ----------------------------------------------------------

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
            lines.append(f"byte {index:>2}: {a} → {b}")
        self.output.setPlainText("\n".join(lines))

    def _promote(self) -> None:
        if self.remote_tab is None:
            return
        profile_id = self.remote_tab.current_profile_id()
        if profile_id is None:
            return
        for hex_cmd in self._selected_hex():
            info = decode_hex_command(hex_cmd)
            self.ctx.db.add_button(profile_id, info["meaning"][:28], hex_cmd, group_name="From lab")
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
            profile_id, name.strip(), frames[0], group_name="Macros", macro_frames=frames
        )
        self.remote_tab.refresh_buttons()
        self.output.append(f"Saved macro '{name.strip()}' with {len(frames)} frames.")

    def _load_scroll(self) -> None:
        for frame in SCROLL_MACRO:
            self.ctx.db.add_command(frame, label="scroll capture")
        self.refresh()
        self.output.append(f"Loaded {len(SCROLL_MACRO)} captured scroll frames into history.")

    def _clear(self) -> None:
        self.ctx.db.clear_commands()
        self.refresh()
