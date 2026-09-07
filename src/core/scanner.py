import re
import struct
from typing import List, Dict, Any

# Cryptographic signatures (hex patterns)
CRYPTO_PATTERNS = [
    {
        'name': 'AES Rijndael S-Box',
        'category': 'Kripto / Güvenlik',
        'bytes': bytes([
            0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5,
            0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76
        ]),
        'confidence': '99%'
    },
    {
        'name': 'SHA-256 Başlangıç K Sabitleri (H0-H3)',
        'category': 'Kripto / Güvenlik',
        'bytes': bytes.fromhex("67e6096a 85ae67bb 72f36e3c 3af54fa5"),
        'confidence': '98%'
    },
    {
        'name': 'MD5 Başlangıç Durum Sabitleri',
        'category': 'Kripto / Güvenlik',
        'bytes': bytes.fromhex("01234567 89abcdef fedcba98 76543210"),
        'confidence': '95%'
    },
    {
        'name': 'CRC32 Ters Çevrilmiş Polinom (0xEDB88320)',
        'category': 'Kripto / Güvenlik',
        'bytes': bytes.fromhex("2083b8ed"),
        'confidence': '85%'
    },
]

# Engine & Game Signatures
GAME_ENGINE_PATTERNS = [
    {
        'name': 'Unity IL2CPP / Meta Veri İmzası',
        'category': 'Oyun Motoru',
        'regex': re.compile(rb"(?:il2cpp|GameAssembly\.dll|UnityPlayer\.dll|PlayerPrefs)"),
        'confidence': '95%'
    },
    {
        'name': 'Unreal Engine GWorld / GNames Deseni',
        'category': 'Oyun Motoru',
        'regex': re.compile(rb"(?:GWorld|GNames|UObject|FNamePool)"),
        'confidence': '90%'
    },
    {
        'name': 'Godot Engine Runtime İmzası',
        'category': 'Oyun Motoru',
        'regex': re.compile(rb"(?:Godot Engine|GDScript)"),
        'confidence': '95%'
    },
]

# Typical Game Struct & Value Patterns (e.g. 100.0f health, coordinates, resources)
FLOAT_100 = struct.pack("<f", 100.0)    # b'\x00\x00\xc8B'
FLOAT_1000 = struct.pack("<f", 1000.0)  # b'\x00\x00zD'
FLOAT_1 = struct.pack("<f", 1.0)        # b'\x00\x00\x80?'

# Critical Windows APIs for Game Modding / Reversing / Network
CRITICAL_APIS = [
    ("VirtualAlloc / Bellek Tahsisi", re.compile(rb"VirtualAlloc(?:Ex)?"), "Bellek Yönetimi"),
    ("WriteProcessMemory / Bellek Yazma", re.compile(rb"WriteProcessMemory"), "Bellek Yönetimi"),
    ("ReadProcessMemory / Bellek Okuma", re.compile(rb"ReadProcessMemory"), "Bellek Yönetimi"),
    ("CreateRemoteThread / Thread Enjeksiyonu", re.compile(rb"CreateRemoteThread"), "Thread İşlemleri"),
    ("IsDebuggerPresent / Anti-Debug Tespiti", re.compile(rb"(?:IsDebuggerPresent|CheckRemoteDebuggerPresent)"), "Anti-Debug"),
    ("Winsock Soket Bağlantısı", re.compile(rb"(?:WSAStartup|connect|send|recv)"), "Ağ / İletişim"),
]

# URLs & IPs
URL_REGEX = re.compile(rb"https?://[a-zA-Z0-9\.\-/_]{6,}")
IP_REGEX = re.compile(rb"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")


