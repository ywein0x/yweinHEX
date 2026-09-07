import re
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QRadioButton, QButtonGroup, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox
)

class SearchDialog(QDialog):
    """
    Search dialog supporting Hex bytes, Text (ASCII/UTF-8), and Regex.
    """
    jump_requested = Signal(int)

    def __init__(self, data_source, current_offset: int = 0, parent=None):
        super().__init__(parent)
        self.data_source = data_source
        self.current_offset = current_offset
        self.setWindowTitle("Find / Search Pattern - yweinHEX")
        self.resize(650, 420)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Mode Selection
        mode_layout = QHBoxLayout()
        mode_lbl = QLabel("Search Type:")
        mode_lbl.setStyleSheet("font-weight: bold; color: #58a6ff;")
        self.rb_hex = QRadioButton("Hex Pattern (e.g. 4D 5A 90)")
        self.rb_text = QRadioButton("ASCII / Text")
        self.rb_regex = QRadioButton("Regular Expression")
        self.rb_hex.setChecked(True)

        self.btn_group = QButtonGroup(self)
        self.btn_group.addButton(self.rb_hex)
        self.btn_group.addButton(self.rb_text)
        self.btn_group.addButton(self.rb_regex)

        mode_layout.addWidget(mode_lbl)
        mode_layout.addWidget(self.rb_hex)
        mode_layout.addWidget(self.rb_text)
        mode_layout.addWidget(self.rb_regex)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)

        # Input field & Find button
        input_layout = QHBoxLayout()
        self.edit_pattern = QLineEdit()
        self.edit_pattern.setPlaceholderText("Enter hex bytes or text to search...")
        self.edit_pattern.returnPressed.connect(self._find_all)

        btn_find = QPushButton("Find All")
        btn_find.setObjectName("primaryButton")
        btn_find.clicked.connect(self._find_all)

        input_layout.addWidget(self.edit_pattern)
        input_layout.addWidget(btn_find)
        layout.addLayout(input_layout)

        # Results Table
        self.table = QTableWidget(0, 3, self)
        self.table.setHorizontalHeaderLabels(["Offset (Hex)", "Offset (Dec)", "Preview Match"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self.table)

        # Status & Bottom Buttons
        bottom_layout = QHBoxLayout()
        self.status_lbl = QLabel("Enter pattern and click Find All.")
        self.status_lbl.setStyleSheet("color: #8b949e;")
        bottom_layout.addWidget(self.status_lbl)
        bottom_layout.addStretch()

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        bottom_layout.addWidget(btn_close)
        layout.addLayout(bottom_layout)

    def _find_all(self):
        pattern_str = self.edit_pattern.text().strip()
        if not pattern_str or not self.data_source or self.data_source.size == 0:
            return

        matches = []
        max_scan = min(self.data_source.size, 50 * 1024 * 1024) # 50 MB scan limit
        chunk_size = 1024 * 1024
        max_matches = 1000

        try:
            if self.rb_hex.isChecked():
                # Parse hex pattern (e.g. "4D 5A 90" or "4d5a90")
                hex_clean = pattern_str.replace(" ", "").replace("0x", "")
                target_bytes = bytes.fromhex(hex_clean)
                finder = lambda chunk: [m.start() for m in re.finditer(re.escape(target_bytes), chunk)]
                target_len = len(target_bytes)
            elif self.rb_text.isChecked():
                target_bytes = pattern_str.encode('utf-8')
                finder = lambda chunk: [m.start() for m in re.finditer(re.escape(target_bytes), chunk)]
                target_len = len(target_bytes)
            else:
                target_regex = re.compile(pattern_str.encode('utf-8'))
                finder = lambda chunk: [m.start() for m in target_regex.finditer(chunk)]
                target_len = 4
        except Exception as e:
            QMessageBox.warning(self, "Invalid Pattern", f"Error parsing pattern: {e}")
            return

        self.status_lbl.setText("Searching...")
        self.table.setRowCount(0)

        offset = 0
        overlap = max(64, target_len)
        while offset < max_scan and len(matches) < max_matches:
            read_len = min(chunk_size + overlap, max_scan - offset)
            chunk = self.data_source.read(offset, read_len)
            if not chunk:
                break

            found_rel = finder(chunk)
            for r in found_rel:
                actual_off = offset + r
                if not any(m['offset'] == actual_off for m in matches):
                    preview_bytes = self.data_source.read(actual_off, 16)
                    preview_hex = " ".join(f"{b:02X}" for b in preview_bytes)
                    matches.append({
                        'offset': actual_off,
                        'offset_hex': f"0x{actual_off:08X}",
                        'preview': preview_hex
                    })
                    if len(matches) >= max_matches:
                        break

            offset += chunk_size

        self.table.setRowCount(len(matches))
        for row, m in enumerate(matches):
            h_item = QTableWidgetItem(m['offset_hex'])
            h_item.setData(Qt.UserRole, m['offset'])
            d_item = QTableWidgetItem(f"{m['offset']:,}")
            p_item = QTableWidgetItem(m['preview'])

            self.table.setItem(row, 0, h_item)
            self.table.setItem(row, 1, d_item)
            self.table.setItem(row, 2, p_item)

        self.status_lbl.setText(f"Found {len(matches)} occurrences. Double-click to jump.")

    def _on_row_double_clicked(self, index):
        row = index.row()
        item = self.table.item(row, 0)
        if item:
            offset = item.data(Qt.UserRole)
            self.jump_requested.emit(offset)
            self.accept()
