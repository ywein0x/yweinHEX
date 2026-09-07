from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QSpinBox, QComboBox, QApplication, QFileDialog, QMessageBox
)
from src.core.string_extractor import extract_strings

class StringsDialog(QDialog):
    """
    Strings Extractor dialog.
    Extracts and filters ASCII and UTF-16 strings with instant jump to offset.
    """
    jump_requested = Signal(int)

    def __init__(self, data_source, parent=None):
        super().__init__(parent)
        self.data_source = data_source
        self.setWindowTitle("Strings Extractor - yweinHEX")
        self.resize(780, 520)
        self.strings_cache = []
        self._init_ui()
        self._extract()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Filters Bar
        filter_bar = QHBoxLayout()
        filter_lbl = QLabel("Search:")
        filter_lbl.setStyleSheet("font-weight: bold; color: #58a6ff;")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter extracted strings...")
        self.search_edit.textChanged.connect(self._filter)

        min_len_lbl = QLabel("Min Length:")
        self.min_len_spin = QSpinBox()
        self.min_len_spin.setRange(3, 64)
        self.min_len_spin.setValue(4)
        self.min_len_spin.valueChanged.connect(self._extract)

        type_lbl = QLabel("Encoding:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["All (ASCII + UTF-16)", "ASCII Only", "UTF-16 Only"])
        self.type_combo.currentIndexChanged.connect(self._filter)

        btn_rescan = QPushButton("Scan")
        btn_rescan.clicked.connect(self._extract)

        filter_bar.addWidget(filter_lbl)
        filter_bar.addWidget(self.search_edit)
        filter_bar.addWidget(min_len_lbl)
        filter_bar.addWidget(self.min_len_spin)
        filter_bar.addWidget(type_lbl)
        filter_bar.addWidget(self.type_combo)
        filter_bar.addWidget(btn_rescan)
        layout.addLayout(filter_bar)

        # Strings Table
        self.table = QTableWidget(0, 4, self)
        self.table.setHorizontalHeaderLabels(["Offset", "Encoding", "Length", "String Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self.table)

        # Bottom Bar
        bottom_bar = QHBoxLayout()
        self.status_lbl = QLabel("Extracting strings...")
        self.status_lbl.setStyleSheet("color: #8b949e;")
        bottom_bar.addWidget(self.status_lbl)
        bottom_bar.addStretch()

        btn_copy = QPushButton("Copy String")
        btn_copy.clicked.connect(self._copy_selected)
        btn_export = QPushButton("Export to TXT")
        btn_export.clicked.connect(self._export)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)

        bottom_bar.addWidget(btn_copy)
        bottom_bar.addWidget(btn_export)
        bottom_bar.addWidget(btn_close)
        layout.addLayout(bottom_bar)

    def _extract(self):
        min_len = self.min_len_spin.value()
        self.status_lbl.setText("Scanning binary...")
        QApplication.processEvents()
        self.strings_cache = extract_strings(self.data_source, min_len=min_len, max_results=3000)
        self._filter()

    def _filter(self):
        query = self.search_edit.text().strip().lower()
        enc_idx = self.type_combo.currentIndex()

        filtered = []
        for s in self.strings_cache:
            if enc_idx == 1 and s['type'] != 'ASCII':
                continue
            if enc_idx == 2 and s['type'] != 'UTF-16':
                continue
            if query and query not in s['value'].lower():
                continue
            filtered.append(s)

        self.table.setRowCount(len(filtered))
        for row, s in enumerate(filtered):
            off_item = QTableWidgetItem(s['offset_hex'])
            off_item.setData(Qt.UserRole, s['offset'])
            type_item = QTableWidgetItem(s['type'])
            len_item = QTableWidgetItem(str(s['length']))
            val_item = QTableWidgetItem(s['value'])

            self.table.setItem(row, 0, off_item)
            self.table.setItem(row, 1, type_item)
            self.table.setItem(row, 2, len_item)
            self.table.setItem(row, 3, val_item)

        self.status_lbl.setText(f"Showing {len(filtered)} / {len(self.strings_cache)} strings. Double-click to jump.")

    def _on_row_double_clicked(self, index):
        row = index.row()
        item = self.table.item(row, 0)
        if item:
            offset = item.data(Qt.UserRole)
            self.jump_requested.emit(offset)
            self.accept()

    def _copy_selected(self):
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            val_item = self.table.item(row, 3)
            if val_item:
                QApplication.clipboard().setText(val_item.text())

    def _export(self):
        if not self.strings_cache:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Strings", "extracted_strings.txt", "Text Files (*.txt)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                for s in self.strings_cache:
                    f.write(f"{s['offset_hex']}\t[{s['type']}]\t{s['value']}\n")
            QMessageBox.information(self, "Exported", f"Exported {len(self.strings_cache)} strings to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {e}")
