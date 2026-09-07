from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QProgressBar, QApplication, QGroupBox
)
from src.core.hash_calc import HashWorker

class HashDialog(QDialog):
    """
    Cryptographic hashes & checksums dialog computed via background worker.
    """

    def __init__(self, data_source, parent=None):
        super().__init__(parent)
        self.data_source = data_source
        self.setWindowTitle("File / Memory Checksums - yweinHEX")
        self.setFixedSize(580, 320)
        self.worker = None
        self._init_ui()
        self._start_calc()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        group = QGroupBox("Cryptographic Hashes")
        g_layout = QVBoxLayout(group)
        g_layout.setSpacing(8)

        self.hash_edits = {}
        for name in ["MD5", "SHA-1", "SHA-256", "CRC32"]:
            row = QHBoxLayout()
            lbl = QLabel(f"{name}:")
            lbl.setFixedWidth(70)
            lbl.setStyleSheet("font-weight: bold; color: #58a6ff;")

            edit = QLineEdit("Calculating...")
            edit.setReadOnly(True)
            self.hash_edits[name] = edit

            btn_copy = QPushButton("Copy")
            btn_copy.setFixedWidth(60)
            btn_copy.clicked.connect(lambda checked=False, e=edit: QApplication.clipboard().setText(e.text()))

            row.addWidget(lbl)
            row.addWidget(edit)
            row.addWidget(btn_copy)
            g_layout.addLayout(row)

        layout.addWidget(group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        bottom = QHBoxLayout()
        self.status_lbl = QLabel("Hashing in progress...")
        self.status_lbl.setStyleSheet("color: #8b949e;")
        bottom.addWidget(self.status_lbl)
        bottom.addStretch()

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.close)
        bottom.addWidget(btn_close)
        layout.addLayout(bottom)

    def _start_calc(self):
        self.worker = HashWorker(self.data_source)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.hashes_ready.connect(self._on_hashes_ready)
        self.worker.start()

    def _on_hashes_ready(self, results):
        self.hash_edits["MD5"].setText(results.get('md5', ''))
        self.hash_edits["SHA-1"].setText(results.get('sha1', ''))
        self.hash_edits["SHA-256"].setText(results.get('sha256', ''))
        self.hash_edits["CRC32"].setText(results.get('crc32', ''))

        self.progress_bar.setValue(100)
        if results.get('partial'):
            self.status_lbl.setText("Hashes computed for the first 500 MB.")
        else:
            self.status_lbl.setText("Hashes calculated successfully.")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(500)
        super().closeEvent(event)
