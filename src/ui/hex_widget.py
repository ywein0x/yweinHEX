import base64
import math
from typing import Optional
from PySide6.QtCore import Qt, QRect, Signal, QPoint
from PySide6.QtGui import (
    QPainter, QFont, QFontMetrics, QColor, QPen, QBrush, 
    QKeySequence, QKeyEvent, QMouseEvent, QWheelEvent, QClipboard
)
from PySide6.QtWidgets import (
    QWidget, QScrollBar, QHBoxLayout, QMenu, QApplication
)
from src.core.data_source import DataSource

class HexWidget(QWidget):
    """
    Virtual-scrolling Hex Viewer widget.
    High-performance QPainter rendering with syntax highlighting,
    synchronized Hex & ASCII selection, and full keyboard navigation.
    """
    cursor_changed = Signal(int)
    selection_changed = Signal(int, int)
    request_add_annotation = Signal(int)

    BYTES_PER_ROW = 16

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAttribute(Qt.WA_OpaquePaintEvent)

        self.data_source: Optional[DataSource] = None
        self.annotation_manager = None
        self.cursor_offset: int = 0
        self.selection_start: int = 0
        self.selection_end: int = 0
        self.is_selecting: bool = False

        # Fonts & Metrics
        self.font = QFont("Consolas", 10)
        self.font.setStyleHint(QFont.Monospace)
        self.font_metrics = QFontMetrics(self.font)
        self.char_width = self.font_metrics.horizontalAdvance("0")
        self.char_height = self.font_metrics.height()
        self.line_height = self.char_height + 4

        # Layout Column X-positions (calculated in resizeEvent)
        self.header_height = self.line_height + 6
        self.offset_x = 12
        self.offset_chars = 8
        self.hex_start_x = 0
        self.ascii_start_x = 0

        # Scrollbar setup
        self.scroll_bar = QScrollBar(Qt.Vertical, self)
        self.scroll_bar.valueChanged.connect(self._on_scroll)

        # Color Palette
        self.col_bg = QColor("#0d1117")
        self.col_header_bg = QColor("#161b22")
        self.col_header_text = QColor("#58a6ff")
        self.col_border = QColor("#30363d")
        self.col_offset = QColor("#8b949e")
        self.col_null = QColor("#484f58")
        self.col_ascii = QColor("#58a6ff")
        self.col_number = QColor("#f2cc60")
        self.col_high = QColor("#bc8cff")
        self.col_control = QColor("#79c0ff")
        self.col_cursor_border = QColor("#00f0ff")
        self.col_select_bg = QColor(31, 111, 235, 120)
        self.col_ascii_text = QColor("#c9d1d9")

        self._update_metrics()

    def set_data_source(self, source: Optional[DataSource]):
        """Attach a new file or process data source."""
        self.data_source = source
        self.cursor_offset = 0
        self.selection_start = 0
        self.selection_end = 0
        self._update_metrics()
        self._update_scroll_range()
        self.scroll_bar.setValue(0)
        self.update()
        self.cursor_changed.emit(self.cursor_offset)
        self.selection_changed.emit(0, 0)

    def set_annotation_manager(self, mgr):
        """Attach an AnnotationManager to render notes, tags and pointer links."""
        self.annotation_manager = mgr
        self.update()

    def _update_metrics(self):
        # Determine offset column width (8 or 16 hex chars)
        if self.data_source and (self.data_source.base_address > 0xFFFFFFFF or self.data_source.size > 0xFFFFFFFF):
            self.offset_chars = 16
        else:
            self.offset_chars = 8
        
        self.offset_width = (self.offset_chars + 3) * self.char_width
        self.hex_start_x = self.offset_x + self.offset_width
        # 16 bytes: 2 chars + 1 space = 3 chars per byte. Extra space at byte 8.
        self.hex_width = (16 * 3 + 2) * self.char_width
        self.ascii_start_x = self.hex_start_x + self.hex_width + (2 * self.char_width)

    def _update_scroll_range(self):
        if not self.data_source or self.data_source.size == 0:
            self.scroll_bar.setRange(0, 0)
            return

        total_rows = math.ceil(self.data_source.size / self.BYTES_PER_ROW)
        visible_rows = max(1, (self.height() - self.header_height) // self.line_height)
        max_scroll = max(0, total_rows - visible_rows)
        self.scroll_bar.setRange(0, max_scroll)
        self.scroll_bar.setPageStep(visible_rows)

    def _on_scroll(self, val):
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        sb_width = self.scroll_bar.sizeHint().width()
        self.scroll_bar.setGeometry(self.width() - sb_width, 0, sb_width, self.height())
        self._update_scroll_range()

    def visible_rows(self) -> int:
        return max(1, (self.height() - self.header_height) // self.line_height)

    def first_visible_row(self) -> int:
        return self.scroll_bar.value()

    def jump_to_offset(self, offset: int):
        """Scroll and focus to a target offset."""
        if not self.data_source:
            return
        offset = max(0, min(offset, self.data_source.size - 1))
        self.cursor_offset = offset
        self.selection_start = offset
        self.selection_end = offset
        
        target_row = offset // self.BYTES_PER_ROW
        first_row = self.first_visible_row()
        vis_rows = self.visible_rows()
        
        if target_row < first_row or target_row >= first_row + vis_rows:
            new_scroll = max(0, target_row - vis_rows // 2)
            self.scroll_bar.setValue(new_scroll)
            
        self.update()
        self.cursor_changed.emit(self.cursor_offset)
        self.selection_changed.emit(self.cursor_offset, 1)

    def _byte_color(self, b: int) -> QColor:
        if b == 0:
            return self.col_null
        elif 0x30 <= b <= 0x39:
            return self.col_number
        elif 0x20 <= b <= 0x7E:
            return self.col_ascii
        elif b >= 0x80:
            return self.col_high
        else:
            return self.col_control

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(self.font)

        # Background
        painter.fillRect(self.rect(), self.col_bg)

        # Header Bar
        hdr_rect = QRect(0, 0, self.width(), self.header_height)
        painter.fillRect(hdr_rect, self.col_header_bg)
        painter.setPen(self.col_border)
        painter.drawLine(0, self.header_height, self.width(), self.header_height)

        # Draw Header Labels
        painter.setPen(self.col_header_text)
        hdr_y = self.font_metrics.ascent() + 4
        painter.drawText(self.offset_x, hdr_y, "Offset")

        for b in range(16):
            x = self._hex_byte_x(b)
            painter.drawText(x, hdr_y, f"{b:02X}")

        painter.drawText(self.ascii_start_x, hdr_y, "Decoded Text")

        if not self.data_source or self.data_source.size == 0:
            painter.setPen(self.col_null)
            painter.drawText(self.offset_x, self.header_height + 40, "No file or process memory loaded. Press 'Open File' or 'Open Process'.")
            return

        # Data Lines
        first_row = self.first_visible_row()
        vis_rows = self.visible_rows() + 1
        total_rows = math.ceil(self.data_source.size / self.BYTES_PER_ROW)

        start_offset = first_row * self.BYTES_PER_ROW
        read_len = min(vis_rows * self.BYTES_PER_ROW, self.data_source.size - start_offset)
        buffer = self.data_source.read(start_offset, read_len)

        sel_min = min(self.selection_start, self.selection_end)
        sel_max = max(self.selection_start, self.selection_end)

        for row_idx in range(vis_rows):
            current_row = first_row + row_idx
            if current_row >= total_rows:
                break

            row_y = self.header_height + (row_idx * self.line_height)
            text_y = row_y + self.font_metrics.ascent() + 2
            row_offset = current_row * self.BYTES_PER_ROW
            display_addr = self.data_source.base_address + row_offset

            # 1. Offset Column
            painter.setPen(self.col_offset)
            if self.offset_chars == 16:
                offset_str = f"{display_addr:016X}"
            else:
                offset_str = f"{display_addr:08X}"
            painter.drawText(self.offset_x, text_y, offset_str)

            # Draw row-level pointer link indicator if any byte in this row has a linked target
            if self.annotation_manager:
                for c in range(16):
                    chk_off = row_offset + c
                    ann_chk = self.annotation_manager.get(chk_off)
                    if ann_chk and ann_chk.linked_target is not None:
                        painter.setPen(QColor("#00f0ff"))
                        painter.drawText(self.offset_x + self.offset_width - (self.char_width * 2), text_y, "➜")
                        break

            # 2. Hex & ASCII Columns
            row_buf_start = row_idx * self.BYTES_PER_ROW
            row_buf_end = min(row_buf_start + self.BYTES_PER_ROW, len(buffer))

            for col in range(16):
                byte_offset = row_offset + col
                if byte_offset >= self.data_source.size:
                    break

                buf_idx = row_buf_start + col
                if buf_idx >= len(buffer):
                    break

                byte_val = buffer[buf_idx]
                hex_x = self._hex_byte_x(col)
                ascii_x = self.ascii_start_x + (col * self.char_width)

                is_selected = (sel_min <= byte_offset <= sel_max and sel_min != sel_max)
                is_cursor = (byte_offset == self.cursor_offset)

                # Check if this byte has a user memory note / annotation
                ann = self.annotation_manager.get_covering_annotation(byte_offset) if self.annotation_manager else None
                if ann:
                    ann_col = QColor(ann.color)
                    ann_col.setAlpha(80)
                    painter.fillRect(QRect(hex_x - 2, row_y + 1, self.char_width * 2 + 4, self.line_height - 2), ann_col)
                    painter.fillRect(QRect(ascii_x, row_y + 1, self.char_width, self.line_height - 2), ann_col)

                # Draw selection background
                if is_selected:
                    sel_rect_hex = QRect(hex_x - 2, row_y + 1, self.char_width * 2 + 4, self.line_height - 2)
                    painter.fillRect(sel_rect_hex, self.col_select_bg)
                    sel_rect_asc = QRect(ascii_x, row_y + 1, self.char_width, self.line_height - 2)
                    painter.fillRect(sel_rect_asc, self.col_select_bg)

                # Draw cursor highlight
                if is_cursor:
                    cur_rect_hex = QRect(hex_x - 2, row_y + 1, self.char_width * 2 + 4, self.line_height - 2)
                    painter.setPen(QPen(self.col_cursor_border, 1.5))
                    painter.drawRect(cur_rect_hex)
                    cur_rect_asc = QRect(ascii_x, row_y + 1, self.char_width, self.line_height - 2)
                    painter.drawRect(cur_rect_asc)

                # Draw Hex text
                painter.setPen(self._byte_color(byte_val))
                painter.drawText(hex_x, text_y, f"{byte_val:02X}")

                # Draw ASCII character
                char_str = chr(byte_val) if 0x20 <= byte_val <= 0x7E else "·"
                painter.setPen(self.col_ascii_text if 0x20 <= byte_val <= 0x7E else self.col_null)
                painter.drawText(ascii_x, text_y, char_str)

    def _hex_byte_x(self, col: int) -> int:
        extra_space = (self.char_width) if col >= 8 else 0
        return self.hex_start_x + (col * 3 * self.char_width) + extra_space

    def _offset_from_pos(self, pt: QPoint) -> Optional[int]:
        if not self.data_source or self.data_source.size == 0:
            return None

        if pt.y() <= self.header_height:
            return None

        row_idx = (pt.y() - self.header_height) // self.line_height
        target_row = self.first_visible_row() + row_idx

        # Check if in Hex area
        for col in range(16):
            x = self._hex_byte_x(col)
            if x - 2 <= pt.x() <= x + (self.char_width * 2) + 2:
                off = target_row * self.BYTES_PER_ROW + col
                return min(off, self.data_source.size - 1)

        # Check if in ASCII area
        for col in range(16):
            x = self.ascii_start_x + (col * self.char_width)
            if x <= pt.x() <= x + self.char_width:
                off = target_row * self.BYTES_PER_ROW + col
                return min(off, self.data_source.size - 1)

        return None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            off = self._offset_from_pos(event.position().toPoint())
            if off is not None:
                self.cursor_offset = off
                if not (event.modifiers() & Qt.ShiftModifier):
                    self.selection_start = off
                    self.selection_end = off
                else:
                    self.selection_end = off
                self.is_selecting = True
                self.update()
                self.cursor_changed.emit(self.cursor_offset)
                sel_len = abs(self.selection_end - self.selection_start) + 1
                self.selection_changed.emit(min(self.selection_start, self.selection_end), sel_len)
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_selecting:
            off = self._offset_from_pos(event.position().toPoint())
            if off is not None:
                self.cursor_offset = off
                self.selection_end = off
                self.update()
                self.cursor_changed.emit(self.cursor_offset)
                sel_len = abs(self.selection_end - self.selection_start) + 1
                self.selection_changed.emit(min(self.selection_start, self.selection_end), sel_len)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.is_selecting = False

    def wheelEvent(self, event: QWheelEvent):
        degrees = event.angleDelta().y() / 8
        steps = -int(degrees / 15) * 3
        self.scroll_bar.setValue(self.scroll_bar.value() + steps)

    def keyPressEvent(self, event: QKeyEvent):
        if not self.data_source or self.data_source.size == 0:
            return

        key = event.key()
        shift = bool(event.modifiers() & Qt.ShiftModifier)
        ctrl = bool(event.modifiers() & Qt.ControlModifier)

        new_offset = self.cursor_offset

        if key == Qt.Key_Left:
            new_offset = max(0, self.cursor_offset - 1)
        elif key == Qt.Key_Right:
            new_offset = min(self.data_source.size - 1, self.cursor_offset + 1)
        elif key == Qt.Key_Up:
            new_offset = max(0, self.cursor_offset - self.BYTES_PER_ROW)
        elif key == Qt.Key_Down:
            new_offset = min(self.data_source.size - 1, self.cursor_offset + self.BYTES_PER_ROW)
        elif key == Qt.Key_PageUp:
            new_offset = max(0, self.cursor_offset - (self.visible_rows() * self.BYTES_PER_ROW))
        elif key == Qt.Key_PageDown:
            new_offset = min(self.data_source.size - 1, self.cursor_offset + (self.visible_rows() * self.BYTES_PER_ROW))
        elif key == Qt.Key_Home:
            if ctrl:
                new_offset = 0
            else:
                new_offset = (self.cursor_offset // self.BYTES_PER_ROW) * self.BYTES_PER_ROW
        elif key == Qt.Key_End:
            if ctrl:
                new_offset = self.data_source.size - 1
            else:
                new_offset = min(self.data_source.size - 1, (self.cursor_offset // self.BYTES_PER_ROW + 1) * self.BYTES_PER_ROW - 1)
        elif ctrl and key == Qt.Key_C:
            self.copy_selection_as_hex()
            return
        elif ctrl and key == Qt.Key_A:
            self.select_all()
            return
        else:
            super().keyPressEvent(event)
            return

        self.jump_to_offset(new_offset)
        if shift:
            self.selection_end = new_offset
        else:
            self.selection_start = new_offset
            self.selection_end = new_offset

        sel_len = abs(self.selection_end - self.selection_start) + 1
        self.selection_changed.emit(min(self.selection_start, self.selection_end), sel_len)

    def get_selected_bytes(self) -> bytes:
        if not self.data_source:
            return b""
        start = min(self.selection_start, self.selection_end)
        length = abs(self.selection_end - self.selection_start) + 1
        return self.data_source.read(start, length)

    def select_all(self):
        if not self.data_source or self.data_source.size == 0:
            return
        self.selection_start = 0
        self.selection_end = self.data_source.size - 1
        self.update()
        self.selection_changed.emit(0, self.data_source.size)

    def copy_selection_as_hex(self, spaces: bool = True):
        data = self.get_selected_bytes()
        if not data:
            return
        text = " ".join(f"{b:02X}" for b in data) if spaces else "".join(f"{b:02X}" for b in data)
        QApplication.clipboard().setText(text)

    def copy_selection_as_c_array(self):
        data = self.get_selected_bytes()
        if not data:
            return
        items = [f"0x{b:02X}" for b in data]
        text = "const unsigned char data[] = {\n    " + ", ".join(items) + "\n};"
        QApplication.clipboard().setText(text)

    def copy_selection_as_string(self):
        data = self.get_selected_bytes()
        if not data:
            return
        text = "".join(chr(b) if 0x20 <= b <= 0x7E else "." for b in data)
        QApplication.clipboard().setText(text)

    def copy_selection_as_base64(self):
        data = self.get_selected_bytes()
        if not data:
            return
        text = base64.b64encode(data).decode('ascii')
        QApplication.clipboard().setText(text)

    def _show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        act_hex = menu.addAction("Copy Hex (Space-separated)")
        act_raw_hex = menu.addAction("Copy Hex (Continuous)")
        act_c = menu.addAction("Copy C-Array")
        act_str = menu.addAction("Copy ASCII String")
        act_b64 = menu.addAction("Copy Base64")
        menu.addSeparator()

        act_note = menu.addAction("📝 Hafızaya / Notlara Ekle (Add to Memory)...")
        act_link = None
        if self.annotation_manager:
            ann = self.annotation_manager.get(self.cursor_offset)
            if ann and ann.linked_target is not None:
                act_link = menu.addAction(f"🔗 Bağlı Hedefe Git: ➜ 0x{ann.linked_target:08X}")

        menu.addSeparator()
        act_all = menu.addAction("Select All (Ctrl+A)")

        action = menu.exec(pos)
        if action == act_hex:
            self.copy_selection_as_hex(spaces=True)
        elif action == act_raw_hex:
            self.copy_selection_as_hex(spaces=False)
        elif action == act_c:
            self.copy_selection_as_c_array()
        elif action == act_str:
            self.copy_selection_as_string()
        elif action == act_b64:
            self.copy_selection_as_base64()
        elif action == act_note:
            self.request_add_annotation.emit(self.cursor_offset)
        elif act_link and action == act_link:
            ann = self.annotation_manager.get(self.cursor_offset)
            if ann and ann.linked_target is not None:
                self.jump_to_offset(ann.linked_target)
        elif action == act_all:
            self.select_all()
