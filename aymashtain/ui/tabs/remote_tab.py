# Original Path: aymashtain/ui/tabs/remote_tab.py

"""Colour control, brightness, and the new Light-modes section.

Round 3 rewrite
---------------
* **Light modes section added.** Under the colour wheel and brightness
  slider, before the strip preview, there is now a stacked list of
  collapsible categories that mirror the vendor app's "Light Mode" tab:
  Basic, Opening & closing, Transition, Running water, Tailing,
  Running. Each category expands to reveal its mode buttons. Clicking
  a mode sends a ``BC06 02`` effect frame.

* **Music modes removed from this tab.** The four "Controller mode"
  entries that used to be here live in the Music & Media tab now, where
  they belong.

* **Multi-strip preview.** Instead of one strip preview, the tab now
  draws one row per connected+selected strip, so the user can see at a
  glance how many strips are being controlled. When the strip selector
  in the main window is empty, every connected strip gets its own row.

* **Best-guess hexes.** The vendor app's Light Mode opcodes are not in
  the captured protocol. Every button here is mapped to the closest
  documented effect byte (Rainbow, Chase, Fade, Breathe, Strobe, etc.)
  and the tooltip says which one. Right-click any button to override
  the frame with a captured one -- overrides last for the session.

Colour + brightness rules kept from Round 2
-------------------------------------------
* Brightness is clamped through ``settings.clamp_brightness()``.
* Live preview updates while the slider drags; the real ``BC0506``
  frame only goes out on release.
* Colour and brightness stay as two separate frames --
  ``BleManager.set_color()`` decides the order.
* Sends go through ``ctx.resolve_targets()`` so the multi-strip
  selector in the main window is honoured.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
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

from ...protocol import (
    CMD_OFF,
    CMD_ON,
    encode_brightness,
    encode_color,
)
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


# ---------------------------------------------------------------------------
# Light-mode catalogue
# ---------------------------------------------------------------------------
#
# The vendor app's "Light Mode" tab groups effects into six categories.
# We mirror the group names and the mode names exactly.
#
# IMPORTANT: The opcode for a specific mode is *not* in the captured
# protocol yet. Each mode here is mapped to the closest documented
# effect byte so the button produces a visible result:
#
#   0x02 Breathe     -- pulsing / opening-closing style
#   0x03 Strobe      -- fast flashing
#   0x04 Flash       -- single blip
#   0x05 Fade        -- tail / trailing
#   0x06 Rainbow     -- full-colour cycling
#   0x07 Rainbow fade -- soft colour cross-fade
#   0x08 Chase       -- running / chasing
#   0x09 Scroll      -- flowing / running water
#   0x0A Twinkle     -- sparkle / fluttering
#
# Once you capture a real opcode from the vendor app (via the Lab tab),
# right-click the button and paste it in. Overrides live for the session.
#
LIGHT_MODE_CATEGORIES: list[tuple[str, list[tuple[str, str]]]] = [
    ("Basic", [
        ("Automatic loop", "BC060206000055"),
        ("Symphony", "BC060206000055"),
        ("Colourful energy", "BC060208000055"),
        ("Colourful jumps", "BC060204000055"),
        ("7 colours strobe", "BC060203000055"),
        ("7 colours gradient", "BC060207000055"),
        ("Colourful fluttering", "BC06020A000055"),
        ("Red-green-blue fluttering", "BC06020A000055"),
        ("Colourful brushing", "BC060205000055"),
        ("Red-green-blue color brushing", "BC060205000055"),
        ("Yellow-cyan-purple color brushing", "BC060205000055"),
        ("Colourful brush closed-pull", "BC060205000055"),
    ]),
    ("Opening & closing", [
        ("7 colours opening-closing", "BC060202000055"),
        ("Red-green-blue opening-closing", "BC060202000055"),
        ("Yellow-cyan-purple opening-closes", "BC060202000055"),
        ("Red opening-closing", "BC060202000055"),
        ("Green opening-closing", "BC060202000055"),
        ("Blue opening-closing", "BC060202000055"),
        ("Yellow opening-closing", "BC060202000055"),
        ("Cyan opening-closing", "BC060202000055"),
        ("Purple opening-closing", "BC060202000055"),
        ("White opening-closing", "BC060202000055"),
    ]),
    ("Transition", [
        ("7 colours transition", "BC060207000055"),
        ("Blue-red-green transition", "BC060207000055"),
        ("Violet-green-yellow transition", "BC060207000055"),
        ("6 colours transition red", "BC060207000055"),
        ("6 colours transition green", "BC060207000055"),
        ("6 colours transition blue", "BC060207000055"),
        ("6 colours transition cyan", "BC060207000055"),
        ("6 colours transition yellow", "BC060207000055"),
        ("6 colours transition purple", "BC060207000055"),
        ("6 colours transition white", "BC060207000055"),
    ]),
    ("Running water", [
        ("7 colours flowing water", "BC060209000055"),
        ("Blue-green-red running water", "BC060209000055"),
        ("Purple-green-yellow running water", "BC060209000055"),
        ("Red-green running water", "BC060209000055"),
        ("Green-blue running water", "BC060209000055"),
        ("Yellow-blue running water", "BC060209000055"),
        ("Yellow-cyan running water", "BC060209000055"),
        ("Blue-purple running water", "BC060209000055"),
    ]),
    ("Tailing", [
        ("7 colours tailing", "BC060205000055"),
        ("Red tailing", "BC060205000055"),
        ("Green tailing", "BC060205000055"),
        ("Blue tailing", "BC060205000055"),
        ("Yellow tailing", "BC060205000055"),
        ("Cyan tailing", "BC060205000055"),
        ("Purple tailing", "BC060205000055"),
        ("White tailing", "BC060205000055"),
    ]),
    ("Running", [
        ("Red running", "BC060208000055"),
        ("Green running", "BC060208000055"),
        ("Blue running", "BC060208000055"),
        ("Yellow running", "BC060208000055"),
        ("Cyan running", "BC060208000055"),
        ("Purple running", "BC060208000055"),
        ("White running", "BC060208000055"),
        ("7 colours running", "BC060208000055"),
        ("Blue-green-red running", "BC060208000055"),
        ("Purple-cyan-yellow running", "BC060208000055"),
    ]),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _color_swatch(rgb: tuple[int, int, int], size: int = 16) -> QIcon:
    """Small rounded square of the given colour, used as a button icon."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setBrush(QColor(*rgb))
    painter.setPen(QColor(0, 0, 0, 70))
    painter.drawRoundedRect(0, 0, size - 1, size - 1, 3.0, 3.0)
    painter.end()
    return QIcon(pixmap)


