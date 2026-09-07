from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QFileDialog, 
    QMessageBox, QDialog, QLineEdit, QComboBox, QApplication
)

from src.core.annotations import AnnotationManager, Annotation
from src.core.i18n import tr

class AddAnnotationDialog(QDialog):
    """Dialog to confirm and add an offset to memory/annotations."""

    def __init__(self, offset: int, default_label: str = "", default_category: str = "General", parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("act_add_note"))
        self.setFixedSize(380, 240)
        self.offset = offset
        self.confirmed_ann: Optional[Annotation] = None
        self._init_ui(default_label, default_category)

    def _init_ui(self, default_label: str, default_category: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl_off = QLabel(f"{tr('status_offset')}: <b>0x{self.offset:08X}</b> ({self.offset:,})")
        lbl_off.setStyleSheet("color: #58a6ff; font-size: 14px;")
        layout.addWidget(lbl_off)

        layout.addWidget(QLabel("Etiket / İsim (Örn: Can Struct, Para Pointer):"))
        self.edit_label = QLineEdit(default_label or f"Offset_0x{self.offset:08X}")
        layout.addWidget(self.edit_label)

        layout.addWidget(QLabel(tr("context_table_cat") + ":"))
        self.combo_cat = QComboBox()
        self.combo_cat.addItems([
            "Oyun Değişkeni / Can", "Oyun Para / Kaynak", "Pointer / Referans", 
            "Kripto / Güvenlik", "Ağ / İletişim", "Kod / Fonksiyon", "Genel Not"
        ])
        if default_category in [self.combo_cat.itemText(i) for i in range(self.combo_cat.count())]:
            self.combo_cat.setCurrentText(default_category)
        layout.addWidget(self.combo_cat)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_save = QPushButton("💾 Onayla ve Hafızaya Al")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self._on_save)
        btn_cancel = QPushButton("İptal")
        btn_cancel.clicked.connect(self.reject)

        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

    def _on_save(self):
        lbl = self.edit_label.text().strip()
        if not lbl:
            lbl = f"Offset_0x{self.offset:08X}"
        cat = self.combo_cat.currentText()
        color = "#bc8cff" if "Can" in cat or "Para" in cat else ("#58a6ff" if "Pointer" in cat else "#3fb950")
        self.confirmed_ann = Annotation(offset=self.offset, label=lbl, category=cat, color=color, length=4)
        self.accept()


class ContextDock(QWidget):
    """
    Memory, Notes and Context Linker Dock widget.
    Shows all approved annotations and pointer links.
    """
    jump_requested = Signal(int)
    annotations_updated = Signal()

    def __init__(self, annotation_manager: AnnotationManager, parent=None):
        super().__init__(parent)
        self.mgr = annotation_manager
        self.data_source = None
        self._init_ui()

    def set_data_source(self, source):
        self.data_source = source
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header Title
        title = QLabel(tr("context_title"))
        title.setStyleSheet("font-weight: bold; color: #bc8cff; letter-spacing: 1px;")
        layout.addWidget(title)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_resolve = QPushButton("🔗 Bağlamları Çöz (Resolve Links)")
        self.btn_resolve.setToolTip("Ofsetlerdeki pointer değerlerini tespit edip hedeflere ok bağlar.")
        self.btn_resolve.clicked.connect(self.resolve_links)

        self.btn_export = QPushButton("JSON Kaydet")
        self.btn_export.clicked.connect(self.export_annotations)

        self.btn_import = QPushButton("Yükle")
        self.btn_import.clicked.connect(self.import_annotations)

        self.btn_clear = QPushButton("Temizle")
        self.btn_clear.clicked.connect(self.clear_all)

        btn_layout.addWidget(self.btn_resolve)
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_import)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)

        # Table
        self.table = QTableWidget(0, 4, self)
        self.table.setHorizontalHeaderLabels([
            tr("context_table_offset"),
            tr("context_table_label"),
            tr("context_table_target"),
            tr("context_table_cat")
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self.table)

        hint = QLabel(tr("context_link_hint"))
        hint.setStyleSheet("color: #8b949e; font-size: 11px;")
        layout.addWidget(hint)

    def refresh(self):
        annotations = self.mgr.all_sorted()
        self.table.setRowCount(len(annotations))

        for row, ann in enumerate(annotations):
            off_item = QTableWidgetItem(f"0x{ann.offset:08X}")
            off_item.setData(Qt.UserRole, ann.offset)
            
            lbl_item = QTableWidgetItem(ann.label)
            lbl_item.setForeground(QColor(ann.color))

            target_str = f"➜ 0x{ann.linked_target:08X}" if ann.linked_target is not None else "-"
            target_item = QTableWidgetItem(target_str)
            if ann.linked_target is not None:
                target_item.setForeground(QColor("#00f0ff"))

            cat_item = QTableWidgetItem(ann.category)

            self.table.setItem(row, 0, off_item)
            self.table.setItem(row, 1, lbl_item)
            self.table.setItem(row, 2, target_item)
            self.table.setItem(row, 3, cat_item)

        self.annotations_updated.emit()

    def resolve_links(self):
        """Resolves pointer values for all annotations against data_source."""
        if not self.data_source:
            return
        resolved_count = 0
        for ann in self.mgr.all_sorted():
            target = self.mgr.resolve_pointer_link(ann, self.data_source)
            if target is not None:
                resolved_count += 1
        self.refresh()
        QMessageBox.information(self, "Bağlam Bağlayıcı", f"{resolved_count} adet bağlantılı pointer hedefi tespit edildi ve eşleştirildi.")

    def _on_row_double_clicked(self, index):
        row = index.row()
        item = self.table.item(row, 0)
        if item:
            offset = item.data(Qt.UserRole)
            self.jump_requested.emit(offset)

    def export_annotations(self):
        if not self.mgr.annotations:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Hafızayı Kaydet", "yweinHEX_memory.json", "JSON (*.json)")
        if path:
            self.mgr.export_json(path)
            QMessageBox.information(self, "Kaydedildi", f"Hafıza ve notlar kaydedildi: {path}")

    def import_annotations(self):
        path, _ = QFileDialog.getOpenFileName(self, "Hafıza Yükle", "", "JSON (*.json)")
        if path:
            count = self.mgr.import_json(path)
            self.refresh()
            QMessageBox.information(self, "Yüklendi", f"{count} adet not/hafıza başarıyla içe aktarıldı.")

    def clear_all(self):
        if QMessageBox.question(self, "Temizle", "Tüm notlar ve hafıza temizlensin mi?") == QMessageBox.Yes:
            self.mgr.clear()
            self.refresh()
