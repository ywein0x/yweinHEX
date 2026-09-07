import os
import re
import struct
from typing import List, Dict, Any, Optional
from src.core.data_source import DataSource, ProcessSource, get_process_modules

# Known Game & Engine Signature Patterns (AOB with byte patterns or regex)
COMMON_GAME_SIGNATURES = [
    {
        'name': 'dwLocalPlayer (Yerel Oyuncu Tabanı)',
        'category': 'Oyuncu / Entity',
        'regex': re.compile(rb"\x8B\x0D(....)\x85\xC9\x74", re.DOTALL),
        'sub_offset_calc': lambda m: struct.unpack("<I", m.group(1))[0]
    },
    {
        'name': 'dwEntityList (Varlık Listesi)',
        'category': 'Oyuncu / Entity',
        'regex': re.compile(rb"\x8B\x04\x8D(....)\x85\xC0", re.DOTALL),
        'sub_offset_calc': lambda m: struct.unpack("<I", m.group(1))[0]
    },
    {
        'name': 'dwViewMatrix (Kamera Matrisi)',
        'category': 'Kamera / Render',
        'regex': re.compile(rb"\x0F\x10\x05(....)\x0F\x11", re.DOTALL),
        'sub_offset_calc': lambda m: struct.unpack("<I", m.group(1))[0]
    },
    {
        'name': 'GWorld (Unreal Engine Dünya Nesnesi)',
        'category': 'Oyun Motoru',
        'regex': re.compile(rb"\x48\x8B\x1D(....)\x48\x85\xDB\x74", re.DOTALL),
        'sub_offset_calc': lambda m: struct.unpack("<i", m.group(1))[0]
    },
    {
        'name': 'GNames (Unreal Engine İsim Havuzu)',
        'category': 'Oyun Motoru',
        'regex': re.compile(rb"\x48\x8B\x05(....)\x48\x85\xC0\x75", re.DOTALL),
        'sub_offset_calc': lambda m: struct.unpack("<i", m.group(1))[0]
    },
    {
        'name': 'IL2CPP_Metadata (Unity Metadata Tabanı)',
        'category': 'Oyun Motoru',
        'regex': re.compile(rb"global-metadata\.dat", re.IGNORECASE),
        'sub_offset_calc': None
    }
]

# Standard Struct Member Offsets (Common across FPS/RPG engines)
STANDARD_MEMBER_OFFSETS = [
    {'name': 'm_iHealth (Can / Sağlık Değeri)', 'offset': 0x100, 'category': 'Can / Durum'},
    {'name': 'm_iMaxHealth (Maksimum Can)', 'offset': 0x104, 'category': 'Can / Durum'},
    {'name': 'm_iArmor (Zırh / Kalkan)', 'offset': 0x108, 'category': 'Can / Durum'},
    {'name': 'm_vecOrigin (Oyuncu X, Y, Z Pozisyonu)', 'offset': 0x138, 'category': 'Pozisyon / Koordinat'},
    {'name': 'm_vecVelocity (Hız Vektörü)', 'offset': 0x144, 'category': 'Fizik / Hareket'},
    {'name': 'm_iTeamNum (Takım Numarası)', 'offset': 0xF4, 'category': 'Oyuncu / Entity'},
    {'name': 'm_fFlags (Yerde/Havada Bayrağı)', 'offset': 0x104, 'category': 'Fizik / Hareket'},
    {'name': 'm_bIsAlive (Hayatta Mı?)', 'offset': 0x88, 'category': 'Can / Durum'},
]


class DumpedOffset:
    def __init__(self, name: str, module_name: str, rva: int, absolute_addr: int, 
                 category: str = "General", desc: str = ""):
        self.name = name
        self.module_name = module_name
        self.rva = rva
        self.absolute_addr = absolute_addr
        self.category = category
        self.desc = desc

    @property
    def rva_hex(self) -> str:
        return f"0x{self.rva:X}"

    @property
    def abs_hex(self) -> str:
        return f"0x{self.absolute_addr:016X}" if self.absolute_addr > 0xFFFFFFFF else f"0x{self.absolute_addr:08X}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'module': self.module_name,
            'rva': self.rva,
            'rva_hex': self.rva_hex,
            'absolute_address': self.absolute_addr,
            'abs_hex': self.abs_hex,
            'category': self.category,
            'description': self.desc
        }


