# ⚡ yweinHEX - Next-Gen Hex & Binary Inspector

<div align="center">

```text
               .__        ___ ___ __________  ___
 ___ _____  _  |__| ____ |   |   \\______   \/   \
|   |   \ \/ \/ /  |/    \|   |   / |    |  _/\   /
 \_____  /\     /|  |   |  \      \ |    |   \/   \
 /        \\/\_/ |__|___|  /___|  / |______  /__/\_\
 \_______/               \/     \/         \/       
```

**Modern, Yüksek Performanslı ve Siber Temalı Hex / Binary İnceleme & Tersine Mühendislik Aracı**  
*Disk Dosyalarını ve Canlı Windows Süreç Belleğini (Process Memory) İnceleyin, Akıllı Desenleri Avlayın ve Bağlam Haritaları Çıkarın.*

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6%20Qt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://pypi.org/project/PySide6/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](LICENSE)

</div>

---

## 🌟 Çoğu Hex Editöründe Olmayan Yeni Nesil Özellikler

### 1. 🧠 Otomatik Değerli Ofset & Desen Avcısı (Smart Pattern Hunter)
Standart hex editörlerinin aksine, `yweinHEX` açılan dosyayı veya seçtiğiniz canlı `.exe` sürecini otomatik olarak tarar ve değerli yapıları isimleriyle bulur:
- **Oyun Motoru Tespiti:** Unity (IL2CPP / Mono metaverileri, `PlayerPrefs`), Unreal Engine (`GWorld`, `GNames`, `FNamePool`), Godot Engine.
- **Oyun Değişkenleri & Can Deseni:** Tipik float can barları (örneğin `100.0f` Current / `100.0f` Max Health), 4-bayt sayaçlar ve kaynak yapıları.
- **Kriptografik Sabitler (FindCrypt Benzeri):** AES Rijndael S-Box, SHA-256 K sabitleri, MD5 sabitleri ve CRC32 polinomları.
- **Kritik API & Ağ Çağrıları:** `VirtualAlloc`, `WriteProcessMemory`, `CreateRemoteThread`, `IsDebuggerPresent`, Winsock soketleri ve gömülü URL'ler.
- **Onaylı Hafızaya Kaydetme:** Bulunan desenleri tek tıkla inceleyip istediğinizi hafızaya aktarabilirsiniz!

### 2. 📝 Hafıza, Not ve Görsel Bağlam Sistemi (Annotation & Context Linker)
- **Hafıza & Not Alma:** İncelediğiniz herhangi bir ofseti (`Ctrl+N`) kendi onayınızla hafızaya alabilir, etiket (örneğin *"Can Struct Başlangıcı"*, *"Oyuncu Pointer"*) ve kategori atayabilirsiniz.
- **🔗 Görsel Bağlam Bağlayıcı (Context Linker):** Bir ofsetteki 32/64-bit değer başka bir adresi işaret ediyorsa, iki ofset arasında otomatik ilişki kurulur (`➜ Hedef Ofset`).
- **Oklar ve Hex Üzerinde Vurgu:** İlgili ofsetler hex ekranında renkli vurgulanır ve sol ofset sütununda pointer bağı olduğunu belirten parlayan oklar (`➜`) çizilir.
- **Dışa/İçe Aktarma:** Hafızadaki tüm notları ve bağlamları JSON olarak kaydedebilir, arkadaşlarınızla paylaşabilir veya GitHub deponuza koyabilirsiniz.

### 3. ⚡ Oyun & Süreç Ofset Dumper (Offset Dumper - Ctrl+D)
Oyuna girip çalışan `.exe` sürecini seçtikten sonra tek tıkla ofsetleri otomatik olarak dump eder:
- **Otomatik Çıkarılan Ofsetler:** `dwLocalPlayer` (Yerel Oyuncu), `dwEntityList` (Varlık Listesi), `dwViewMatrix` (Kamera Matrisi), `GWorld` / `GNames` (Unreal Engine), `m_iHealth` (Can Değeri), `m_vecOrigin` (Pozisyon) ve yüklü tüm modüllerin taban adresleri (`base_client_dll`, `base_UnityPlayer_dll` vb.).
- **Tek Tıkla Dışa Aktarma:**
  - **C++ Header (`.hpp`):** `namespace Offsets { constexpr uintptr_t ... = ...; }`
  - **C# Sınıfı (`.cs`):** `public static class Offsets { public const int ... = ...; }`
  - **Python (`.py`):** `class Offsets: ... = ...`
  - **JSON (`.json`):** Tüm ofsetleri ve açıklamalarını içeren veri yapısı.
