from PySide6.QtCore import Qt, Signal, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QBrush, QMouseEvent
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
)
from src.core.entropy import calculate_entropy_blocks

class EntropyCanvas(QWidget):
    """Custom painted widget rendering the entropy curve/histogram across the binary."""
    offset_clicked = Signal(int)

    def __init__(self, entropies, total_size, parent=None):
        super().__init__(parent)
        self.entropies = entropies
        self.total_size = total_size
        self.hover_idx = -1
        self.setMouseTracking(True)
        self.setMinimumHeight(240)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.entropies:
            return
        w = self.width()
        num_blocks = len(self.entropies)
        block_w = w / num_blocks
        idx = int(event.position().x() / block_w)
        if 0 <= idx < num_blocks:
            self.hover_idx = idx
            self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and 0 <= self.hover_idx < len(self.entropies):
            step = self.total_size / len(self.entropies)
            target_offset = int(self.hover_idx * step)
            self.offset_clicked.emit(target_offset)

    def paintEvent(self, event):
        painter = QPainter(self)
        w = self.width()
        h = self.height()

        # Dark canvas background
        painter.fillRect(self.rect(), QColor("#161b22"))
        painter.setPen(QColor("#30363d"))
        painter.drawRect(0, 0, w - 1, h - 1)

        # Draw grid lines for 2.0, 4.0, 6.0, 8.0 entropy
        painter.setFont(QFont("Consolas", 9))
        for level in [2.0, 4.0, 6.0, 7.2, 8.0]:
            y = int(h - (level / 8.0) * (h - 30) - 20)
            painter.setPen(QPen(QColor("#21262d"), 1, Qt.DashLine))
            painter.drawLine(40, y, w - 10, y)
            painter.setPen(QColor("#8b949e"))
            painter.drawText(8, y + 4, f"{level:.1f}")

        if not self.entropies:
            painter.drawText(w // 2 - 50, h // 2, "No entropy data available.")
            return

        num_blocks = len(self.entropies)
        block_w = (w - 50) / num_blocks

        # Draw bars
        for i, ent in enumerate(self.entropies):
            bar_h = int((ent / 8.0) * (h - 30))
            x = 45 + int(i * block_w)
            y = h - 20 - bar_h

            if ent > 7.2:
                col = QColor("#f85149") # Encrypted / Packed
            elif ent > 5.5:
                col = QColor("#d29922") # High density / code
            elif ent > 3.0:
                col = QColor("#58a6ff") # Normal data
            else:
                col = QColor("#238636") # Sparse / repetitive

            if i == self.hover_idx:
                col = QColor("#00f0ff")

            painter.fillRect(QRect(x, y, max(1, int(block_w)), bar_h), col)

        # Hover info
        if 0 <= self.hover_idx < len(self.entropies):
            ent = self.entropies[self.hover_idx]
            step = self.total_size / num_blocks
            offset = int(self.hover_idx * step)
            info_text = f"Offset: 0x{offset:08X} | Block #{self.hover_idx + 1} | Entropy: {ent:.3f} / 8.0"
            painter.setPen(QColor("#00f0ff"))
            painter.drawText(50, 20, info_text)


class EntropyDialog(QDialog):
    """
    Shannon Entropy analysis dialog.
    """
    jump_requested = Signal(int)

    def __init__(self, data_source, parent=None):
        super().__init__(parent)
        self.data_source = data_source
        self.setWindowTitle("Shannon Entropy Graph - yweinHEX")
        self.resize(780, 440)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Top stats
        top_layout = QHBoxLayout()
        blocks = calculate_entropy_blocks(self.data_source, self.data_source.size, block_count=120)
        mean_ent = (sum(blocks) / len(blocks)) if blocks else 0.0

        stats_lbl = QLabel(f"Mean Entropy: <b style='color:#58a6ff;'>{mean_ent:.2f} / 8.0</b>")
        stats_lbl.setStyleSheet("font-size: 14px;")
        top_layout.addWidget(stats_lbl)
        top_layout.addStretch()

        legend_lbl = QLabel(
            "<span style='color:#238636;'>■</span> Low (<3) &nbsp; "
            "<span style='color:#58a6ff;'>■</span> Normal (3-5.5) &nbsp; "
            "<span style='color:#d29922;'>■</span> High (5.5-7.2) &nbsp; "
            "<span style='color:#f85149;'>■</span> Packed / Encrypted (>7.2)"
        )
        top_layout.addWidget(legend_lbl)
        layout.addLayout(top_layout)

        # Canvas
        self.canvas = EntropyCanvas(blocks, self.data_source.size, self)
        self.canvas.offset_clicked.connect(self._on_jump)
        layout.addWidget(self.canvas)

        hint = QLabel("💡 Tip: Click on any bar in the graph to jump to that offset in the Hex View.")
        hint.setStyleSheet("color: #8b949e; font-size: 11px;")
        layout.addWidget(hint)

        # Bottom Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

    def _on_jump(self, offset: int):
        self.jump_requested.emit(offset)
        self.accept()