class SmartScanner:
    """
    Scans data sources for game engine artifacts, typical health/resource values,
    cryptographic constants, and critical API / network references.
    """

    def __init__(self, data_source, max_scan_bytes: int = 15 * 1024 * 1024):
        self.data_source = data_source
        self.max_scan = min(data_source.size if data_source else 0, max_scan_bytes)

    def scan(self, callback_progress=None) -> List[Dict[str, Any]]:
        results = []
        if not self.data_source or self.max_scan <= 0:
            return results

        chunk_size = 512 * 1024
        offset = 0

        while offset < self.max_scan:
            read_len = min(chunk_size + 64, self.max_scan - offset)
            chunk = self.data_source.read(offset, read_len)
            if not chunk:
                break

            # 1. Check Crypto Signatures
            for pat in CRYPTO_PATTERNS:
                idx = 0
                target = pat['bytes']
                while True:
                    idx = chunk.find(target, idx)
                    if idx == -1:
                        break
                    actual_off = offset + idx
                    results.append({
                        'offset': actual_off,
                        'offset_hex': f"0x{actual_off:08X}",
                        'name': pat['name'],
                        'category': pat['category'],
                        'confidence': pat['confidence'],
                        'preview': target.hex().upper()[:32],
                        'suggested_label': pat['name'],
                        'length': len(target)
                    })
                    idx += len(target)

            # 2. Check Game Engine Signatures
            for ge in GAME_ENGINE_PATTERNS:
                for match in ge['regex'].finditer(chunk):
                    actual_off = offset + match.start()
                    found_str = match.group().decode('ascii', errors='ignore')
                    results.append({
                        'offset': actual_off,
                        'offset_hex': f"0x{actual_off:08X}",
                        'name': f"{ge['name']}: {found_str}",
                        'category': ge['category'],
                        'confidence': ge['confidence'],
                        'preview': found_str,
                        'suggested_label': f"Motor: {found_str}",
                        'length': len(match.group())
                    })

            # 3. Check Typical Game Health / Value Structs (100.0f float arrays)
            # Find occurrences of 100.0f followed by plausible struct members
            idx = 0
            while True:
                idx = chunk.find(FLOAT_100, idx)
                if idx == -1 or idx + 8 > len(chunk):
                    break
                # Check if next 4 bytes is also 100.0f (MaxHealth == CurrentHealth)
                next_val = chunk[idx+4:idx+8]
                if next_val == FLOAT_100:
                    actual_off = offset + idx
                    results.append({
                        'offset': actual_off,
                        'offset_hex': f"0x{actual_off:08X}",
                        'name': 'Oyun Can Deseni (CurrentHealth: 100.0f | MaxHealth: 100.0f)',
                        'category': 'Oyun Değişkeni / Can',
                        'confidence': '85%',
                        'preview': '100.0f, 100.0f (Sağlık / Can Yapısı)',
                        'suggested_label': 'Can Yapısı (100.0f / 100.0f)',
                        'length': 8
                    })
                idx += 4

            # 4. Check Critical APIs
            for api_name, api_regex, cat in CRITICAL_APIS:
                for match in api_regex.finditer(chunk):
                    actual_off = offset + match.start()
                    s_val = match.group().decode('ascii', errors='ignore')
                    results.append({
                        'offset': actual_off,
                        'offset_hex': f"0x{actual_off:08X}",
                        'name': f"API: {s_val} ({api_name})",
                        'category': cat,
                        'confidence': '90%',
                        'preview': s_val,
                        'suggested_label': f"API_{s_val}",
                        'length': len(match.group())
                    })

            # 5. Check URLs & IPs
            for match in URL_REGEX.finditer(chunk):
                actual_off = offset + match.start()
                url_str = match.group().decode('ascii', errors='ignore')
                results.append({
                    'offset': actual_off,
                    'offset_hex': f"0x{actual_off:08X}",
                    'name': 'Gömülü Ağ Bağlantısı / URL',
                    'category': 'Ağ / İletişim',
                    'confidence': '95%',
                    'preview': url_str[:40],
                    'suggested_label': f"URL: {url_str[:25]}",
                    'length': len(match.group())
                })

            offset += chunk_size
            if callback_progress:
                callback_progress(int((offset / self.max_scan) * 100))

        # Deduplicate results by offset and name
        unique = []
        seen = set()
        for r in results:
            key = (r['offset'], r['name'])
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return sorted(unique, key=lambda x: x['offset'])
