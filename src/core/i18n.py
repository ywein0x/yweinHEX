"""
Internationalization (i18n) module for yweinHEX.
Provides Turkish (tr) and English (en) translations.
"""

from typing import Dict

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "tr": {
        "app_title": "yweinHEX - Yeni Nesil Hex & Binary İnceleyici",
        "menu_file": "&Dosya",
        "menu_edit": "&Düzenle",
        "menu_analysis": "&Analiz",
        "menu_view": "&Görünüm",
        "menu_language": "&Dil (Language)",
        "menu_help": "&Yardım",

        "act_open_file": "Dosya Aç...",
        "act_open_proc": "Uygulama / Süreç İncele...",
        "act_close": "Kapat",
        "act_exit": "Çıkış",
        "act_find": "Desen / Metin Ara...",
        "act_goto": "Ofsete Git...",
        "act_select_all": "Tümünü Seç",
        "act_pe": "PE & Binary Başlıkları...",
        "act_strings": "Metinleri (Strings) Çıkar...",
        "act_entropy": "Shannon Entropi Grafiği...",
        "act_hashes": "Özetler ve Sağlama (Hashes)...",
        "act_smart_scan": "🧠 Akıllı Ofset & Desen Avcısı...",
        "act_dumper": "⚡ Oyun & Süreç Ofset Dumper...",
        "act_add_note": "📝 Hafızaya / Notlara Ekle...",
        "act_about": "yweinHEX Hakkında",

        "dock_inspector": "Canlı Veri İnceleyici",
        "dock_context": "Hafıza, Notlar & Bağlam Haritası",

        "status_ready": "Hazır",
        "status_offset": "Ofset",
        "status_byte": "Bayt",
        "status_sel": "Seçim",
        "status_size": "Boyut",
        "status_format": "Format",

        "inspector_title": "CANLI VERİ İNCELEYİCİ",
        "inspector_tip": "💡 İpucu: Herhangi bir satıra çift tıklayarak değeri kopyalayabilirsiniz.",

        "context_title": "HAFIZA & BAĞLAM HARİTASI",
        "context_add_btn": "+ Not / Ofset Ekle",
        "context_export_btn": "Dışa Aktar (JSON)",
        "context_clear_btn": "Temizle",
        "context_table_offset": "Ofset",
        "context_table_label": "Açıklama / İsim",
        "context_table_target": "Bağlantılı Hedef (Pointer)",
        "context_table_cat": "Kategori",
        "context_link_hint": "💡 Bağlantı (Pointer): Bir ofset başka bir adresi işaret ettiğinde otomatik bağ kurulur.",

        "scanner_title": "🧠 Akıllı Değerli Ofset & Desen Avcısı",
        "scanner_btn_scan": "Taramayı Başlat",
        "scanner_btn_save_selected": "Seçilenleri Hafızaya Kaydet",
        "scanner_searching": "İkili veri taranıyor...",
        "scanner_col_offset": "Ofset",
        "scanner_col_category": "Kategori",
        "scanner_col_name": "Tespit Edilen Varlık / Desen",
        "scanner_col_confidence": "Güvenilirlik",
        "scanner_col_preview": "Önizleme / Detay",
        "scanner_filter_placeholder": "Sonuçları filtrele...",
    },
    "en": {
        "app_title": "yweinHEX - Next-Gen Hex & Binary Inspector",
        "menu_file": "&File",
        "menu_edit": "&Edit",
        "menu_analysis": "&Analysis",
        "menu_view": "&View",
        "menu_language": "&Language (Dil)",
        "menu_help": "&Help",

        "act_open_file": "Open File...",
        "act_open_proc": "Inspect Application / Process...",
        "act_close": "Close",
        "act_exit": "Exit",
        "act_find": "Find Pattern / Text...",
        "act_goto": "Go to Offset...",
        "act_select_all": "Select All",
        "act_pe": "PE & Binary Headers...",
        "act_strings": "Extract Strings...",
        "act_entropy": "Shannon Entropy Graph...",
        "act_hashes": "Checksums & Hashes...",
        "act_smart_scan": "🧠 Smart Offset & Pattern Hunter...",
        "act_dumper": "⚡ Game & Process Offset Dumper...",
        "act_add_note": "📝 Add to Memory / Annotations...",
        "act_about": "About yweinHEX",

        "dock_inspector": "Data Inspector",
        "dock_context": "Memory, Notes & Context Map",

        "status_ready": "Ready",
        "status_offset": "Offset",
        "status_byte": "Byte",
        "status_sel": "Sel",
        "status_size": "Size",
        "status_format": "Format",

        "inspector_title": "DATA INSPECTOR",
        "inspector_tip": "💡 Tip: Double-click any row to copy value.",

        "context_title": "MEMORY & CONTEXT MAP",
        "context_add_btn": "+ Add Note / Offset",
        "context_export_btn": "Export (JSON)",
        "context_clear_btn": "Clear",
        "context_table_offset": "Offset",
        "context_table_label": "Description / Name",
        "context_table_target": "Linked Target (Pointer)",
        "context_table_cat": "Category",
        "context_link_hint": "💡 Context Linker: Links are automatically drawn when an offset contains a pointer.",

        "scanner_title": "🧠 Smart Offset & Pattern Hunter",
        "scanner_btn_scan": "Start Scan",
        "scanner_btn_save_selected": "Save Selected to Memory",
        "scanner_searching": "Scanning binary data...",
        "scanner_col_offset": "Offset",
        "scanner_col_category": "Category",
        "scanner_col_name": "Detected Entity / Pattern",
        "scanner_col_confidence": "Confidence",
        "scanner_col_preview": "Preview / Details",
        "scanner_filter_placeholder": "Filter results...",
    }
}

CURRENT_LANG = "tr"

def set_language(lang_code: str):
    global CURRENT_LANG
    if lang_code in TRANSLATIONS:
        CURRENT_LANG = lang_code

def get_language() -> str:
    return CURRENT_LANG

def tr(key: str, default: str = "") -> str:
    """Translate key based on current language."""
    lang_dict = TRANSLATIONS.get(CURRENT_LANG, TRANSLATIONS["tr"])
    return lang_dict.get(key, default or key)
