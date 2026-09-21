# Original Path: aymashtain/ui/theme.py

"""Qt stylesheet for the dark (default) and light themes.

Round 3 follow-up (Session 13)
------------------------------
* **Scroll-area and tab-page backgrounds fixed.** The Options tab was
  rendering light in dark mode because ``QScrollArea``'s viewport has its
  own palette role that ignores the parent QTabWidget pane. Same bug hit
  the Remote tab's right panel. Both are now transparent, so the pane
  background shows through.
* **QTabWidget pane children.** ``QTabWidget::pane > QWidget`` gets an
  explicit background so individual tab pages never fall back to the OS
  default.
* **QGroupBox is now transparent** so it inherits whatever its parent
  provides instead of showing a light wash behind its border.

Round 3 (original) kept
-----------------------
* Section-header styles for the collapsible Light-modes categories in
  the Remote tab.
* Camera tab borders are set by the widget itself, not here.

Round 2 (kept)
--------------
* Dark-mode highlights softened (indigo-800 tabs, indigo-700 accent
  buttons, zinc-300 slider handle).
* Menu audit: separators, disabled items, pressed menu-bar items have
  explicit rules in both themes.
* Remote tab's preset buttons use icons, not inline stylesheets.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Dark theme
# ---------------------------------------------------------------------------

DARK = """
QMainWindow, QDialog { background-color: #0E0E12; }
QWidget { color: #E4E4E7; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; }

/* --- tabs ------------------------------------------------------------- */
QTabWidget::pane { border: 1px solid #27272A; background: #131318; border-radius: 10px; }
QTabWidget::pane > QWidget { background: #131318; }
QTabBar::tab {
    background: #1B1B21; border: 1px solid #27272A; padding: 8px 16px; margin-right: 4px;
    border-top-left-radius: 8px; border-top-right-radius: 8px; color: #A1A1AA;
}
QTabBar::tab:selected {
    background: #3730A3; color: #F4F4F5; font-weight: 600; border-color: #4338CA;
}
QTabBar::tab:hover:!selected { background: #27272A; color: #E4E4E7; }

/* --- scrollable containers ------------------------------------------- */
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget { background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }

/* --- buttons ---------------------------------------------------------- */
QPushButton {
    background: #1F1F26; border: 1px solid #33333C; border-radius: 8px;
    padding: 7px 14px; font-weight: 600; color: #E4E4E7;
}
QPushButton:hover { background: #2C2C36; border-color: #4F46E5; }
QPushButton:pressed { background: #131318; }
QPushButton:disabled { color: #52525B; border-color: #27272A; background: #17171D; }

QPushButton[accent="true"] {
    background: #4338CA; border-color: #4F46E5; color: #FFFFFF;
}
QPushButton[accent="true"]:hover { background: #4F46E5; border-color: #6366F1; }
QPushButton[accent="true"]:pressed { background: #3730A3; }
QPushButton[accent="true"]:disabled { background: #2A2A33; color: #52525B; border-color: #33333C; }

QPushButton[danger="true"] {
    background: #7F1D1D; border-color: #B91C1C; color: #FEE2E2;
}
QPushButton[danger="true"]:hover { background: #991B1B; }
QPushButton[danger="true"]:disabled { background: #3B1414; color: #7F1D1D; border-color: #4C1D1D; }

/* --- group boxes ------------------------------------------------------ */
QGroupBox {
    background: transparent;
    border: 1px solid #27272A; border-radius: 10px; margin-top: 16px;
    font-weight: 600; padding: 12px;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #818CF8; }

/* --- section headers (Light modes / collapsible) --------------------- */
QPushButton[sectionHeader="true"] {
    background: #1B1B21;
    border: 1px solid #27272A;
    border-radius: 6px;
    padding: 6px 10px;
    text-align: left;
    font-weight: 600;
    color: #C7D2FE;
}
QPushButton[sectionHeader="true"]:hover {
    background: #27272A;
    border-color: #4338CA;
}

/* --- inputs ----------------------------------------------------------- */
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #0B0B0F; border: 1px solid #27272A; border-radius: 6px; padding: 5px;
    color: #E4E4E7;
    selection-background-color: #4338CA;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: #4F46E5; }
QTextEdit, QPlainTextEdit { font-family: 'Consolas', 'JetBrains Mono', monospace; font-size: 12px; }
QComboBox::drop-down { border: 0; width: 22px; }
QComboBox QAbstractItemView {
    background: #17171D; border: 1px solid #27272A; selection-background-color: #3730A3;
    color: #E4E4E7;
}

/* --- lists / tables --------------------------------------------------- */
QListWidget, QTableWidget, QTreeWidget {
    background: #0B0B0F; border: 1px solid #27272A; border-radius: 8px;
    alternate-background-color: #111117; gridline-color: #27272A;
    color: #E4E4E7;
}
QListWidget::item:selected, QTableWidget::item:selected, QTreeWidget::item:selected {
    background: #3730A3; color: #F4F4F5;
}
QHeaderView::section { background: #1B1B21; border: 0; padding: 6px; color: #A1A1AA; }

/* --- sliders ---------------------------------------------------------- */
QSlider::groove:horizontal { height: 6px; background: #27272A; border-radius: 3px; }
QSlider::sub-page:horizontal { background: #4F46E5; border-radius: 3px; }
QSlider::handle:horizontal {
    background: #D4D4D8; width: 16px; margin: -6px 0; border-radius: 8px;
}
QSlider::handle:horizontal:hover { background: #FAFAFA; }

/* --- progress --------------------------------------------------------- */
QProgressBar {
    border: 1px solid #27272A; border-radius: 6px; text-align: center;
    background: #0B0B0F; color: #E4E4E7;
}
QProgressBar::chunk { background: #4338CA; border-radius: 5px; }

/* --- statusbar -------------------------------------------------------- */
QStatusBar { color: #A1A1AA; background: #0E0E12; }
QStatusBar::item { border: 0; }

/* --- menu bar + menus ------------------------------------------------- */
QMenuBar { background: #0E0E12; color: #E4E4E7; }
QMenuBar::item { padding: 6px 12px; background: transparent; border-radius: 6px; }
QMenuBar::item:selected { background: #27272A; }
QMenuBar::item:pressed { background: #33333C; }

QMenu { background: #17171D; border: 1px solid #27272A; padding: 4px; color: #E4E4E7; }
QMenu::item { padding: 6px 22px; border-radius: 6px; }
QMenu::item:selected { background: #3730A3; color: #FFFFFF; }
QMenu::item:disabled { color: #52525B; }
QMenu::separator { height: 1px; background: #27272A; margin: 4px 8px; }
QMenu::indicator { width: 14px; height: 14px; }

/* --- tooltips --------------------------------------------------------- */
QToolTip {
    background: #17171D; color: #E4E4E7; border: 1px solid #4338CA;
    padding: 4px 6px; border-radius: 6px;
}

/* --- scrollbars ------------------------------------------------------- */
QScrollBar:vertical { background: #0B0B0F; width: 12px; margin: 0; }
QScrollBar:horizontal { background: #0B0B0F; height: 12px; margin: 0; }
QScrollBar::handle { background: #33333C; border-radius: 6px; min-height: 28px; min-width: 28px; }
QScrollBar::handle:hover { background: #4338CA; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* --- checkboxes / radios --------------------------------------------- */
QCheckBox, QRadioButton { background: transparent; color: #E4E4E7; }
QCheckBox::indicator, QRadioButton::indicator { width: 15px; height: 15px; }
QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {
    border: 1px solid #52525B; border-radius: 4px; background: #0B0B0F;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    border: 1px solid #4F46E5; border-radius: 4px; background: #4338CA;
}
QRadioButton::indicator:unchecked { border-radius: 8px; }
QRadioButton::indicator:checked { border-radius: 8px; }
"""

# ---------------------------------------------------------------------------
# Light theme
# ---------------------------------------------------------------------------

LIGHT = """
QMainWindow, QDialog { background-color: #F4F4F5; }
QWidget { color: #18181B; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; }

/* --- tabs ------------------------------------------------------------- */
QTabWidget::pane { border: 1px solid #D4D4D8; background: #FFFFFF; border-radius: 10px; }
QTabWidget::pane > QWidget { background: #FFFFFF; }
QTabBar::tab {
    background: #E4E4E7; border: 1px solid #D4D4D8; padding: 8px 16px; margin-right: 4px;
    border-top-left-radius: 8px; border-top-right-radius: 8px;
}
QTabBar::tab:selected { background: #4F46E5; color: #FFFFFF; font-weight: 600; }
QTabBar::tab:hover:!selected { background: #D4D4D8; }

/* --- scrollable containers ------------------------------------------- */
QScrollArea { background: transparent; border: none; }
QScrollArea > QWidget { background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }

/* --- buttons ---------------------------------------------------------- */
QPushButton {
    background: #FFFFFF; border: 1px solid #D4D4D8; border-radius: 8px;
    padding: 7px 14px; font-weight: 600; color: #18181B;
}
QPushButton:hover { border-color: #6366F1; background: #FAFAFA; }
QPushButton:pressed { background: #E4E4E7; }
QPushButton:disabled { color: #A1A1AA; border-color: #E4E4E7; background: #FAFAFA; }
QPushButton[accent="true"] { background: #4F46E5; color: #FFFFFF; border-color: #4338CA; }
QPushButton[accent="true"]:hover { background: #4338CA; }
QPushButton[accent="true"]:disabled { background: #C7D2FE; border-color: #A5B4FC; color: #FFFFFF; }
QPushButton[danger="true"] { background: #DC2626; color: #FFFFFF; border-color: #B91C1C; }
QPushButton[danger="true"]:hover { background: #B91C1C; }

/* --- group boxes ------------------------------------------------------ */
QGroupBox {
    background: transparent;
    border: 1px solid #D4D4D8; border-radius: 10px; margin-top: 16px;
    font-weight: 600; padding: 12px;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #4338CA; }

/* --- section headers (Light modes / collapsible) --------------------- */
QPushButton[sectionHeader="true"] {
    background: #EEF2FF;
    border: 1px solid #C7D2FE;
    border-radius: 6px;
    padding: 6px 10px;
    text-align: left;
    font-weight: 600;
    color: #3730A3;
}
QPushButton[sectionHeader="true"]:hover {
    background: #E0E7FF;
    border-color: #6366F1;
}

/* --- inputs ----------------------------------------------------------- */
QTextEdit, QPlainTextEdit { font-family: 'Consolas', monospace; font-size: 12px; background: #FFFFFF; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #FFFFFF; border: 1px solid #D4D4D8; border-radius: 6px; padding: 5px;
    color: #18181B;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border-color: #6366F1; }
QComboBox QAbstractItemView {
    background: #FFFFFF; border: 1px solid #D4D4D8; selection-background-color: #4F46E5;
    selection-color: #FFFFFF; color: #18181B;
}

/* --- lists / tables --------------------------------------------------- */
QListWidget, QTableWidget, QTreeWidget {
    background: #FFFFFF; border: 1px solid #D4D4D8; border-radius: 8px;
    gridline-color: #E4E4E7; alternate-background-color: #FAFAFA;
    color: #18181B;
}
QListWidget::item:selected, QTableWidget::item:selected, QTreeWidget::item:selected {
    background: #4F46E5; color: #FFFFFF;
}
QHeaderView::section { background: #E4E4E7; border: 0; padding: 6px; color: #18181B; }

/* --- sliders ---------------------------------------------------------- */
QSlider::groove:horizontal { height: 6px; background: #D4D4D8; border-radius: 3px; }
QSlider::sub-page:horizontal { background: #4F46E5; border-radius: 3px; }
QSlider::handle:horizontal { background: #18181B; width: 16px; margin: -6px 0; border-radius: 8px; }
QSlider::handle:horizontal:hover { background: #000000; }

/* --- progress --------------------------------------------------------- */
QProgressBar {
    border: 1px solid #D4D4D8; border-radius: 6px; text-align: center;
    background: #FFFFFF; color: #18181B;
}
QProgressBar::chunk { background: #4F46E5; border-radius: 5px; }

/* --- statusbar -------------------------------------------------------- */
QStatusBar { color: #52525B; background: #F4F4F5; }
QStatusBar::item { border: 0; }

/* --- menu bar + menus ------------------------------------------------- */
QMenuBar { background: #F4F4F5; }
QMenuBar::item { padding: 6px 12px; background: transparent; border-radius: 6px; }
QMenuBar::item:selected { background: #E4E4E7; }
QMenuBar::item:pressed { background: #D4D4D8; }

QMenu { background: #FFFFFF; border: 1px solid #D4D4D8; padding: 4px; }
QMenu::item { padding: 6px 22px; border-radius: 6px; }
QMenu::item:selected { background: #4F46E5; color: #FFFFFF; }
QMenu::item:disabled { color: #A1A1AA; }
QMenu::separator { height: 1px; background: #E4E4E7; margin: 4px 8px; }
QMenu::indicator { width: 14px; height: 14px; }

/* --- tooltips --------------------------------------------------------- */
QToolTip {
    background: #FFFFFF; color: #18181B; border: 1px solid #D4D4D8;
    padding: 4px 6px; border-radius: 6px;
}

/* --- scrollbars ------------------------------------------------------- */
QScrollBar:vertical { background: #F4F4F5; width: 12px; margin: 0; }
QScrollBar:horizontal { background: #F4F4F5; height: 12px; margin: 0; }
QScrollBar::handle { background: #C7C7CC; border-radius: 6px; min-height: 28px; min-width: 28px; }
QScrollBar::handle:hover { background: #A1A1AA; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

/* --- checkboxes / radios --------------------------------------------- */
QCheckBox, QRadioButton { background: transparent; color: #18181B; }
QCheckBox::indicator, QRadioButton::indicator { width: 15px; height: 15px; }
QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {
    border: 1px solid #A1A1AA; border-radius: 4px; background: #FFFFFF;
}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    border: 1px solid #4338CA; border-radius: 4px; background: #4F46E5;
}
QRadioButton::indicator:unchecked { border-radius: 8px; }
QRadioButton::indicator:checked { border-radius: 8px; }
"""


def stylesheet(dark: bool) -> str:
    """Return the stylesheet for the given theme. No state, pure function."""
    return DARK if dark else LIGHT