class OffsetDumper:
    """
    Scans process memory or binary file to dump game offsets,
    module base addresses, and struct offsets.
    """

    def __init__(self, data_source: DataSource):
        self.data_source = data_source
        self.dumped_offsets: List[DumpedOffset] = []

    def dump(self, callback_progress=None) -> List[DumpedOffset]:
        self.dumped_offsets.clear()
        if not self.data_source:
            return []

        base = self.data_source.base_address
        total_size = self.data_source.size
        main_mod_name = getattr(self.data_source, 'name', 'MainModule')

        # 1. Dump Module Base Addresses
        if isinstance(self.data_source, ProcessSource):
            modules = get_process_modules(self.data_source.pid)
            for m in modules:
                m_addr = m['base_address']
                self.dumped_offsets.append(DumpedOffset(
                    name=f"base_{m['name'].replace('.', '_')}",
                    module_name=m['name'],
                    rva=0,
                    absolute_addr=m_addr,
                    category="Modül Tabanı",
                    desc=f"Boyut: {m['size_str']} | Giriş: {m['entry_hex']}"
                ))
        else:
            self.dumped_offsets.append(DumpedOffset(
                name="base_ImageBase",
                module_name=main_mod_name,
                rva=0,
                absolute_addr=base,
                category="Modül Tabanı",
                desc=f"Dosya Boyutu: {total_size:,} bayt"
            ))

        # 2. Add Standard Struct Member Offsets
        for std in STANDARD_MEMBER_OFFSETS:
            self.dumped_offsets.append(DumpedOffset(
                name=std['name'].split()[0],
                module_name="LocalPlayer",
                rva=std['offset'],
                absolute_addr=base + std['offset'],
                category=std['category'],
                desc=std['name']
            ))

        # 3. Signature & Pattern Scanning (Scan up to 10MB of data)
        max_scan = min(total_size, 10 * 1024 * 1024)
        chunk_size = 512 * 1024
        offset = 0

        while offset < max_scan:
            read_len = min(chunk_size + 64, max_scan - offset)
            chunk = self.data_source.read(offset, read_len)
            if not chunk:
                break

            for sig in COMMON_GAME_SIGNATURES:
                regex = sig['regex']
                for match in regex.finditer(chunk):
                    match_off = offset + match.start()
                    calc_fn = sig['sub_offset_calc']
                    if calc_fn:
                        try:
                            extracted_val = calc_fn(match)
                            # If extracted value is an offset or relative RIP displacement
                            rva = extracted_val & 0xFFFFFFFF
                        except Exception:
                            rva = match_off
                    else:
                        rva = match_off

                    self.dumped_offsets.append(DumpedOffset(
                        name=sig['name'].split()[0],
                        module_name=main_mod_name,
                        rva=rva,
                        absolute_addr=base + rva,
                        category=sig['category'],
                        desc=sig['name']
                    ))

            offset += chunk_size
            if callback_progress:
                callback_progress(int((offset / max_scan) * 100))

        # Deduplicate results by name
        unique = []
        seen = set()
        for item in self.dumped_offsets:
            key = (item.name, item.rva)
            if key not in seen:
                seen.add(key)
                unique.append(item)

        self.dumped_offsets = unique
        return self.dumped_offsets

    def generate_cpp_header(self) -> str:
        lines = [
            "// =============================================",
            "//  yweinHEX - Game Offset Dump",
            f"//  Target: {self.data_source.name if self.data_source else 'Unknown'}",
            "//  Generated by yweinHEX Next-Gen Inspector",
            "// =============================================",
            "#pragma once",
            "#include <cstdint>",
            "",
            "namespace Offsets {"
        ]
        for off in self.dumped_offsets:
            lines.append(f"    constexpr uintptr_t {off.name} = {off.rva_hex}; // {off.desc or off.category}")
        lines.append("}")
        return "\n".join(lines)

    def generate_csharp_class(self) -> str:
        lines = [
            "// =============================================",
            "//  yweinHEX - Game Offset Dump (C#)",
            f"//  Target: {self.data_source.name if self.data_source else 'Unknown'}",
            "// =============================================",
            "using System;",
            "",
            "public static class Offsets",
            "{"
        ]
        for off in self.dumped_offsets:
            lines.append(f"    public const int {off.name} = {off.rva_hex}; // {off.desc or off.category}")
        lines.append("}")
        return "\n".join(lines)

    def generate_python_class(self) -> str:
        lines = [
            "# =============================================",
            "#  yweinHEX - Game Offset Dump (Python)",
            f"#  Target: {self.data_source.name if self.data_source else 'Unknown'}",
            "# =============================================",
            "",
            "class Offsets:"
        ]
        for off in self.dumped_offsets:
            lines.append(f"    {off.name} = {off.rva_hex}  # {off.desc or off.category}")
        return "\n".join(lines)
