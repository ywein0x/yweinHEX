from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox
)

class GotoDialog(QDialog):
    """
    Jump to Offset dialog supporting Hex, Decimal, and Relative offsets.
    """
    jump_requested = Signal(int)

    def __init__(self, current_offset: int, max_size: int, parent=None):
        super().__init__(parent)
        self.current_offset = current_offset
        self.max_size = max_size
        self.setWindowTitle("Go to Offset - yweinHEX")
        self.setFixedSize(380, 160)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl = QLabel("Enter Offset (Hex: <code>0x100</code> or Dec: <code>256</code>):")
        lbl.setStyleSheet("color: #c9d1d9;")
        layout.addWidget(lbl)

        self.edit_offset = QLineEdit()
        self.edit_offset.setPlaceholderText("e.g. 0x00400000, 4096, +0x100...")
        self.edit_offset.setText(f"0x{self.current_offset:X}")
        self.edit_offset.selectAll()
        self.edit_offset.returnPressed.connect(self._on_jump)
        layout.addWidget(self.edit_offset)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_go = QPushButton("Go")
        btn_go.setObjectName("primaryButton")
        btn_go.clicked.connect(self._on_jump)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_go)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def _on_jump(self):
        text = self.edit_offset.text().strip().lower()
        if not text:
            return

        is_relative = text.startswith("+") or text.startswith("-")
        sign = -1 if text.startswith("-") else 1
        raw_val = text.lstrip("+-")

        try:
            if raw_val.startswith("0x") or any(c in "abcdef" for c in raw_val) or raw_val.endswith("h"):
                raw_val = raw_val.replace("0x", "").rstrip("h")
                val = int(raw_val, 16)
            else:
                val = int(raw_val, 10)

            if is_relative:
                target = self.current_offset + (sign * val)
            else:
                target = val

            if target < 0 or (self.max_size > 0 and target >= self.max_size):
                QMessageBox.warning(self, "Invalid Offset", f"Offset 0x{target:X} is outside range (0 to 0x{self.max_size:X}).")
                return

            self.jump_requested.emit(target)
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid number format. Use e.g. 0x1000 or 4096.")
