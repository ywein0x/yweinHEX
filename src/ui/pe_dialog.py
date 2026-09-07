from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QGroupBox, QPushButton, QTabWidget, QWidget
)
from src.core.pe_analyzer import PEAnalyzer

class PEDialog(QDialog):
    """
    PE (Portable Executable) & Binary Headers inspection dialog.
    """
    jump_requested = Signal(int)

    def __init__(self, pe_analyzer: PEAnalyzer, parent=None):
        super().__init__(parent)
        self.pe = pe_analyzer
        self.setWindowTitle("PE & Binary Header Inspector - yweinHEX")
        self.resize(780, 520)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        tabs = QTabWidget(self)

        # Tab 1: Headers & Architecture Info
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        
        info_table = QTableWidget(len(self.pe.info), 2, self)
        info_table.setHorizontalHeaderLabels(["Field", "Value"])
        info_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        info_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        info_table.verticalHeader().setVisible(False)
        info_table.setAlternatingRowColors(True)

        for row, (k, v) in enumerate(self.pe.info.items()):
            k_item = QTableWidgetItem(str(k))
            k_item.setForeground(Qt.gray)
            v_item = QTableWidgetItem(str(v))
            v_item.setFlags(v_item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            info_table.setItem(row, 0, k_item)
            info_table.setItem(row, 1, v_item)

        info_layout.addWidget(info_table)
        tabs.addTab(info_widget, "Headers & Properties")

        # Tab 2: Sections Table
        sec_widget = QWidget()
        sec_layout = QVBoxLayout(sec_widget)

        self.sec_table = QTableWidget(len(self.pe.sections), 7, self)
        self.sec_table.setHorizontalHeaderLabels([
            "Section", "Virt Addr", "Virt Size", "Raw Offset", "Raw Size", "Entropy", "Flags"
        ])
        self.sec_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.sec_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.sec_table.verticalHeader().setVisible(False)
        self.sec_table.setAlternatingRowColors(True)
        self.sec_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sec_table.doubleClicked.connect(self._on_section_double_clicked)

        for row, sec in enumerate(self.pe.sections):
            name_item = QTableWidgetItem(sec['name'])
            name_item.setData(Qt.UserRole, sec['raw_offset'])
            
            va_item = QTableWidgetItem(sec['virtual_address'])
            vs_item = QTableWidgetItem(sec['virtual_size'])
            ro_item = QTableWidgetItem(sec['raw_offset'])
            rs_item = QTableWidgetItem(sec['raw_size'])
            
            ent_val = float(sec['entropy'])
            ent_item = QTableWidgetItem(sec['entropy'])
            if ent_val > 7.2:
                ent_item.setForeground(QColor("#f85149")) # High / packed
            elif ent_val > 6.0:
                ent_item.setForeground(QColor("#d29922")) # Moderate
            else:
                ent_item.setForeground(QColor("#3fb950")) # Normal

            flags_item = QTableWidgetItem(sec['flags'])

            self.sec_table.setItem(row, 0, name_item)
            self.sec_table.setItem(row, 1, va_item)
            self.sec_table.setItem(row, 2, vs_item)
            self.sec_table.setItem(row, 3, ro_item)
            self.sec_table.setItem(row, 4, rs_item)
            self.sec_table.setItem(row, 5, ent_item)
            self.sec_table.setItem(row, 6, flags_item)

        sec_layout.addWidget(self.sec_table)
        sec_hint = QLabel("💡 Tip: Double-click any section row to jump directly to its raw offset in Hex View.")
        sec_hint.setStyleSheet("color: #8b949e; font-size: 11px;")
        sec_layout.addWidget(sec_hint)
        tabs.addTab(sec_widget, f"Sections ({len(self.pe.sections)})")

        layout.addWidget(tabs)

        # Bottom Close Button
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

    def _on_section_double_clicked(self, index):
        row = index.row()
        item = self.sec_table.item(row, 0)
        if item:
            raw_off_str = item.data(Qt.UserRole)
            try:
                offset = int(raw_off_str, 16)
                self.jump_requested.emit(offset)
                self.accept()
            except Exception:
                pass
