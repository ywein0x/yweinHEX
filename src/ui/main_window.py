import os
from typing import Optional
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon, QKeySequence, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QFileDialog, QMessageBox, QLabel, QToolBar, QStatusBar, QDockWidget
)

from src.core.data_source import DataSource, FileSource, ProcessSource
from src.core.pe_analyzer import PEAnalyzer, detect_file_format
from src.core.annotations import AnnotationManager
from src.core.i18n import tr, set_language, get_language

from src.ui.hex_widget import HexWidget
from src.ui.data_inspector import DataInspector
from src.ui.process_dialog import ProcessSelectorDialog
from src.ui.pe_dialog import PEDialog
from src.ui.strings_dialog import StringsDialog
from src.ui.entropy_dialog import EntropyDialog
from src.ui.search_dialog import SearchDialog
from src.ui.goto_dialog import GotoDialog
from src.ui.hash_dialog import HashDialog
from src.ui.context_dock import ContextDock, AddAnnotationDialog
from src.ui.smart_scanner_dlg import SmartScannerDialog
from src.ui.dumper_dialog import OffsetDumperDialog
from src.core.elevation import is_admin, restart_as_admin

class MainWindow(QMainWindow):
    """
    Main Application Window for yweinHEX with Smart Scanning,
    Memory Annotations, and Context Linker.
    """

    def __init__(self, initial_path: Optional[str] = None):
        super().__init__()
        admin_badge = " [Yönetici / Admin 🛡️]" if is_admin() else ""
        self.setWindowTitle(f"{tr('app_title')}{admin_badge}")
        self.resize(1280, 800)
        self.setAcceptDrops(True)

        self.data_source: Optional[DataSource] = None
        self.pe_analyzer: Optional[PEAnalyzer] = None
        self.annotation_manager = AnnotationManager()

        self._init_ui()
        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._create_statusbar()

        if initial_path and os.path.exists(initial_path):
            self.open_file_path(initial_path)

    def _init_ui(self):
        self.hex_widget = HexWidget(self)
        self.hex_widget.set_annotation_manager(self.annotation_manager)
        self.hex_widget.cursor_changed.connect(self._on_cursor_changed)
        self.hex_widget.selection_changed.connect(self._on_selection_changed)
        self.hex_widget.request_add_annotation.connect(self.prompt_add_annotation)

        # 1. Data Inspector Dock (Right)
        self.data_inspector = DataInspector(self)
        self.dock_inspector = QDockWidget(tr("dock_inspector"), self)
        self.dock_inspector.setWidget(self.data_inspector)
        self.dock_inspector.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_inspector)

        # 2. Memory & Context Linker Dock (Bottom / Right tabbed)
        self.context_dock = ContextDock(self.annotation_manager, self)
        self.context_dock.jump_requested.connect(self.hex_widget.jump_to_offset)
        self.context_dock.annotations_updated.connect(self.hex_widget.update)

        self.dock_context = QDockWidget(tr("dock_context"), self)
        self.dock_context.setWidget(self.context_dock)
        self.dock_context.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_context)

        # Tabify right docks
        self.tabifyDockWidget(self.dock_inspector, self.dock_context)
        self.dock_inspector.raise_()

        self.setCentralWidget(self.hex_widget)

    def _create_actions(self):
        # File Actions
        self.act_open_file = QAction(tr("act_open_file"), self)
        self.act_open_file.setShortcut(QKeySequence.Open)
        self.act_open_file.triggered.connect(self.open_file_dialog)

        self.act_open_proc = QAction(tr("act_open_proc"), self)
        self.act_open_proc.setShortcut("Ctrl+P")
        self.act_open_proc.triggered.connect(self.open_process_dialog)

        self.act_close = QAction(tr("act_close"), self)
        self.act_close.triggered.connect(self.close_source)

        self.act_restart_admin = QAction("🛡️ Yönetici Olarak Yeniden Başlat...", self)
        self.act_restart_admin.triggered.connect(self.request_admin)

        self.act_exit = QAction(tr("act_exit"), self)
        self.act_exit.setShortcut("Alt+F4")
        self.act_exit.triggered.connect(self.close)

        # Edit Actions
        self.act_find = QAction(tr("act_find"), self)
        self.act_find.setShortcut(QKeySequence.Find)
        self.act_find.triggered.connect(self.open_search_dialog)

        self.act_goto = QAction(tr("act_goto"), self)
        self.act_goto.setShortcut("Ctrl+G")
        self.act_goto.triggered.connect(self.open_goto_dialog)

        self.act_select_all = QAction(tr("act_select_all"), self)
        self.act_select_all.setShortcut(QKeySequence.SelectAll)
        self.act_select_all.triggered.connect(self.hex_widget.select_all)

        # Annotation Action
        self.act_add_note = QAction(tr("act_add_note"), self)
        self.act_add_note.setShortcut("Ctrl+N")
        self.act_add_note.triggered.connect(lambda: self.prompt_add_annotation(self.hex_widget.cursor_offset))

        # Analysis Actions
        self.act_smart_scan = QAction(tr("act_smart_scan"), self)
        self.act_smart_scan.setShortcut("Ctrl+Shift+S")
        self.act_smart_scan.triggered.connect(self.open_smart_scanner)

        self.act_dumper = QAction(tr("act_dumper"), self)
        self.act_dumper.setShortcut("Ctrl+D")
        self.act_dumper.triggered.connect(self.open_offset_dumper)

        self.act_pe = QAction(tr("act_pe"), self)
        self.act_pe.setShortcut("Ctrl+H")
        self.act_pe.triggered.connect(self.open_pe_dialog)

        self.act_strings = QAction(tr("act_strings"), self)
        self.act_strings.setShortcut("Ctrl+T")
        self.act_strings.triggered.connect(self.open_strings_dialog)

        self.act_entropy = QAction(tr("act_entropy"), self)
        self.act_entropy.setShortcut("Ctrl+E")
        self.act_entropy.triggered.connect(self.open_entropy_dialog)

        self.act_hashes = QAction(tr("act_hashes"), self)
        self.act_hashes.triggered.connect(self.open_hash_dialog)

        # Languages
        self.act_lang_tr = QAction("Türkçe 🇹🇷", self)
        self.act_lang_tr.triggered.connect(lambda: self.switch_language("tr"))
        self.act_lang_en = QAction("English 🇬🇧", self)
        self.act_lang_en.triggered.connect(lambda: self.switch_language("en"))

        # Help
        self.act_about = QAction(tr("act_about"), self)
        self.act_about.triggered.connect(self.show_about)

    def _create_menus(self):
        menubar = self.menuBar()
        menubar.clear()

        # File Menu
        menu_file = menubar.addMenu(tr("menu_file"))
        menu_file.addAction(self.act_open_file)
        menu_file.addAction(self.act_open_proc)
        menu_file.addSeparator()
        if not is_admin():
            menu_file.addAction(self.act_restart_admin)
            menu_file.addSeparator()
        menu_file.addAction(self.act_close)
        menu_file.addSeparator()
        menu_file.addAction(self.act_exit)

        # Edit Menu
        menu_edit = menubar.addMenu(tr("menu_edit"))
        menu_edit.addAction(self.act_find)
        menu_edit.addAction(self.act_goto)
        menu_edit.addSeparator()
        menu_edit.addAction(self.act_add_note)
        menu_edit.addSeparator()
        menu_edit.addAction(self.act_select_all)

        # Analysis Menu
        menu_analysis = menubar.addMenu(tr("menu_analysis"))
        menu_analysis.addAction(self.act_smart_scan)
        menu_analysis.addAction(self.act_dumper)
        menu_analysis.addSeparator()
        menu_analysis.addAction(self.act_pe)
        menu_analysis.addAction(self.act_strings)
        menu_analysis.addAction(self.act_entropy)
        menu_analysis.addSeparator()
        menu_analysis.addAction(self.act_hashes)

        # View Menu
        menu_view = menubar.addMenu(tr("menu_view"))
        menu_view.addAction(self.dock_inspector.toggleViewAction())
        menu_view.addAction(self.dock_context.toggleViewAction())

        # Language Menu
        menu_lang = menubar.addMenu(tr("menu_language"))
        menu_lang.addAction(self.act_lang_tr)
        menu_lang.addAction(self.act_lang_en)

        # Help Menu
        menu_help = menubar.addMenu(tr("menu_help"))
        menu_help.addAction(self.act_about)

    def _create_toolbar(self):
        # Remove existing toolbars
        for tb in self.findChildren(QToolBar):
            self.removeToolBar(tb)

        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        toolbar.addAction(self.act_open_file)
        toolbar.addAction(self.act_open_proc)
        toolbar.addSeparator()
        if not is_admin():
            toolbar.addAction(self.act_restart_admin)
            toolbar.addSeparator()
        toolbar.addAction(self.act_smart_scan)
        toolbar.addAction(self.act_dumper)
        toolbar.addAction(self.act_add_note)
        toolbar.addSeparator()
        toolbar.addAction(self.act_find)
        toolbar.addAction(self.act_goto)
        toolbar.addSeparator()
        toolbar.addAction(self.act_pe)
        toolbar.addAction(self.act_strings)
        toolbar.addAction(self.act_entropy)
        toolbar.addAction(self.act_hashes)

    def _create_statusbar(self):
        sb = self.statusBar()
        self.lbl_status_offset = QLabel(f"{tr('status_offset')}: 0x00000000 (0)")
        self.lbl_status_val = QLabel(f"{tr('status_byte')}: -")
        self.lbl_status_sel = QLabel(f"{tr('status_sel')}: 0 B")
        self.lbl_status_size = QLabel(f"{tr('status_size')}: 0 B")
        self.lbl_status_format = QLabel(f"{tr('status_format')}: -")
        self.lbl_status_source = QLabel(tr("status_ready"))

        sb.addWidget(self.lbl_status_source, 2)
        sb.addPermanentWidget(self.lbl_status_format, 2)
        sb.addPermanentWidget(self.lbl_status_offset, 1)
        sb.addPermanentWidget(self.lbl_status_val, 1)
        sb.addPermanentWidget(self.lbl_status_sel, 1)
        sb.addPermanentWidget(self.lbl_status_size, 1)

    def switch_language(self, lang_code: str):
        set_language(lang_code)
        self.setWindowTitle(tr("app_title"))
        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self.dock_inspector.setWindowTitle(tr("dock_inspector"))
        self.dock_context.setWindowTitle(tr("dock_context"))
        self.statusBar().showMessage(f"Language set to: {'Türkçe' if lang_code == 'tr' else 'English'}", 2000)

    def prompt_add_annotation(self, offset: int):
        """Prompt user to confirm and add a valuable offset to memory."""
        if not self.data_source:
            return
        dlg = AddAnnotationDialog(offset=offset, parent=self)
        if dlg.exec() == AddAnnotationDialog.Accepted and dlg.confirmed_ann:
            ann = dlg.confirmed_ann
            self.annotation_manager.add(
                offset=ann.offset,
                label=ann.label,
                category=ann.category,
                color=ann.color,
                length=ann.length
            )
            # Try to resolve pointer link automatically
            self.annotation_manager.resolve_pointer_link(ann, self.data_source)
            self.context_dock.refresh()
            self.hex_widget.update()

    def open_smart_scanner(self):
        if not self.data_source or self.data_source.size == 0:
            QMessageBox.information(self, "Bilgi", "Lütfen önce bir dosya veya çalışan süreç açın.")
            return
        dlg = SmartScannerDialog(self.data_source, self.annotation_manager, self)
        dlg.jump_requested.connect(self.hex_widget.jump_to_offset)
        dlg.annotations_added.connect(self.context_dock.refresh)
        dlg.annotations_added.connect(self.hex_widget.update)
        dlg.exec()

    def open_offset_dumper(self):
        if not self.data_source or self.data_source.size == 0:
            QMessageBox.information(self, "Bilgi", "Lütfen önce bir oyun, uygulama veya dosya seçin.")
            return
        dlg = OffsetDumperDialog(self.data_source, self.annotation_manager, self)
        dlg.jump_requested.connect(self.hex_widget.jump_to_offset)
        dlg.annotations_added.connect(self.context_dock.refresh)
        dlg.annotations_added.connect(self.hex_widget.update)
        dlg.exec()

    def request_admin(self):
        """Requests elevation to Windows Administrator via UAC prompt."""
        if is_admin():
            QMessageBox.information(self, "Bilgi", "Uygulama zaten Yönetici (Administrator) yetkileriyle çalışıyor.")
            return

        reply = QMessageBox.question(
            self,
            "Yönetici Yetkisi Ver",
            "Oyunlar ve korumalı uygulamaların belleğini incelemek için Yönetici (Administrator) yetkisi gerekiyor.\n\n"
            "Windows UAC onayı ile uygulama Yönetici olarak yeniden başlatılsın mı?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            if not restart_as_admin():
                QMessageBox.warning(self, "Uyarı", "Yönetici izni verilmedi veya işlem kullanıcı tarafından iptal edildi.")

    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "İncelemek İçin Dosya Seçin", 
            "", 
            "Tüm Dosyalar (*.*);;Çalıştırılabilir & DLL (*.exe *.dll *.sys *.bin);;Arşivler (*.zip *.7z *.tar *.apk)"
        )
        if path:
            self.open_file_path(path)

    def open_file_path(self, filepath: str):
        try:
            if self.data_source:
                self.data_source.close()

            self.data_source = FileSource(filepath)
            self.hex_widget.set_data_source(self.data_source)
            self.context_dock.set_data_source(self.data_source)
            self.pe_analyzer = PEAnalyzer(self.data_source)

            # Detect format
            prefix = self.data_source.read(0, 256)
            fmt = detect_file_format(prefix)

            # Update status
            size = self.data_source.size
            size_str = f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / (1024*1024):.2f} MB"
            self.lbl_status_source.setText(f"📁 {os.path.basename(filepath)}")
            self.lbl_status_size.setText(f"{tr('status_size')}: {size_str} ({size:,} B)")
            self.lbl_status_format.setText(f"{tr('status_format')}: {fmt}")
            self.setWindowTitle(f"yweinHEX - {os.path.basename(filepath)} ({size_str})")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Dosya açılamadı: {e}")

    def open_process_dialog(self):
        dlg = ProcessSelectorDialog(self)
        dlg.process_selected.connect(self._on_process_attached)
        dlg.exec()

    def _on_process_attached(self, process_source: ProcessSource):
        if self.data_source:
            self.data_source.close()

        self.data_source = process_source
        self.hex_widget.set_data_source(self.data_source)
        self.context_dock.set_data_source(self.data_source)
        self.pe_analyzer = PEAnalyzer(self.data_source)

        prefix = self.data_source.read(0, 256)
        fmt = detect_file_format(prefix)

        size = self.data_source.size
        size_str = f"{size / 1024:.1f} KB" if size < 1024*1024 else f"{size / (1024*1024):.2f} MB"
        self.lbl_status_source.setText(f"⚡ Süreç: {self.data_source.name}")
        self.lbl_status_size.setText(f"{tr('status_size')}: {size_str}")
        self.lbl_status_format.setText(f"{tr('status_format')}: {fmt}")
        self.setWindowTitle(f"yweinHEX - {self.data_source.name}")

    def close_source(self):
        if self.data_source:
            self.data_source.close()
            self.data_source = None
            self.pe_analyzer = None
            self.hex_widget.set_data_source(None)
            self.context_dock.set_data_source(None)
            self.data_inspector.update_data(b"")
            self.lbl_status_source.setText(tr("status_ready"))
            self.lbl_status_size.setText(f"{tr('status_size')}: 0 B")
            self.lbl_status_format.setText(f"{tr('status_format')}: -")
            self.lbl_status_offset.setText(f"{tr('status_offset')}: 0x00000000 (0)")
            self.lbl_status_val.setText(f"{tr('status_byte')}: -")
            self.lbl_status_sel.setText(f"{tr('status_sel')}: 0 B")
            self.setWindowTitle(tr("app_title"))

    def open_search_dialog(self):
        if not self.data_source or self.data_source.size == 0:
            QMessageBox.information(self, "Bilgi", "Lütfen önce bir dosya veya süreç açın.")
            return
        dlg = SearchDialog(self.data_source, self.hex_widget.cursor_offset, self)
        dlg.jump_requested.connect(self.hex_widget.jump_to_offset)
        dlg.exec()

    def open_goto_dialog(self):
        if not self.data_source or self.data_source.size == 0:
            return
        dlg = GotoDialog(self.hex_widget.cursor_offset, self.data_source.size, self)
        dlg.jump_requested.connect(self.hex_widget.jump_to_offset)
        dlg.exec()

    def open_pe_dialog(self):
        if not self.data_source or self.data_source.size == 0:
            QMessageBox.information(self, "Bilgi", "Lütfen önce bir dosya veya süreç açın.")
            return
        if not self.pe_analyzer or not self.pe_analyzer.is_pe:
            QMessageBox.warning(self, "PE Başlığı Yok", "Seçilen veri geçerli bir PE/MZ imzası içermiyor.")
            return
        dlg = PEDialog(self.pe_analyzer, self)
        dlg.jump_requested.connect(self.hex_widget.jump_to_offset)
        dlg.exec()

    def open_strings_dialog(self):
        if not self.data_source or self.data_source.size == 0:
            QMessageBox.information(self, "Bilgi", "Lütfen önce bir dosya veya süreç açın.")
            return
        dlg = StringsDialog(self.data_source, self)
        dlg.jump_requested.connect(self.hex_widget.jump_to_offset)
        dlg.exec()

    def open_entropy_dialog(self):
        if not self.data_source or self.data_source.size == 0:
            QMessageBox.information(self, "Bilgi", "Lütfen önce bir dosya veya süreç açın.")
            return
        dlg = EntropyDialog(self.data_source, self)
        dlg.jump_requested.connect(self.hex_widget.jump_to_offset)
        dlg.exec()

    def open_hash_dialog(self):
        if not self.data_source or self.data_source.size == 0:
            QMessageBox.information(self, "Bilgi", "Lütfen önce bir dosya veya süreç açın.")
            return
        dlg = HashDialog(self.data_source, self)
        dlg.exec()

    def _on_cursor_changed(self, offset: int):
        if not self.data_source:
            return
        
        display_addr = self.data_source.base_address + offset
        if self.data_source.base_address > 0xFFFFFFFF:
            self.lbl_status_offset.setText(f"{tr('status_offset')}: 0x{display_addr:016X} ({offset:,})")
        else:
            self.lbl_status_offset.setText(f"{tr('status_offset')}: 0x{display_addr:08X} ({offset:,})")

        # Read up to 8 bytes for data inspector
        raw = self.data_source.read(offset, 8)
        self.data_inspector.update_data(raw)

        if raw:
            b0 = raw[0]
            ch = chr(b0) if 0x20 <= b0 <= 0x7E else "."
            self.lbl_status_val.setText(f"{tr('status_byte')}: 0x{b0:02X} ('{ch}')")

    def _on_selection_changed(self, start: int, length: int):
        if length <= 0:
            self.lbl_status_sel.setText(f"{tr('status_sel')}: 0 B")
        elif length < 1024:
            self.lbl_status_sel.setText(f"{tr('status_sel')}: {length} B")
        else:
            self.lbl_status_sel.setText(f"{tr('status_sel')}: {length / 1024:.1f} KB")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            filepath = urls[0].toLocalFile()
            if os.path.isfile(filepath):
                self.open_file_path(filepath)

    def show_about(self):
        QMessageBox.about(
            self,
            "yweinHEX Hakkında",
            "<h3>⚡ yweinHEX v1.2.0</h3>"
            "<p>Yeni Nesil Siber Temalı Hex & Binary İnceleyici ve Tersine Mühendislik Asistanı.</p>"
            "<p><b>Öne Çıkan Gelişmiş Özellikler:</b></p>"
            "<ul>"
            "<li><b>🧠 Akıllı Ofset & Desen Avcısı:</b> Oyun motoru (Unity/Unreal), Can (100.0f vb.) ve Kripto sabitleri otomatik bulucu.</li>"
            "<li><b>📝 Hafıza ve Not Sistemi:</b> Değerli ofsetleri onaylayarak hafızaya kaydetme ve etiketleme.</li>"
            "<li><b>🔗 Bağlam Bağlayıcı (Context Linker):</b> Birbiriyle ilişkili ofsetleri ve pointer referanslarını oklarla gösterme.</li>"
            "<li><b>Çift Mod:</b> Disk dosyaları ve Canlı Windows Uygulama Belleği (Process Memory) inceleme.</li>"
            "<li><b>60 FPS Sanal Hex Görünümü:</b> Sözdizimi renklendirme ve not vurguları.</li>"
            "<li><b>Canlı Veri İnceleyici:</b> Int8/16/32/64, Float, Double, Endianness, Timestamp.</li>"
            "<li><b>PE Header ve Shannon Entropi:</b> Şifreli/paketlenmiş zararlı kod tespiti.</li>"
            "</ul>"
            "<p>Geliştirici: <b>ywein0x</b> | Lisans: MIT</p>"
        )

    def closeEvent(self, event):
        if self.data_source:
            self.data_source.close()
        super().closeEvent(event)