class CollapsibleSection(QWidget):
    """A stack of these builds the Light-modes picker.

    The header is a button; clicking it shows or hides the content
    widget. Only the header is visible when collapsed, so six
    categories fit in a small space.
    """

    def __init__(self, title: str, content: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = title
        self._content = content
        self._expanded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.btn_header = QPushButton(f"\u25b8 {title}")
        # This property is what theme.py keys on for the section header
        # colouring. Without it the header just gets the plain button
        # style and the arrow vanishes into the group box border.
        self.btn_header.setProperty("sectionHeader", True)
        self.btn_header.setCheckable(False)
        self.btn_header.clicked.connect(self.toggle)
        layout.addWidget(self.btn_header)

        layout.addWidget(content)
        content.setVisible(False)

    def toggle(self) -> None:
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        arrow = "\u25be" if self._expanded else "\u25b8"
        self.btn_header.setText(f"{arrow} {self._title}")


class StripPreviewRow(QWidget):
    """One row: strip name on the left, capsules on the right."""

    def __init__(self, address: str, name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.address = address

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.lbl_name = QLabel(name)
        self.lbl_name.setMinimumWidth(140)
        self.lbl_name.setMaximumWidth(180)
        self.lbl_name.setStyleSheet("color: #A1A1AA; font-size: 11px;")
        layout.addWidget(self.lbl_name)

        self.preview = StripPreview()
        self.preview.setMinimumHeight(44)
        layout.addWidget(self.preview, stretch=1)

    def set_color(self, r: int, g: int, b: int, brightness: float, label: str) -> None:
        self.preview.set_color(r, g, b, brightness, label)


class ButtonDialog(QDialog):
    """Dialog for creating or editing a user remote button."""

    def __init__(
        self, parent: QWidget, label="", hex_cmd="", group="Ungrouped", frames=""
    ) -> None:
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
        frames = [
            line.strip()
            for line in self.edit_frames.toPlainText().splitlines()
            if line.strip()
        ]
        return {
            "label": self.edit_label.text().strip() or "Button",
            "hex": self.edit_hex.text().strip(),
            "group": self.edit_group.text().strip() or "Ungrouped",
            "frames": frames,
            "delay": self.spin_delay.value(),
        }


# ---------------------------------------------------------------------------
# The tab
# ---------------------------------------------------------------------------


class RemoteTab(QWidget):
    def __init__(self, ctx: AppContext, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.ctx = ctx
        self.rgb = tuple(ctx.settings.last_color)

        #: Per-session override for the Light-mode hexes. Right-click a
        #: mode button to replace its frame with one you captured.
        self._light_mode_overrides: dict[str, str] = {}

        #: Multi-strip preview rows keyed by device address.
        self._preview_rows: dict[str, StripPreviewRow] = {}

        layout = QHBoxLayout(self)

        # ------------------------------------------------------------------
        # Left: colour + brightness + light modes + multi-strip preview
        # ------------------------------------------------------------------
        left = QVBoxLayout()

        # Power buttons
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

        # Colour wheel + presets
        wheel_box = QGroupBox("Colour")
        wheel_layout = QVBoxLayout(wheel_box)
        self.wheel = ColorWheel()
        self.wheel.set_rgb(*self.rgb)
        self.wheel.color_changed.connect(self._on_wheel)
        wheel_layout.addWidget(self.wheel, stretch=1)

        preset_grid = QGridLayout()
        preset_grid.setHorizontalSpacing(6)
        preset_grid.setVerticalSpacing(6)
        for index, (name, rgb) in enumerate(PRESETS):
            button = QPushButton(name)
            button.setIcon(_color_swatch(rgb))
            button.setIconSize(QSize(16, 16))
            button.clicked.connect(lambda _=False, c=rgb: self._apply_color(*c))
            preset_grid.addWidget(button, index // 5, index % 5)
        wheel_layout.addLayout(preset_grid)
        left.addWidget(wheel_box)

        # Brightness slider
        bright_box = QGroupBox("Brightness")
        bright_layout = QVBoxLayout(bright_box)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(ctx.settings.last_brightness)
        self.slider.valueChanged.connect(self._on_slider_preview)
        self.slider.sliderReleased.connect(self._on_brightness)

        self.lbl_brightness = QLabel(f"{self.slider.value()}%")
        self.lbl_brightness.setMinimumWidth(48)
        row = QHBoxLayout()
        row.addWidget(self.slider, stretch=1)
        row.addWidget(self.lbl_brightness)
        bright_layout.addLayout(row)

        self.lbl_clamp = QLabel("")
        self.lbl_clamp.setWordWrap(True)
        bright_layout.addWidget(self.lbl_clamp)
        left.addWidget(bright_box)

        # --- Light modes -------------------------------------------------
        light_modes_box = QGroupBox("Light modes")
        light_modes_layout = QVBoxLayout(light_modes_box)

        note = QLabel(
            "The strip's own built-in effects. Right-click any mode to "
            "override its frame with one captured from the vendor app."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #71717A; font-size: 11px;")
        light_modes_layout.addWidget(note)

        self._light_modes_scroll = QScrollArea()
        self._light_modes_scroll.setWidgetResizable(True)
        self._light_modes_scroll.setMaximumHeight(300)
        self._build_light_modes()
        light_modes_layout.addWidget(self._light_modes_scroll)
        left.addWidget(light_modes_box)

        # --- Multi-strip preview -----------------------------------------
        self.preview_container = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_layout.setSpacing(2)
        left.addWidget(self.preview_container)

        layout.addLayout(left, stretch=3)

        # ------------------------------------------------------------------
        # Right: remote buttons (profile-based)
        # ------------------------------------------------------------------
        right = QVBoxLayout()
        profile_row = QHBoxLayout()
        self.combo_profile = QComboBox()
        self.combo_profile.currentIndexChanged.connect(lambda _: self.refresh_buttons())
        for label, slot in (
            ("New", self._new_profile),
            ("Rename", self._rename_profile),
            ("Delete", self._delete_profile),
        ):
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

        # --- initial paint -----------------------------------------------
        self.refresh_profiles()
        self._refresh_clamp_notice()
        self._on_slider_preview(self.slider.value())
        self._refresh_preview_strips()

        # The preview rows follow the main window's strip selector, which
        # can change at any time, so poll a few times per second.
        self._preview_timer = QTimer(self)
        self._preview_timer.timeout.connect(self._refresh_preview_strips)
        self._preview_timer.start(750)

    # ------------------------------------------------------------------
    # Light modes
    # ------------------------------------------------------------------

    def _build_light_modes(self) -> None:
        container = QWidget()
        stack = QVBoxLayout(container)
        stack.setContentsMargins(0, 0, 0, 0)
        stack.setSpacing(2)

        for category, modes in LIGHT_MODE_CATEGORIES:
            content = QWidget()
            grid = QGridLayout(content)
            grid.setContentsMargins(6, 6, 6, 6)
            grid.setHorizontalSpacing(6)
            grid.setVerticalSpacing(6)

            for index, (mode_name, mode_hex) in enumerate(modes):
                btn = QPushButton(mode_name)
                btn.setToolTip(
                    f"Sends {mode_hex}\n"
                    "Right-click to override with a captured frame."
                )
                btn.setContextMenuPolicy(Qt.CustomContextMenu)
                btn.clicked.connect(
                    lambda _=False, n=mode_name, h=mode_hex: self._on_light_mode_clicked(
                        n, h
                    )
                )
                btn.customContextMenuRequested.connect(
                    lambda pos, n=mode_name, h=mode_hex, w=btn: self._on_light_mode_context_menu(
                        w, pos, n, h
                    )
                )
                # Two columns keeps the buttons wide enough to read.
                grid.addWidget(btn, index // 2, index % 2)

            section = CollapsibleSection(category, content)
            stack.addWidget(section)

        stack.addStretch()
        self._light_modes_scroll.setWidget(container)

    def _on_light_mode_clicked(self, mode_name: str, default_hex: str) -> None:
        frame = self._light_mode_overrides.get(mode_name, default_hex)
        self.ctx.db.add_command(frame, label=f"light:{mode_name}")
        targets = self.ctx.resolve_targets()
        self.ctx.log("send", f"Light mode '{mode_name}' -> {frame}")
        self.ctx.run(
            self.ctx.ble.send_hex_all(frame, f"light:{mode_name}", addresses=targets)
        )

    def _on_light_mode_context_menu(
        self, widget: QWidget, pos, mode_name: str, default_hex: str
    ) -> None:
        menu = QMenu(self)
        action_edit = menu.addAction("Edit hex…")
        current_override = mode_name in self._light_mode_overrides
        action_reset = menu.addAction("Reset to default")
        action_reset.setEnabled(current_override)
        chosen = menu.exec(widget.mapToGlobal(pos))
        if chosen == action_edit:
            self._edit_light_mode_hex(mode_name, default_hex)
        elif chosen == action_reset:
            self._light_mode_overrides.pop(mode_name, None)
            self.ctx.log("info", f"Light mode '{mode_name}' reset to default")

    def _edit_light_mode_hex(self, mode_name: str, default_hex: str) -> None:
        current = self._light_mode_overrides.get(mode_name, default_hex)
        text, ok = QInputDialog.getText(
            self,
            "Edit light mode",
            f"Hex frame for '{mode_name}':",
            text=current,
        )
        if not ok:
            return
        text = text.strip().upper()
        if not text:
            return
        cleaned = "".join(c for c in text if c in "0123456789ABCDEFabcdef")
        if len(cleaned) != len(text) or len(cleaned) % 2:
            QMessageBox.warning(
                self,
                "Invalid hex",
                "Frame must be an even number of hex digits (0-9, A-F).",
            )
            return
        self._light_mode_overrides[mode_name] = cleaned
        self.ctx.log("info", f"Light mode '{mode_name}' set to {cleaned}")

    # ------------------------------------------------------------------
    # Colour + brightness
    # ------------------------------------------------------------------

    def _clamped_brightness(self, slider_value: int | None = None) -> float:
        raw = (self.slider.value() if slider_value is None else slider_value) / 100.0
        return self.ctx.settings.clamp_brightness(raw)

    def _refresh_clamp_notice(self) -> None:
        lo = self.ctx.settings.brightness_min
        hi = self.ctx.settings.brightness_max
        if lo <= 0 and hi >= 100:
            self.lbl_clamp.setText("")
        else:
            self.lbl_clamp.setText(f"Clamped to {lo}%-{hi}% by the Options tab.")

    def sync_clamp_notice(self) -> None:
        """Called by the main window when Options changes the brightness range."""
        self._refresh_clamp_notice()
        self._on_slider_preview(self.slider.value())

    def _on_wheel(self, r: int, g: int, b: int) -> None:
        self._apply_color(r, g, b)

    def _apply_color(self, r: int, g: int, b: int) -> None:
        self.rgb = (r, g, b)
        self.ctx.settings.last_color = [r, g, b]
        brightness = self._clamped_brightness()
        self.wheel.set_rgb(r, g, b)
        self._update_previews()
        self.ctx.db.add_command(encode_color(r, g, b), label="color")
        targets = self.ctx.resolve_targets()
        self.ctx.run(self.ctx.ble.set_color(r, g, b, brightness, addresses=targets))

    def _on_slider_preview(self, value: int) -> None:
        """Live update while dragging - preview only, no BLE traffic."""
        self.lbl_brightness.setText(f"{value}%")
        self._update_previews()

    def _on_brightness(self) -> None:
        value = self.slider.value()
        self.ctx.settings.last_brightness = value
        clamped = self._clamped_brightness(value)
        self._update_previews()
        self._send(encode_brightness(clamped), "brightness")

    def _send(self, hex_cmd: str, label: str) -> None:
        self.ctx.db.add_command(hex_cmd, label=label)
        targets = self.ctx.resolve_targets()
        self.ctx.run(self.ctx.ble.send_hex_all(hex_cmd, label, addresses=targets))

    # ------------------------------------------------------------------
    # Multi-strip preview
    # ------------------------------------------------------------------

    def _refresh_preview_strips(self) -> None:
        targets = self.ctx.resolve_targets()
        if targets is None:
            targets = self.ctx.ble.connected_addresses()

        # Remove stale preview rows.
        for address in list(self._preview_rows.keys()):
            if address not in targets:
                row = self._preview_rows.pop(address)
                self.preview_layout.removeWidget(row)
                row.deleteLater()

        # Add rows for newly-targeted strips.
        for address in targets:
            if address in self._preview_rows:
                continue
            state = self.ctx.ble.devices.get(address)
            name = (state.name if state is not None else None) or address[-8:]
            if len(name) > 22:
                name = name[:20] + "…"
            row = StripPreviewRow(address, name)
            self._preview_rows[address] = row
            self.preview_layout.addWidget(row)

        self._update_previews()

    def _update_previews(self) -> None:
        r, g, b = self.rgb
        brightness = self._clamped_brightness()
        label = f"rgb({r},{g},{b})"
        for row in self._preview_rows.values():
            row.set_color(r, g, b, brightness, label)

    # ------------------------------------------------------------------
    # Profiles
    # ------------------------------------------------------------------

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
            self,
            "Delete profile",
            f"Delete '{self.combo_profile.currentText()}' and its buttons?",
        )
        if confirm == QMessageBox.Yes:
            self.ctx.db.delete_profile(profile_id)
            self.refresh_profiles()

    # ------------------------------------------------------------------
    # Remote buttons
    # ------------------------------------------------------------------

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
                widget = QPushButton(button.label + (" >" if button.is_macro else ""))
                widget.setToolTip(
                    button.hex
                    if not button.is_macro
                    else f"{len(button.macro_frames)} frames"
                )
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
            self.ctx.log(
                "send",
                f"Macro '{button.label}' ({len(button.macro_frames)} frames)",
            )
            targets = self.ctx.resolve_targets()
            self.ctx.run(
                self.ctx.ble.run_macro(
                    button.macro_frames,
                    button.macro_delay_ms,
                    addresses=targets,
                )
            )
        else:
            self._send(button.hex, button.label)

    def _context_menu(self, widget: QWidget, pos, button) -> None:
        menu = QMenu(self)
        action_edit = menu.addAction("Edit...")
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
            button.id,
            values["label"],
            values["hex"],
            values["group"],
            values["frames"],
            values["delay"],
        )
        self.refresh_buttons()
