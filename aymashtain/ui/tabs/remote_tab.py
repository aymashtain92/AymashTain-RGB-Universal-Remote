"""Colour control plus the user-editable button remote."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...protocol import CMD_OFF, CMD_ON, EFFECTS, encode_brightness, encode_color, encode_effect
from ..context import AppContext
from ..widgets import ColorWheel, StripPreview

PRESETS = [
    ("Red", (255, 0, 0)),
    ("Orange", (255, 110, 0)),
    ("Yellow", (255, 210, 0)),
    ("Green", (0, 255, 0)),
    ("Cyan", (0, 255, 255)),
    ("Blue", (0, 0, 255)),
    ("Violet", (150, 0, 255)),
    ("Magenta", (255, 0, 255)),
    ("Warm white", (255, 190, 120)),
    ("Cool white", (220, 235, 255)),
]


class ButtonDialog(QDialog):
    def __init__(self, parent: QWidget, label="", hex_cmd="", group="Ungrouped", frames=""):
        super().__init__(parent)
        self.setWindowTitle("Remote button")
        form = QFormLayout(self)
        self.edit_label = QLineEdit(label)
        self.edit_hex = QLineEdit(hex_cmd)
        self.edit_group = QLineEdit(group)
        self.edit_frames = QPlainTextEdit(frames)
        self.edit_frames.setPlaceholderText("Optional macro: one hex frame per line")
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(10, 5000)
        self.spin_delay.setValue(120)
        self.spin_delay.setSuffix(" ms")
        form.addRow("Label", self.edit_label)
        form.addRow("Hex", self.edit_hex)
        form.addRow("Group", self.edit_group)
        form.addRow("Macro frames", self.edit_frames)
        form.addRow("Macro delay", self.spin_delay)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self) -> dict:
        frames = [line.strip() for line in self.edit_frames.toPlainText().splitlines() if line.strip()]
        return {
            "label": self.edit_label.text().strip() or "Button",
            "hex": self.edit_hex.text().strip(),
            "group": self.edit_group.text().strip() or "Ungrouped",
            "frames": frames,
            "delay": self.spin_delay.value(),
        }


class RemoteTab(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.rgb = tuple(ctx.settings.last_color)

        layout = QHBoxLayout(self)

        # --- left: colour -------------------------------------------------
        left = QVBoxLayout()

        power = QHBoxLayout()
        btn_on = QPushButton("Power ON")
        btn_on.setProperty("accent", True)
        btn_on.clicked.connect(lambda: self._send(CMD_ON, "power on"))
        btn_off = QPushButton("Power OFF")
        btn_off.setProperty("danger", True)
        btn_off.clicked.connect(lambda: self._send(CMD_OFF, "power off"))
        power.addWidget(btn_on)
        power.addWidget(btn_off)
        left.addLayout(power)

        wheel_box = QGroupBox("Colour")
        wheel_layout = QVBoxLayout(wheel_box)
        self.wheel = ColorWheel()
        self.wheel.set_rgb(*self.rgb)
        self.wheel.color_changed.connect(self._on_wheel)
        wheel_layout.addWidget(self.wheel, stretch=1)

        preset_grid = QGridLayout()
        for index, (name, rgb) in enumerate(PRESETS):
            button = QPushButton(name)
            button.setStyleSheet(f"border-left: 6px solid rgb{rgb};")
            button.clicked.connect(lambda _=False, c=rgb: self._apply_color(*c))
            preset_grid.addWidget(button, index // 5, index % 5)
        wheel_layout.addLayout(preset_grid)
        left.addWidget(wheel_box, stretch=1)

        bright_box = QGroupBox("Brightness")
        bright_layout = QVBoxLayout(bright_box)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(ctx.settings.last_brightness)
        self.slider.sliderReleased.connect(self._on_brightness)
        self.lbl_brightness = QLabel(f"{self.slider.value()}%")
        self.slider.valueChanged.connect(lambda v: self.lbl_brightness.setText(f"{v}%"))
        row = QHBoxLayout()
        row.addWidget(self.slider, stretch=1)
        row.addWidget(self.lbl_brightness)
        bright_layout.addLayout(row)
        left.addWidget(bright_box)

        effects_box = QGroupBox("Effects")
        effects_layout = QHBoxLayout(effects_box)
        self.combo_effect = QComboBox()
        for code, name in EFFECTS.items():
            self.combo_effect.addItem(f"{name} (0x{code})", code)
        btn_effect = QPushButton("Send effect")
        btn_effect.clicked.connect(
            lambda: self._send(encode_effect(self.combo_effect.currentData()), "effect")
        )
        effects_layout.addWidget(self.combo_effect, stretch=1)
        effects_layout.addWidget(btn_effect)
        left.addWidget(effects_box)

        self.preview = StripPreview()
        self.preview.set_color(*self.rgb, brightness=self.slider.value() / 100.0)
        left.addWidget(self.preview)

        layout.addLayout(left, stretch=3)

        # --- right: remote buttons ---------------------------------------
        right = QVBoxLayout()
        profile_row = QHBoxLayout()
        self.combo_profile = QComboBox()
        self.combo_profile.currentIndexChanged.connect(lambda _: self.refresh_buttons())
        for label, slot in (("New", self._new_profile), ("Rename", self._rename_profile), ("Delete", self._delete_profile)):
            button = QPushButton(label)
            button.clicked.connect(slot)
            profile_row.addWidget(button)
        right.addWidget(QLabel("<b>Remote profile</b>"))
        right.addWidget(self.combo_profile)
        right.addLayout(profile_row)

        self.button_area = QScrollArea()
        self.button_area.setWidgetResizable(True)
        right.addWidget(self.button_area, stretch=1)

        btn_add = QPushButton("Add button…")
        btn_add.setProperty("accent", True)
        btn_add.clicked.connect(self._add_button)
        right.addWidget(btn_add)

        layout.addLayout(right, stretch=2)

        self.refresh_profiles()

    # --- colour -----------------------------------------------------------

    def _on_wheel(self, r: int, g: int, b: int) -> None:
        self._apply_color(r, g, b)

    def _apply_color(self, r: int, g: int, b: int) -> None:
        self.rgb = (r, g, b)
        self.ctx.settings.last_color = [r, g, b]
        brightness = self.slider.value() / 100.0
        self.wheel.set_rgb(r, g, b)
        self.preview.set_color(r, g, b, brightness, f"rgb({r},{g},{b})")
        self.ctx.db.add_command(encode_color(r, g, b), label="color")
        self.ctx.run(self.ctx.ble.set_color(r, g, b, brightness))

    def _on_brightness(self) -> None:
        value = self.slider.value()
        self.ctx.settings.last_brightness = value
        self.preview.set_color(*self.rgb, brightness=value / 100.0)
        self._send(encode_brightness(value / 100.0), "brightness")

    def _send(self, hex_cmd: str, label: str) -> None:
        self.ctx.db.add_command(hex_cmd, label=label)
        self.ctx.run(self.ctx.ble.send_hex_all(hex_cmd, label))

    # --- profiles ---------------------------------------------------------

    def refresh_profiles(self) -> None:
        self.combo_profile.blockSignals(True)
        self.combo_profile.clear()
        for profile in self.ctx.db.get_profiles():
            self.combo_profile.addItem(profile.name, profile.id)
        index = self.combo_profile.findText(self.ctx.settings.last_profile)
        self.combo_profile.setCurrentIndex(max(0, index))
        self.combo_profile.blockSignals(False)
        self.refresh_buttons()

    def current_profile_id(self) -> int | None:
        data = self.combo_profile.currentData()
        return int(data) if data is not None else None

    def _new_profile(self) -> None:
        name, ok = QInputDialog.getText(self, "New profile", "Profile name")
        if ok and name.strip():
            self.ctx.db.create_profile(name.strip())
            self.ctx.settings.last_profile = name.strip()
            self.refresh_profiles()

    def _rename_profile(self) -> None:
        profile_id = self.current_profile_id()
        if profile_id is None:
            return
        name, ok = QInputDialog.getText(
            self, "Rename profile", "New name", text=self.combo_profile.currentText()
        )
        if ok and name.strip():
            self.ctx.db.rename_profile(profile_id, name.strip())
            self.refresh_profiles()

    def _delete_profile(self) -> None:
        profile_id = self.current_profile_id()
        if profile_id is None or self.combo_profile.count() <= 1:
            return
        confirm = QMessageBox.question(
            self, "Delete profile", f"Delete '{self.combo_profile.currentText()}' and its buttons?"
        )
        if confirm == QMessageBox.Yes:
            self.ctx.db.delete_profile(profile_id)
            self.refresh_profiles()

    # --- buttons ----------------------------------------------------------

    def refresh_buttons(self) -> None:
        profile_id = self.current_profile_id()
        container = QWidget()
        layout = QVBoxLayout(container)
        if profile_id is None:
            self.button_area.setWidget(container)
            return

        self.ctx.settings.last_profile = self.combo_profile.currentText()
        groups: dict[str, list] = {}
        for button in self.ctx.db.get_buttons(profile_id):
            groups.setdefault(button.group_name, []).append(button)

        for group_name, buttons in groups.items():
            box = QGroupBox(group_name)
            grid = QGridLayout(box)
            for index, button in enumerate(buttons):
                widget = QPushButton(button.label + (" ▶" if button.is_macro else ""))
                widget.setToolTip(button.hex if not button.is_macro else f"{len(button.macro_frames)} frames")
                widget.clicked.connect(lambda _=False, b=button: self._fire(b))
                widget.setContextMenuPolicy(Qt.CustomContextMenu)
                widget.customContextMenuRequested.connect(
                    lambda pos, b=button, w=widget: self._context_menu(w, pos, b)
                )
                grid.addWidget(widget, index // 3, index % 3)
            layout.addWidget(box)
        layout.addStretch()
        self.button_area.setWidget(container)

    def _fire(self, button) -> None:
        if button.is_macro:
            self.ctx.log("send", f"Macro '{button.label}' ({len(button.macro_frames)} frames)")
            self.ctx.run(
                self.ctx.ble.run_macro(button.macro_frames, button.macro_delay_ms)
            )
        else:
            self._send(button.hex, button.label)

    def _context_menu(self, widget: QWidget, pos, button) -> None:
        menu = QMenu(self)
        action_edit = menu.addAction("Edit…")
        action_clone = menu.addAction("Duplicate")
        action_delete = menu.addAction("Delete")
        chosen = menu.exec(widget.mapToGlobal(pos))
        if chosen == action_edit:
            self._edit_button(button)
        elif chosen == action_clone:
            self.ctx.db.clone_button(button.id)
            self.refresh_buttons()
        elif chosen == action_delete:
            self.ctx.db.delete_button(button.id)
            self.refresh_buttons()

    def _add_button(self) -> None:
        profile_id = self.current_profile_id()
        if profile_id is None:
            return
        dialog = ButtonDialog(self, hex_cmd=encode_color(*self.rgb))
        if dialog.exec() != QDialog.Accepted:
            return
        values = dialog.values()
        self.ctx.db.add_button(
            profile_id,
            values["label"],
            values["hex"] or (values["frames"][0] if values["frames"] else ""),
            group_name=values["group"],
            macro_frames=values["frames"],
            macro_delay_ms=values["delay"],
        )
        self.refresh_buttons()

    def _edit_button(self, button) -> None:
        dialog = ButtonDialog(
            self,
            button.label,
            button.hex,
            button.group_name,
            "\n".join(button.macro_frames or []),
        )
        dialog.spin_delay.setValue(button.macro_delay_ms)
        if dialog.exec() != QDialog.Accepted:
            return
        values = dialog.values()
        self.ctx.db.update_button(
            button.id, values["label"], values["hex"], values["group"], values["frames"], values["delay"]
        )
        self.refresh_buttons()
