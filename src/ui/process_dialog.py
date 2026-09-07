from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QSplitter, QMessageBox, QGroupBox
)
from src.core.data_source import get_running_processes, get_process_modules, ProcessSource
from src.core.elevation import is_admin, restart_as_admin

class ProcessSelectorDialog(QDialog):
    """
    Process & Application selector dialog.
    Allows user to select any running Windows application and inspect its live memory/modules.
    Supports on-demand UAC Administrator elevation.
    """
    process_selected = Signal(ProcessSource)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Application / Process - yweinHEX")
        self.resize(850, 590)
        self.all_processes = []
        self._init_ui()
        self.refresh_processes()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # Admin Elevation Banner if not admin
        if not is_admin():
            admin_banner = QGroupBox()
            admin_banner.setStyleSheet("QGroupBox { background-color: #2b1d0c; border: 1px solid #9e6a03; border-radius: 6px; margin-top: 0; padding: 4px; }")
            b_layout = QHBoxLayout(admin_banner)
            b_layout.setContentsMargins(10, 6, 10, 6)

            lbl_warn = QLabel("⚠️ <b>Standart Kullanıcı Modu:</b> Oyunlar ve korumalı uygulamaların belleğini okumak için Yönetici yetkisi gerekebilir.")
            lbl_warn.setStyleSheet("color: #ffd166; font-size: 12px;")
            b_layout.addWidget(lbl_warn)
            b_layout.addStretch()

            btn_elevate = QPushButton("🛡️ Yönetici Olarak Yeniden Başlat")
            btn_elevate.setStyleSheet("background-color: #9e6a03; color: #ffffff; border: 1px solid #d29922; font-weight: bold; padding: 4px 10px;")
            btn_elevate.clicked.connect(self._prompt_elevation)
            b_layout.addWidget(btn_elevate)

            layout.addWidget(admin_banner)

        # Search Bar & Refresh
        top_bar = QHBoxLayout()
        search_lbl = QLabel("Search:")
        search_lbl.setStyleSheet("font-weight: bold; color: #58a6ff;")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter by application name or PID (e.g. notepad, chrome, 1234)...")
        self.search_edit.textChanged.connect(self._filter_processes)

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.clicked.connect(self.refresh_processes)

        top_bar.addWidget(search_lbl)
        top_bar.addWidget(self.search_edit)
        top_bar.addWidget(btn_refresh)
        layout.addLayout(top_bar)

        splitter = QSplitter(Qt.Vertical, self)

        # 1. Process Table
        proc_group = QGroupBox("Running Applications & Processes")
        proc_layout = QVBoxLayout(proc_group)
        self.proc_table = QTableWidget(0, 4, self)
        self.proc_table.setHorizontalHeaderLabels(["PID", "Application Name", "Memory (RSS)", "Path"])
        self.proc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.proc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.proc_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.proc_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.proc_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.proc_table.setSelectionMode(QTableWidget.SingleSelection)
        self.proc_table.setAlternatingRowColors(True)
        self.proc_table.itemSelectionChanged.connect(self._on_process_selected)
        proc_layout.addWidget(self.proc_table)
        splitter.addWidget(proc_group)

        # 2. Modules Table
        mod_group = QGroupBox("Loaded Modules & Executable Memory Regions")
        mod_layout = QVBoxLayout(mod_group)
        self.mod_table = QTableWidget(0, 4, self)
        self.mod_table.setHorizontalHeaderLabels(["Module Name", "Base Address", "Image Size", "Entry Point"])
        self.mod_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.mod_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.mod_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.mod_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.mod_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.mod_table.setSelectionMode(QTableWidget.SingleSelection)
        self.mod_table.setAlternatingRowColors(True)
        self.mod_table.doubleClicked.connect(self._on_accept_module)
        mod_layout.addWidget(self.mod_table)
        splitter.addWidget(mod_group)

        splitter.setSizes([320, 200])
        layout.addWidget(splitter)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.status_lbl = QLabel("Select a process to inspect.")
        self.status_lbl.setStyleSheet("color: #8b949e;")
        btn_layout.addWidget(self.status_lbl)
        btn_layout.addStretch()

        self.btn_inspect = QPushButton("Inspect Process Memory")
        self.btn_inspect.setObjectName("primaryButton")
        self.btn_inspect.clicked.connect(self._on_accept_module)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_inspect)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

    def refresh_processes(self):
        self.all_processes = get_running_processes()
        self._populate_process_table(self.all_processes)

    def _populate_process_table(self, procs):
        self.proc_table.setRowCount(0)
        self.mod_table.setRowCount(0)
        self.proc_table.setRowCount(len(procs))

        for row, p in enumerate(procs):
            pid_item = QTableWidgetItem(str(p['pid']))
            pid_item.setData(Qt.UserRole, p)
            name_item = QTableWidgetItem(p['name'])
            mem_item = QTableWidgetItem(p['memory_str'])
            path_item = QTableWidgetItem(p['exe'])

            self.proc_table.setItem(row, 0, pid_item)
            self.proc_table.setItem(row, 1, name_item)
            self.proc_table.setItem(row, 2, mem_item)
            self.proc_table.setItem(row, 3, path_item)

        self.status_lbl.setText(f"Found {len(procs)} active processes.")

    def _filter_processes(self, query: str):
        query = query.strip().lower()
        if not query:
            self._populate_process_table(self.all_processes)
            return

        filtered = [
            p for p in self.all_processes
            if query in p['name'].lower() or query in str(p['pid']) or query in p['exe'].lower()
        ]
        self._populate_process_table(filtered)

    def _on_process_selected(self):
        selected = self.proc_table.selectedItems()
        if not selected:
            return

        p_data = self.proc_table.item(selected[0].row(), 0).data(Qt.UserRole)
        pid = p_data['pid']
        modules = get_process_modules(pid)

        self.mod_table.setRowCount(len(modules))
        for row, m in enumerate(modules):
            name_item = QTableWidgetItem(m['name'])
            name_item.setData(Qt.UserRole, m)
            base_item = QTableWidgetItem(m['base_hex'])
            size_item = QTableWidgetItem(m['size_str'])
            entry_item = QTableWidgetItem(m['entry_hex'])

            self.mod_table.setItem(row, 0, name_item)
            self.mod_table.setItem(row, 1, base_item)
            self.mod_table.setItem(row, 2, size_item)
            self.mod_table.setItem(row, 3, entry_item)

        if modules:
            self.mod_table.selectRow(0)
            self.status_lbl.setText(f"Process {p_data['name']} (PID: {pid}) - {len(modules)} modules loaded.")
        else:
            self.status_lbl.setText(f"Process {p_data['name']} (PID: {pid}) - Protected system process or access restricted.")

    def _on_accept_module(self):
        # Determine target module or process
        mod_selected = self.mod_table.selectedItems()
        proc_selected = self.proc_table.selectedItems()

        if not proc_selected:
            QMessageBox.warning(self, "Warning", "Please select a process first.")
            return

        p_data = self.proc_table.item(proc_selected[0].row(), 0).data(Qt.UserRole)
        pid = p_data['pid']

        if mod_selected:
            m_data = self.mod_table.item(mod_selected[0].row(), 0).data(Qt.UserRole)
            base_addr = m_data['base_address']
            size = m_data['size']
            mod_name = m_data['name']
        else:
            # Fallback to default region of 1MB at default base
            base_addr = 0x00400000
            size = 0x100000
            mod_name = p_data['name']

        source = ProcessSource(pid=pid, base_address=base_addr, region_size=size, module_name=mod_name)
        if not source.h_process:
            reply = QMessageBox.question(
                self, 
                "Yetki Hatası / Yönetici İzni Gerekli", 
                f"'{p_data['name']}' (PID: {pid}) sürecine erişim reddedildi.\n\n"
                "Oyunlar ve korumalı uygulamaların belleğini incelemek için Yönetici (Administrator) yetkisi gerekir.\n\n"
                "Uygulama şimdi Yönetici olarak yeniden başlatılsın mı?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self._prompt_elevation()
            return

        self.process_selected.emit(source)
        self.accept()

    def _prompt_elevation(self):
        if not restart_as_admin():
            QMessageBox.warning(self, "Uyarı", "Yönetici izni verilmedi veya UAC isteği iptal edildi.")
