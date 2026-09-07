"""
yweinHEX Cyber-Dark Theme & Styling
Designed for high-contrast readability, sleek aesthetics, and responsive feel.
"""

DARK_THEME = """
QWidget {
    background-color: #0d1117;
    color: #c9d1d9;
    font-size: 10pt;
    selection-background-color: #1f6feb;
    selection-color: #ffffff;
}

/* ToolBar & MenuBar */
QMenuBar {
    background-color: #161b22;
    color: #c9d1d9;
    border-bottom: 1px solid #30363d;
    padding: 2px 4px;
}
QMenuBar::item {
    background: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #21262d;
    color: #58a6ff;
}
QMenu {
    background-color: #161b22;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #1f6feb;
    color: #ffffff;
}
QMenu::separator {
    height: 1px;
    background-color: #30363d;
    margin: 4px 6px;
}

/* ToolBar */
QToolBar {
    background-color: #161b22;
    border-bottom: 1px solid #30363d;
    spacing: 6px;
    padding: 4px 6px;
}
QToolButton {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 5px;
    padding: 5px 10px;
    font-weight: 500;
}
QToolButton:hover {
    background-color: #30363d;
    color: #58a6ff;
    border-color: #58a6ff;
}
QToolButton:pressed {
    background-color: #1f6feb;
    color: #ffffff;
}

/* PushButtons */
QPushButton {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 5px 12px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #30363d;
    color: #58a6ff;
    border-color: #58a6ff;
}
QPushButton:pressed {
    background-color: #1f6feb;
    color: #ffffff;
}
QPushButton#primaryButton {
    background-color: #238636;
    color: #ffffff;
    border: 1px solid #2ea043;
}
QPushButton#primaryButton:hover {
    background-color: #2ea043;
}
QPushButton#accentButton {
    background-color: #8957e5;
    color: #ffffff;
    border: 1px solid #a371f7;
}
QPushButton#accentButton:hover {
    background-color: #a371f7;
}

/* LineEdit & TextEdit */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #0d1117;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 5px 8px;
    font-family: "Consolas", monospace;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #58a6ff;
    background-color: #0d1117;
}

/* TableView & TreeView */
QTableView, QTableWidget, QTreeView, QTreeWidget, QListWidget {
    background-color: #0d1117;
    color: #c9d1d9;
    gridline-color: #21262d;
    border: 1px solid #30363d;
    border-radius: 6px;
    alternate-background-color: #161b22;
    selection-background-color: #1f6feb;
    selection-color: #ffffff;
}
QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    padding: 5px 8px;
    border: none;
    border-bottom: 1px solid #30363d;
    border-right: 1px solid #21262d;
    font-weight: bold;
}
QHeaderView::section:hover {
    background-color: #21262d;
    color: #58a6ff;
}

/* DockWidget & GroupBox */
QDockWidget {
    color: #c9d1d9;
    font-weight: bold;
}
QDockWidget::title {
    background-color: #161b22;
    padding: 6px 10px;
    border-bottom: 1px solid #30363d;
}
QGroupBox {
    border: 1px solid #30363d;
    border-radius: 6px;
    margin-top: 18px;
    padding: 10px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: #58a6ff;
}

/* ScrollBars */
QScrollBar:vertical {
    background: #0d1117;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #30363d;
    min-height: 25px;
    border-radius: 6px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background: #58a6ff;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #0d1117;
    height: 12px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background: #30363d;
    min-width: 25px;
    border-radius: 6px;
    margin: 2px;
}
QScrollBar::handle:horizontal:hover {
    background: #58a6ff;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* StatusBar */
QStatusBar {
    background-color: #161b22;
    color: #8b949e;
    border-top: 1px solid #30363d;
    font-family: "Consolas", monospace;
}
QStatusBar QLabel {
    padding: 2px 8px;
}

/* Splitter */
QSplitter::handle {
    background-color: #21262d;
}
QSplitter::handle:hover {
    background-color: #58a6ff;
}
"""
