from typing import List, Dict, Any
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QProgressBar, QComboBox, QMessageBox, QApplication
)
from src.core.scanner import SmartScanner
from src.core.annotations import AnnotationManager
from src.core.i18n import tr

class SmartScannerDialog(QDialog):
    """
    Automatic Smart Pattern & Game Entity Hunter Dialog.
    Discovers game engines, health/value patterns, crypto constants, and APIs.
    Allows user to approve and save valuable offsets directly to memory.
    """
    jump_requested = Signal(int)
    annotations_added = Signal()

    def __init__(self, data_source, annotation_manager: AnnotationManager, parent=None):
        super().__init__(parent)
        self.data_source = data_source
        self.mgr = annotation_manager
        self.setWindowTitle(tr("scanner_title"))
        self.resize(920, 560)
        self.all_results: List[Dict[str, Any]] = []
        self._init_ui()
        self._start_scan()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Filters Bar
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("Filtre:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(tr("scanner_filter_placeholder"))
        self.search_edit.textChanged.connect(self._filter)

        self.cat_combo = QComboBox()
        self.cat_combo.addItems(["Hepsi", "Oyun", "Kripto", "Bellek", "Ağ / İletişim"])
        self.cat_combo.currentIndexChanged.connect(self._filter)

        btn_rescan = QPushButton("🔄 Yeniden Tara")
        btn_rescan.clicked.connect(self._start_scan)

        top_bar.addWidget(self.search_edit)
        top_bar.addWidget(self.cat_combo)
        top_bar.addWidget(btn_rescan)
        layout.addLayout(top_bar)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Results Table
        self.table = QTableWidget(0, 5, self)
        self.table.setHorizontalHeaderLabels([
            tr("scanner_col_offset"),
            tr("scanner_col_category"),
            tr("scanner_col_name"),
            tr("scanner_col_confidence"),
            tr("scanner_col_preview")
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

        # Bottom Bar
        bottom_bar = QHBoxLayout()
        self.status_lbl = QLabel(tr("scanner_searching"))
        self.status_lbl.setStyleSheet("color: #8b949e;")
        bottom_bar.addWidget(self.status_lbl)
        bottom_bar.addStretch()

        self.btn_save = QPushButton("⭐ Seçilenleri Onayla ve Hafızaya Ekle")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setToolTip("Seçili satırları onaylayarak hafıza ve bağlam haritasına aktarır.")
        self.btn_save.clicked.connect(self._save_selected_to_memory)

        btn_close = QPushButton("Kapat")
        btn_close.clicked.connect(self.accept)

        bottom_bar.addWidget(self.btn_save)
        bottom_bar.addWidget(btn_close)
        layout.addLayout(bottom_bar)

    def _start_scan(self):
        if not self.data_source:
            return
        self.status_lbl.setText("Akıllı tarayıcı çalışıyor...")
        self.progress_bar.setValue(10)
        QApplication.processEvents()

        scanner = SmartScanner(self.data_source)
        self.all_results = scanner.scan(callback_progress=self.progress_bar.setValue)
        self.progress_bar.setValue(100)
        self._filter()

    def _filter(self):
        query = self.search_edit.text().strip().lower()
        cat_filter = self.cat_combo.currentText()

        filtered = []
        for r in self.all_results:
            if cat_filter != "Hepsi" and cat_filter not in r['category']:
                continue
            if query and query not in r['name'].lower() and query not in r['offset_hex'].lower():
                continue
            filtered.append(r)

        self.table.setRowCount(len(filtered))
        for row, r in enumerate(filtered):
            off_item = QTableWidgetItem(r['offset_hex'])
            off_item.setData(Qt.UserRole, r)

            cat_item = QTableWidgetItem(r['category'])
            if "Oyun" in r['category']:
                cat_item.setForeground(QColor("#bc8cff"))
            elif "Kripto" in r['category']:
                cat_item.setForeground(QColor("#f2cc60"))
            else:
                cat_item.setForeground(QColor("#58a6ff"))

            name_item = QTableWidgetItem(r['name'])
            conf_item = QTableWidgetItem(r['confidence'])
            prev_item = QTableWidgetItem(r['preview'])

            self.table.setItem(row, 0, off_item)
            self.table.setItem(row, 1, cat_item)
            self.table.setItem(row, 2, name_item)
            self.table.setItem(row, 3, conf_item)
            self.table.setItem(row, 4, prev_item)

        self.status_lbl.setText(f"{len(filtered)} / {len(self.all_results)} değerli desen bulundu. Çift tıklayarak ofsete gidebilirsiniz.")

    def _on_row_double_clicked(self, index):
        row = index.row()
        item = self.table.item(row, 0)
        if item:
            r = item.data(Qt.UserRole)
            self.jump_requested.emit(r['offset'])

    def _save_selected_to_memory(self):
        selected_rows = sorted(set(idx.row() for idx in self.table.selectedIndexes()))
        if not selected_rows:
            QMessageBox.information(self, "Bilgi", "Lütfen hafızaya eklemek istediğiniz satır(ları) seçin.")
            return

        added_count = 0
        for row in selected_rows:
            item = self.table.item(row, 0)
            if item:
                r = item.data(Qt.UserRole)
                col = "#bc8cff" if "Oyun" in r['category'] else ("#f2cc60" if "Kripto" in r['category'] else "#58a6ff")
                self.mgr.add(
                    offset=r['offset'],
                    label=r['suggested_label'],
                    category=r['category'],
                    color=col,
                    length=r.get('length', 4),
                    notes=f"Otomatik Bulundu: {r['name']} ({r['confidence']})"
                )
                added_count += 1

        self.annotations_added.emit()
        QMessageBox.information(
            self, 
            "Hafızaya Alındı", 
            f"✅ {added_count} adet değerli ofset başarıyla onaylandı ve Hafıza / Bağlam Haritasına kaydedildi!"
        )