- **Hafızaya & Notlara Aktar:** Çıkarılan ofsetleri tek tıkla yweinHEX'in Hafıza ve Bağlam Haritasına ekleyerek canlı incelemeye devam edebilirsiniz!

### 4. 🔄 Çift Modlu İnceleme (Dosya & Canlı Uygulama/Process)
- **Disk Dosyaları:** GB'larca büyüklükteki dosyaları dahi RAM'i şişirmeden sanal kaydırma (`mmap` / chunked reading) ile 60 FPS akıcılıkta açar.
- **Canlı Süreçler (`Ctrl+P`):** Windows üzerinde çalışan herhangi bir oyunu veya uygulamayı seçin; modülleri (`.exe`, `.dll`) ve sanal bellek bölgelerini canlı inceleyin.

### 5. 🇹🇷 Tam Türkçe & Çift Dil Desteği
- Uygulama varsayılan olarak zengin Türkçe arayüz ile gelir. Menüden tek tıkla **Türkçe 🇹🇷** veya **English 🇬🇧** moduna geçiş yapabilirsiniz.

### 5. 🔬 Canlı Veri İnceleyici (Data Inspector)
İmlecin durduğu baytın temsil ettiği veriyi anında şu tiplere dönüştürür:
- **Binary (8-bit):** `01001101`
- **Tamsayılar:** `Int8`, `UInt8`, `Int16`, `UInt16`, `Int32`, `UInt32`, `Int64`, `UInt64`
- **Ondalıklı Sayılar:** `Float (32-bit)`, `Double (64-bit IEEE 754)`
- **Zaman Damgası:** `Unix Timestamp (UTC Tarih)`
- **Endianness Desteği:** Tek tıkla **Little-Endian (LE)** veya **Big-Endian (BE)** moduna geçiş.

### 6. 🛡️ Tek Tıkla Yönetici (UAC) Yetkisi & SeDebugPrivilege
Oyunlar ve korumalı Windows uygulamaları bellek okuma erişimini varsayılan olarak kısıtlar:
- **Otomatik Yetki İsteme:** Korumalı bir oyunu seçtiğinizde veya `OpenProcess` erişimi reddedildiğinde, yweinHEX size sormadan çökmez; *"Yönetici İzni Gerekli, Yeniden Başlatılsın Mı?"* diyerek onayınızı ister.
- **Windows UAC Diyalogu:** Evet dediğinizde Windows UAC ekranı (Kalkan simgesi) tetiklenir ve uygulama tek tıkla tam yetkili olarak açılır.
- **SeDebugPrivilege:** Yönetici olarak çalıştırıldığında Windows `SeDebugPrivilege` hata ayıklama yetkisi otomatik aktif edilir ve korumalı oyunların belleği tam erişimle incelenebilir.
- **Arayüz Üzerinden Erişim:** Araç çubuğundaki **🛡️ Yönetici Yetkisi Ver** butonuyla istediğiniz an tek tıkla yetki yükseltebilirsiniz.

### 7. 🛡️ PE & Binary Başlık Analizi (PE Analyzer)
- DOS Header, COFF File Header (Mimari x86/x64, Timestamp).
- Optional Header (Entry Point, Image Base, Subsystem, ASLR & DEP/NX Güvenlik Bayrakları).
- **Sections Tablosu:** `.text`, `.data`, `.rsrc` vb. bölümlerin sanal/fiziksel adresleri, boyutları, izinleri ve her bölüme özel entropi oranı. Çift tıklayarak ofsete atlama.

### 8. 📊 Shannon Entropi Grafiği & Dizgi (Strings) Çıkarıcı
- Dosya boyunca Shannon entropi dağılımını göstererek şifrelenmiş veya paketlenmiş (packed/obfuscated) kod alanlarını anında tespit etme.
- ASCII ve UTF-16 Unicode metinleri hızlıca tarama ve TXT olarak dışa aktarma.

---

## 🚀 Kurulum

