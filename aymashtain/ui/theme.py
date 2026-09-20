"""Qt stylesheet for the dark (default) and light themes."""

from __future__ import annotations

DARK = """
QMainWindow, QDialog { background-color: #0E0E12; }
QWidget { color: #E4E4E7; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; }
QTabWidget::pane { border: 1px solid #27272A; background: #131318; border-radius: 10px; }
QTabBar::tab {
    background: #1B1B21; border: 1px solid #27272A; padding: 8px 16px; margin-right: 4px;
    border-top-left-radius: 8px; border-top-right-radius: 8px; color: #A1A1AA;
}
QTabBar::tab:selected { background: #4F46E5; color: #FFFFFF; font-weight: 600; border-color: #6366F1; }
QTabBar::tab:hover:!selected { background: #27272A; color: #E4E4E7; }
QPushButton {
    background: #1F1F26; border: 1px solid #33333C; border-radius: 8px;
    padding: 7px 14px; font-weight: 600;
}
QPushButton:hover { background: #2C2C36; border-color: #6366F1; }
QPushButton:disabled { color: #52525B; border-color: #27272A; }
QPushButton[accent="true"] { background: #4F46E5; border-color: #6366F1; color: #FFFFFF; }
QPushButton[accent="true"]:hover { background: #6366F1; }
QPushButton[danger="true"] { background: #7F1D1D; border-color: #B91C1C; color: #FEE2E2; }
QGroupBox {
    border: 1px solid #27272A; border-radius: 10px; margin-top: 16px;
    font-weight: 600; padding: 12px;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #818CF8; }
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #0B0B0F; border: 1px solid #27272A; border-radius: 6px; padding: 5px;
    selection-background-color: #4F46E5;
}
QTextEdit, QPlainTextEdit { font-family: 'Consolas', 'JetBrains Mono', monospace; font-size: 12px; }
QListWidget, QTableWidget, QTreeWidget {
    background: #0B0B0F; border: 1px solid #27272A; border-radius: 8px;
    alternate-background-color: #111117; gridline-color: #27272A;
}
QHeaderView::section { background: #1B1B21; border: 0; padding: 6px; color: #A1A1AA; }
QSlider::groove:horizontal { height: 6px; background: #27272A; border-radius: 3px; }
QSlider::sub-page:horizontal { background: #6366F1; border-radius: 3px; }
QSlider::handle:horizontal {
    background: #FAFAFA; width: 16px; margin: -6px 0; border-radius: 8px;
}
QProgressBar { border: 1px solid #27272A; border-radius: 6px; text-align: center; background: #0B0B0F; }
QProgressBar::chunk { background: #4F46E5; border-radius: 5px; }
QStatusBar { color: #A1A1AA; background: #0E0E12; }
QMenuBar { background: #0E0E12; color: #E4E4E7; }
QMenuBar::item { padding: 6px 12px; background: transparent; }
QMenuBar::item:selected { background: #27272A; border-radius: 6px; }
QMenu { background: #17171D; border: 1px solid #27272A; padding: 4px; }
QMenu::item { padding: 6px 22px; border-radius: 6px; }
QMenu::item:selected { background: #4F46E5; color: #FFFFFF; }
QToolTip { background: #17171D; color: #E4E4E7; border: 1px solid #4F46E5; padding: 4px; }
QScrollBar:vertical { background: #0B0B0F; width: 12px; margin: 0; }
QScrollBar:horizontal { background: #0B0B0F; height: 12px; margin: 0; }
QScrollBar::handle { background: #33333C; border-radius: 6px; min-height: 28px; min-width: 28px; }
QScrollBar::handle:hover { background: #4F46E5; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QCheckBox::indicator, QRadioButton::indicator { width: 15px; height: 15px; }
QCheckBox::indicator:unchecked { border: 1px solid #52525B; border-radius: 4px; background: #0B0B0F; }
QCheckBox::indicator:checked { border: 1px solid #6366F1; border-radius: 4px; background: #4F46E5; }
"""

LIGHT = """
QMainWindow, QDialog { background-color: #F4F4F5; }
QWidget { color: #18181B; font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; }
QTabWidget::pane { border: 1px solid #D4D4D8; background: #FFFFFF; border-radius: 10px; }
QTabBar::tab {
    background: #E4E4E7; border: 1px solid #D4D4D8; padding: 8px 16px; margin-right: 4px;
    border-top-left-radius: 8px; border-top-right-radius: 8px;
}
QTabBar::tab:selected { background: #4F46E5; color: #FFFFFF; font-weight: 600; }
QPushButton {
    background: #FFFFFF; border: 1px solid #D4D4D8; border-radius: 8px;
    padding: 7px 14px; font-weight: 600;
}
QPushButton:hover { border-color: #6366F1; }
QPushButton[accent="true"] { background: #4F46E5; color: #FFFFFF; border-color: #4338CA; }
QPushButton[danger="true"] { background: #DC2626; color: #FFFFFF; border-color: #B91C1C; }
QGroupBox {
    border: 1px solid #D4D4D8; border-radius: 10px; margin-top: 16px; font-weight: 600; padding: 12px;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #4338CA; }
QTextEdit, QPlainTextEdit { font-family: 'Consolas', monospace; font-size: 12px; background: #FFFFFF; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #FFFFFF; border: 1px solid #D4D4D8; border-radius: 6px; padding: 5px;
}
QListWidget, QTableWidget, QTreeWidget {
    background: #FFFFFF; border: 1px solid #D4D4D8; border-radius: 8px; gridline-color: #E4E4E7;
}
QHeaderView::section { background: #E4E4E7; border: 0; padding: 6px; }
QSlider::groove:horizontal { height: 6px; background: #D4D4D8; border-radius: 3px; }
QSlider::sub-page:horizontal { background: #4F46E5; border-radius: 3px; }
QSlider::handle:horizontal { background: #18181B; width: 16px; margin: -6px 0; border-radius: 8px; }
QProgressBar { border: 1px solid #D4D4D8; border-radius: 6px; text-align: center; background: #FFFFFF; }
QProgressBar::chunk { background: #4F46E5; border-radius: 5px; }
QMenuBar { background: #F4F4F5; }
QMenu { background: #FFFFFF; border: 1px solid #D4D4D8; }
QMenu::item:selected { background: #4F46E5; color: #FFFFFF; }
"""


def stylesheet(dark: bool) -> str:
    return DARK if dark else LIGHT
