#!/usr/bin/env python3
"""
yweinHEX - Next-Gen Hex & Binary Inspector
Author: ywein0x
"""
import sys
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from src.ui.main_window import MainWindow
from src.ui.styles import DARK_THEME
from src.core.elevation import is_admin, enable_debug_privilege

def main():
    if is_admin():
        enable_debug_privilege()

    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("yweinHEX")
    app.setOrganizationName("ywein0x")
    app.setStyleSheet(DARK_THEME)

    # Check CLI argument for direct file opening (e.g. `python main.py target.exe`)
    initial_file = None
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        initial_file = sys.argv[1]

    window = MainWindow(initial_path=initial_file)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
