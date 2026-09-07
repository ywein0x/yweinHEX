import struct
import datetime
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QRadioButton, QButtonGroup, 
    QApplication, QPushButton
)

class DataInspector(QWidget):
    """
    Real-time Data Inspector panel.
    Interprets bytes at the current offset as different primitive types
    with Little-Endian and Big-Endian support.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_little_endian = True
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Header & Endian Selector
        top_layout = QHBoxLayout()
        title = QLabel("DATA INSPECTOR")
        title.setStyleSheet("font-weight: bold; color: #58a6ff; letter-spacing: 1px;")
        top_layout.addWidget(title)
        top_layout.addStretch()

        self.btn_le = QRadioButton("LE")
        self.btn_be = QRadioButton("BE")
        self.btn_le.setChecked(True)
        self.btn_le.setToolTip("Little-Endian (x86/x64 default)")
        self.btn_be.setToolTip("Big-Endian")

        self.endian_group = QButtonGroup(self)
        self.endian_group.addButton(self.btn_le)
        self.endian_group.addButton(self.btn_be)
        self.btn_le.toggled.connect(self._on_endian_changed)

        top_layout.addWidget(self.btn_le)
        top_layout.addWidget(self.btn_be)
        layout.addLayout(top_layout)

        # Inspector Table
        self.table = QTableWidget(11, 2, self)
        self.table.setHorizontalHeaderLabels(["Type", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)

        self.types = [
            "Binary (8-bit)",
            "Int8 / UInt8",
            "Int16",
            "UInt16",
            "Int32",
            "UInt32",
            "Int64",
            "UInt64",
            "Float (32-bit)",
            "Double (64-bit)",
            "Unix Time / Date"
        ]

        for i, t in enumerate(self.types):
            type_item = QTableWidgetItem(t)
            type_item.setForeground(Qt.gray)
            val_item = QTableWidgetItem("-")
            self.table.setItem(i, 0, type_item)
            self.table.setItem(i, 1, val_item)

        self.table.doubleClicked.connect(self._on_copy_value)
        layout.addWidget(self.table)

        hint = QLabel("💡 Tip: Double-click any row to copy value.")
        hint.setStyleSheet("color: #8b949e; font-size: 11px;")
        layout.addWidget(hint)

    def _on_endian_changed(self):
        self.is_little_endian = self.btn_le.isChecked()
        if hasattr(self, '_last_raw_bytes'):
            self.update_data(self._last_raw_bytes)

    def _on_copy_value(self, index):
        row = index.row()
        item = self.table.item(row, 1)
        if item and item.text() != "-":
            QApplication.clipboard().setText(item.text())

    def update_data(self, raw_bytes: bytes):
        """Update the table based on up to 8 bytes from cursor."""
        self._last_raw_bytes = raw_bytes
        if not raw_bytes:
            for i in range(len(self.types)):
                self.table.item(i, 1).setText("-")
            return

        endian = "<" if self.is_little_endian else ">"
        b_len = len(raw_bytes)
        b0 = raw_bytes[0]

        # 1. Binary (8-bit)
        self.table.item(0, 1).setText(f"{b0:08b}")

        # 2. Int8 / UInt8
        s_byte = struct.unpack("b", raw_bytes[:1])[0]
        self.table.item(1, 1).setText(f"{s_byte}  /  {b0}")

        # 3. Int16
        if b_len >= 2:
            i16 = struct.unpack(f"{endian}h", raw_bytes[:2])[0]
            self.table.item(2, 1).setText(f"{i16:,}")
        else:
            self.table.item(2, 1).setText("-")

        # 4. UInt16
        if b_len >= 2:
            u16 = struct.unpack(f"{endian}H", raw_bytes[:2])[0]
            self.table.item(3, 1).setText(f"{u16:,}")
        else:
            self.table.item(3, 1).setText("-")

        # 5. Int32
        if b_len >= 4:
            i32 = struct.unpack(f"{endian}i", raw_bytes[:4])[0]
            self.table.item(4, 1).setText(f"{i32:,}")
        else:
            self.table.item(4, 1).setText("-")

        # 6. UInt32
        if b_len >= 4:
            u32 = struct.unpack(f"{endian}I", raw_bytes[:4])[0]
            self.table.item(5, 1).setText(f"{u32:,}")
        else:
            self.table.item(5, 1).setText("-")

        # 7. Int64
        if b_len >= 8:
            i64 = struct.unpack(f"{endian}q", raw_bytes[:8])[0]
            self.table.item(6, 1).setText(f"{i64:,}")
        else:
            self.table.item(6, 1).setText("-")

        # 8. UInt64
        if b_len >= 8:
            u64 = struct.unpack(f"{endian}Q", raw_bytes[:8])[0]
            self.table.item(7, 1).setText(f"{u64:,}")
        else:
            self.table.item(7, 1).setText("-")

        # 9. Float (32-bit)
        if b_len >= 4:
            f32 = struct.unpack(f"{endian}f", raw_bytes[:4])[0]
            self.table.item(8, 1).setText(f"{f32:.6g}")
        else:
            self.table.item(8, 1).setText("-")

        # 10. Double (64-bit)
        if b_len >= 8:
            d64 = struct.unpack(f"{endian}d", raw_bytes[:8])[0]
            self.table.item(9, 1).setText(f"{d64:.10g}")
        else:
            self.table.item(9, 1).setText("-")

        # 11. Unix Time
        if b_len >= 4:
            ts = struct.unpack(f"{endian}I", raw_bytes[:4])[0]
            try:
                # Limit to realistic timestamps between 1970 and 2100
                if 0 < ts < 4102444800:
                    dt = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
                    self.table.item(10, 1).setText(dt.strftime("%Y-%m-%d %H:%M:%S UTC"))
                else:
                    self.table.item(10, 1).setText(f"Out of range ({ts})")
            except Exception:
                self.table.item(10, 1).setText("-")
        else:
            self.table.item(10, 1).setText("-")
