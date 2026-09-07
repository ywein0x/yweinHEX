import json
from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QProgressBar, QFileDialog, QMessageBox, QApplication, QGroupBox
)

from src.core.dumper import OffsetDumper, DumpedOffset
from src.core.annotations import AnnotationManager

class OffsetDumperDialog(QDialog):
    """
    Game & Process Offset Dumper Dialog.
    Dumps module bases, entity pointers, and struct offsets.
    Exports to C++, C#, Python, or JSON and integrates with Memory Annotations.
    """
    jump_requested = Signal(int)
    annotations_added = Signal()

    def __init__(self, data_source, annotation_manager: AnnotationManager, parent=None):
        super().__init__(parent)
        self.data_source = data_source
        self.mgr = annotation_manager
        self.dumper = OffsetDumper(data_source)
        self.setWindowTitle("⚡ Oyun & Süreç Ofset Dumper (Offset Dumper) - yweinHEX")
        self.resize(960, 600)
        self.all_dumped: List[DumpedOffset] = []
        self._init_ui()
        self._start_dump()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header Info Box
        src_name = self.data_source.name if self.data_source else "None"
        base_str = f"0x{self.data_source.base_address:X}" if self.data_source else "0x0"

        info_box = QGroupBox("Hedef Uygulama / Oyun Bilgileri")
        info_layout = QHBoxLayout(info_box)
        self.lbl_target = QLabel(f"Hedef: <b style='color:#58a6ff;'>{src_name}</b> | Taban Adres: <b style='color:#00f0ff;'>{base_str}</b>")
        self.lbl_target.setStyleSheet("font-size: 13px;")
        info_layout.addWidget(self.lbl_target)
        info_layout.addStretch()

        btn_redump = QPushButton("🚀 Yeniden Dump Et")
        btn_redump.setObjectName("primaryButton")
        btn_redump.clicked.connect(self._start_dump)
        info_layout.addWidget(btn_redump)
        layout.addWidget(info_box)

        # Filter Bar
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel("Filtrele:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Ofset adı, modül veya kategoriye göre ara (örn: health, player, Unity)...")
        self.search_edit.textChanged.connect(self._filter)
        filter_bar.addWidget(self.search_edit)
        layout.addLayout(filter_bar)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Offsets Table
        self.table = QTableWidget(0, 5, self)
        self.table.setHorizontalHeaderLabels([
            "Ofset Adı (Name)",
            "Modül",
            "RVA Ofset",
            "Mutlak Adres",
            "Kategori / Açıklama"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.doubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self.table)

        # Export & Action Bar
        action_bar = QHBoxLayout()
        self.status_lbl = QLabel("Ofsetler taranıyor...")
        self.status_lbl.setStyleSheet("color: #8b949e;")
        action_bar.addWidget(self.status_lbl)
        action_bar.addStretch()

        btn_save_mem = QPushButton("⭐ Seçilenleri Hafızaya Aktar")
        btn_save_mem.setToolTip("Seçili ofsetleri yweinHEX'in Hafıza ve Bağlam Haritasına kaydeder.")
        btn_save_mem.clicked.connect(self._save_to_memory)

        btn_cpp = QPushButton("📄 C++ (.hpp)")
        btn_cpp.clicked.connect(self._export_cpp)

        btn_cs = QPushButton("📄 C# (.cs)")
        btn_cs.clicked.connect(self._export_cs)

        btn_py = QPushButton("📄 Python (.py)")
        btn_py.clicked.connect(self._export_py)

        btn_json = QPushButton("📄 JSON")
        btn_json.clicked.connect(self._export_json)

        btn_close = QPushButton("Kapat")
        btn_close.clicked.connect(self.accept)

        action_bar.addWidget(btn_save_mem)
        action_bar.addWidget(btn_cpp)
        action_bar.addWidget(btn_cs)
        action_bar.addWidget(btn_py)
        action_bar.addWidget(btn_json)
        action_bar.addWidget(btn_close)
        layout.addLayout(action_bar)

    def _start_dump(self):
        if not self.data_source:
            return
        self.status_lbl.setText("Ofset dumper çalışıyor, bellek taranıyor...")
        self.progress_bar.setValue(10)
        QApplication.processEvents()

        self.all_dumped = self.dumper.dump(callback_progress=self.progress_bar.setValue)
        self.progress_bar.setValue(100)
        self._filter()

    def _filter(self):
        query = self.search_edit.text().strip().lower()
        filtered = []

        for item in self.all_dumped:
            if not query or (query in item.name.lower() or query in item.module_name.lower() or query in item.category.lower() or query in item.rva_hex.lower()):
                filtered.append(item)

        self.table.setRowCount(len(filtered))
        for row, item in enumerate(filtered):
            name_item = QTableWidgetItem(item.name)
            name_item.setData(Qt.UserRole, item)

            if "Can" in item.category or "Health" in item.name:
                name_item.setForeground(QColor("#bc8cff"))
            elif "Player" in item.name or "Oyuncu" in item.category:
                name_item.setForeground(QColor("#00f0ff"))
            elif "Modül" in item.category:
                name_item.setForeground(QColor("#f2cc60"))
            else:
                name_item.setForeground(QColor("#58a6ff"))

            mod_item = QTableWidgetItem(item.module_name)
            rva_item = QTableWidgetItem(item.rva_hex)
            abs_item = QTableWidgetItem(item.abs_hex)
            desc_item = QTableWidgetItem(f"[{item.category}] {item.desc}")

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, mod_item)
            self.table.setItem(row, 2, rva_item)
            self.table.setItem(row, 3, abs_item)
            self.table.setItem(row, 4, desc_item)

        self.status_lbl.setText(f"Toplam {len(filtered)} / {len(self.all_dumped)} ofset çıkarıldı. Çift tıklayarak ofsete gidebilirsiniz.")

    def _on_row_double_clicked(self, index):
        row = index.row()
        item = self.table.item(row, 0)
        if item:
            dumped: DumpedOffset = item.data(Qt.UserRole)
            self.jump_requested.emit(dumped.rva)

    def _save_to_memory(self):
        selected_rows = sorted(set(idx.row() for idx in self.table.selectedIndexes()))
        targets = [self.table.item(r, 0).data(Qt.UserRole) for r in selected_rows] if selected_rows else self.all_dumped

        if not targets:
            return

        added = 0
        for t in targets:
            col = "#bc8cff" if "Can" in t.category else ("#00f0ff" if "Player" in t.name else "#58a6ff")
            self.mgr.add(
                offset=t.rva,
                label=t.name,
                category=t.category,
                color=col,
                length=4,
                notes=f"Dumped from {t.module_name} ({t.desc})"
            )
            added += 1

        self.annotations_added.emit()
        QMessageBox.information(self, "Hafızaya Aktarıldı", f"✅ {added} adet ofset başarıyla Hafıza ve Bağlam Haritasına kaydedildi!")

    def _export_cpp(self):
        code = self.dumper.generate_cpp_header()
        path, _ = QFileDialog.getSaveFileName(self, "C++ Header Olarak Kaydet", "Offsets.hpp", "C++ Header (*.hpp *.h)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
            QMessageBox.information(self, "Kaydedildi", f"C++ ofset başlık dosyası kaydedildi: {path}")

    def _export_cs(self):
        code = self.dumper.generate_csharp_class()
        path, _ = QFileDialog.getSaveFileName(self, "C# Sınıfı Olarak Kaydet", "Offsets.cs", "C# Files (*.cs)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
            QMessageBox.information(self, "Kaydedildi", f"C# ofset dosyası kaydedildi: {path}")

    def _export_py(self):
        code = self.dumper.generate_python_class()
        path, _ = QFileDialog.getSaveFileName(self, "Python Olarak Kaydet", "offsets.py", "Python Files (*.py)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)
            QMessageBox.information(self, "Kaydedildi", f"Python ofset dosyası kaydedildi: {path}")

    def _export_json(self):
        data = [d.to_dict() for d in self.all_dumped]
        path, _ = QFileDialog.getSaveFileName(self, "JSON Olarak Kaydet", "offsets.json", "JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Kaydedildi", f"JSON ofset dosyası kaydedildi: {path}")