### Gereksinimler
- Python 3.10 veya üzeri
- Windows 10 / 11

### Adım Adım Kurulum

```bash
# 1. Depoyu klonlayın
git clone https://github.com/ywein0x/yweinHEX.git
cd yweinHEX

# 2. Gerekli paketleri yükleyin
pip install -r requirements.txt

# 3. Uygulamayı başlatın
python main.py
```

Doğrudan bir dosyayı incelemek için:
```bash
python main.py "C:\Path\To\Target.exe"
```

---

## ⌨️ Klavye Kısayolları

| Kısayol | İşlev |
| :--- | :--- |
| `Ctrl + O` | Dosya Aç |
| `Ctrl + P` | Çalışan Uygulama / Process Seçici |
| `Ctrl + D` | ⚡ Oyun & Süreç Ofset Dumper |
| `Ctrl + Shift + S` | 🧠 Akıllı Ofset & Desen Avcısı |
| `Ctrl + N` | 📝 Seçili Ofseti Hafızaya / Notlara Ekle |
| `Ctrl + F` | Hex / ASCII / Regex Arama |
| `Ctrl + G` | Ofsete Git (Hex veya Dec) |
| `Ctrl + H` | PE & Binary Başlık İnceleyici |
| `Ctrl + T` | String Çıkarıcı |
| `Ctrl + E` | Shannon Entropi Grafiği |
| `Ctrl + A` | Tümünü Seç |
| `Ctrl + C` | Seçilen Baytları Kopyala |
| `Shift + Oklar` | Bayt Aralığı Seçimi |
| `Alt + F4` | Çıkış |

---

## 📁 Proje Yapısı

```
yweinHEX/
├── main.py                     # Uygulama giriş noktası
├── requirements.txt            # Python bağımlılıkları (PySide6, psutil)
├── README.md                   # Proje dökümantasyonu
├── LICENSE                     # MIT Lisansı
├── .gitignore                  # Git dışlama kuralları
├── tests/
│   ├── test_core.py            # Çekirdek mantık ve ayrıştırma testleri
│   ├── test_gui.py             # Arayüz ve pencere testleri
│   └── test_scanner.py         # Akıllı desen ve bağlam bağlayıcı testleri
└── src/
    ├── core/
    │   ├── data_source.py      # Dosya ve Process bellek soyutlaması
    │   ├── scanner.py          # Akıllı Desen, Oyun/Kripto/API avcısı
    │   ├── annotations.py      # Hafıza, Not ve Pointer Bağlam (Context Linker)
    │   ├── i18n.py             # Türkçe & İngilizce dil motoru
    │   ├── pe_analyzer.py      # PE / COFF ve Magic Byte başlık çözümleyici
    │   ├── entropy.py          # Shannon entropi hesaplama motoru
    │   ├── string_extractor.py # ASCII/UTF-16 string arama motoru
    │   └── hash_calc.py        # Asenkron hash hesaplayıcı
    └── ui/
        ├── styles.py           # Siber-Koyu QSS stil ve renk paleti
        ├── main_window.py      # Ana uygulama penceresi
        ├── hex_widget.py       # 60 FPS Sanal Hex Viewer (Not & Ok vurgulu)
        ├── context_dock.py     # Hafıza, Notlar ve Bağlam Haritası Paneli
        ├── smart_scanner_dlg.py# Akıllı Desen & Değer Avcısı Penceresi
        ├── data_inspector.py   # Gerçek zamanlı tip dönüştürücü paneli
        ├── process_dialog.py   # Windows uygulama / süreç seçici penceresi
        ├── pe_dialog.py        # PE başlıkları ve bölümleri penceresi
        ├── strings_dialog.py   # Metin çıkarıcı penceresi
        ├── entropy_dialog.py   # Entropi dağılım penceresi
        ├── search_dialog.py    # Gelişmiş arama penceresi
        ├── goto_dialog.py      # Ofset atlama penceresi
        └── hash_dialog.py      # Hash ve özet penceresi
```

---

## 📄 Lisans

Bu proje **[MIT Lisansı](LICENSE)** altında lisanslanmıştır.

---

<div align="center">
Geliştirici: <b>ywein0x</b> | GitHub'a yıldız vermeyi unutmayın! ⭐
</div>
