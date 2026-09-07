import struct
import datetime
from typing import Dict, Any, List, Optional
from .entropy import calculate_entropy

# Known magic byte signatures
MAGIC_SIGNATURES = [
    (b"MZ", "Windows PE Executable / DLL (MZ)"),
    (b"\x7fELF", "Linux ELF Executable / Object"),
    (b"\xca\xfe\xba\xbe", "Java Class File / Mach-O Fat Binary"),
    (b"\xfe\xed\xfa\xce", "Mach-O 32-bit (Big Endian)"),
    (b"\xce\xfa\xed\xfe", "Mach-O 32-bit (Little Endian)"),
    (b"\xfe\xed\xfa\xcf", "Mach-O 64-bit (Big Endian)"),
    (b"\xcf\xfa\xed\xfe", "Mach-O 64-bit (Little Endian)"),
    (b"PK\x03\x04", "ZIP Archive / DOCX / APK / JAR"),
    (b"\x89PNG\r\n\x1a\n", "PNG Image File"),
    (b"\xff\xd8\xff", "JPEG Image File"),
    (b"GIF87a", "GIF Image File (v87a)"),
    (b"GIF89a", "GIF Image File (v89a)"),
    (b"%PDF-", "Adobe PDF Document"),
    (b"SQLite format 3\x00", "SQLite 3 Database File"),
    (b"7z\xbc\xaf'\x1c", "7-Zip Compressed Archive"),
    (b"Rar!\x1a\x07\x00", "RAR Archive v4.x"),
    (b"Rar!\x1a\x07\x01\x00", "RAR Archive v5.x"),
    (b"\x1f\x8b", "GZIP Compressed File"),
    (b"BM", "BMP Bitmap Image"),
    (b"OggS", "OGG Media Stream"),
    (b"RIFF", "Resource Interchange File (WAV / AVI / WEBP)"),
    (b"fLaC", "FLAC Audio Stream"),
    (b"\x42\x5a\x68", "BZip2 Archive"),
    (b"\xfd7zXZ\x00", "XZ Archive"),
    (b"\x00\x00\x01\x00", "Windows Icon File (.ico)"),
]

def detect_file_format(data_prefix: bytes) -> str:
    """Identify the file format based on magic byte signatures."""
    if not data_prefix:
        return "Empty File / Unknown"
    
    for sig, desc in MAGIC_SIGNATURES:
        if data_prefix.startswith(sig):
            return desc
            
    # Check for text / ASCII
    try:
        sample = data_prefix[:256].decode('utf-8')
        if all(c.isprintable() or c in '\r\n\t' for c in sample):
            return "Plain Text / UTF-8 Script or Configuration"
    except Exception:
        pass

    return "Raw Binary / Unknown Format"


MACHINE_TYPES = {
    0x014C: "Intel 386 (x86 32-bit)",
    0x8664: "AMD64 / x86-64 (64-bit)",
    0x01C0: "ARM Little Endian",
    0xAA64: "ARM64 Little Endian",
    0x0200: "Intel Itanium (IA-64)",
}

SUBSYSTEMS = {
    1: "Native / Device Driver",
    2: "Windows GUI",
    3: "Windows CUI (Console Application)",
    7: "POSIX CUI",
    9: "Windows CE GUI",
    10: "EFI Application",
    11: "EFI Boot Service Driver",
    12: "EFI Runtime Driver",
    14: "XBOX",
}

class PEAnalyzer:
    """Self-contained PE/COFF parser for EXE/DLL binaries without external heavy dependencies."""

    def __init__(self, data_reader):
        """data_reader: callable or object with read(offset, length) -> bytes"""
        self.reader = data_reader
        self.is_pe = False
        self.info: Dict[str, Any] = {}
        self.sections: List[Dict[str, Any]] = []
        self._parse()

    def _read(self, offset: int, length: int) -> bytes:
        if hasattr(self.reader, 'read'):
            return self.reader.read(offset, length)
        return b""

    def _parse(self):
        # 1. DOS Header
        dos_hdr = self._read(0, 64)
        if len(dos_hdr) < 64 or dos_hdr[:2] != b"MZ":
            return
        
        # e_lfanew is at offset 0x3C (uint32)
        e_lfanew = struct.unpack_from("<I", dos_hdr, 0x3C)[0]
        self.info['e_lfanew'] = e_lfanew
        
        # 2. PE Signature
        pe_sig = self._read(e_lfanew, 4)
        if pe_sig != b"PE\x00\x00":
            return
        
        self.is_pe = True
        coff_offset = e_lfanew + 4
        
        # 3. COFF File Header (20 bytes)
        coff_hdr = self._read(coff_offset, 20)
        if len(coff_hdr) < 20:
            return
            
        machine, num_sections, timedatestamp, _, _, size_opt_hdr, characteristics = struct.unpack(
            "<HHIIIHH", coff_hdr
        )
        
        try:
            timestamp_dt = datetime.datetime.fromtimestamp(timedatestamp, datetime.timezone.utc)
            timestamp_str = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except Exception:
            timestamp_str = f"Raw: {timedatestamp}"

        self.info['Machine'] = MACHINE_TYPES.get(machine, f"Unknown (0x{machine:04X})")
        self.info['NumberOfSections'] = num_sections
        self.info['TimeDateStamp'] = timestamp_str
        self.info['Characteristics'] = f"0x{characteristics:04X}"
        self.info['IsDLL'] = bool(characteristics & 0x2000)
        self.info['IsExecutable'] = bool(characteristics & 0x0002)
        
        # 4. Optional Header
        opt_offset = coff_offset + 20
        if size_opt_hdr >= 2:
            magic_bytes = self._read(opt_offset, 2)
            opt_magic = struct.unpack("<H", magic_bytes)[0]
            is_64 = (opt_magic == 0x20B)
            self.info['Architecture'] = "PE32+ (64-bit)" if is_64 else ("PE32 (32-bit)" if opt_magic == 0x10B else f"Unknown (0x{opt_magic:04X})")
            
            # Read entry point and image base
            if is_64 and size_opt_hdr >= 112:
                opt_data = self._read(opt_offset, 112)
                entry_point = struct.unpack_from("<I", opt_data, 16)[0]
                image_base = struct.unpack_from("<Q", opt_data, 24)[0]
                sec_align = struct.unpack_from("<I", opt_data, 32)[0]
                file_align = struct.unpack_from("<I", opt_data, 36)[0]
                size_image = struct.unpack_from("<I", opt_data, 56)[0]
                size_headers = struct.unpack_from("<I", opt_data, 60)[0]
                subsystem = struct.unpack_from("<H", opt_data, 68)[0]
                dll_char = struct.unpack_from("<H", opt_data, 70)[0]
            elif not is_64 and size_opt_hdr >= 96:
                opt_data = self._read(opt_offset, 96)
                entry_point = struct.unpack_from("<I", opt_data, 16)[0]
                image_base = struct.unpack_from("<I", opt_data, 28)[0]
                sec_align = struct.unpack_from("<I", opt_data, 32)[0]
                file_align = struct.unpack_from("<I", opt_data, 36)[0]
                size_image = struct.unpack_from("<I", opt_data, 56)[0]
                size_headers = struct.unpack_from("<I", opt_data, 60)[0]
                subsystem = struct.unpack_from("<H", opt_data, 68)[0]
                dll_char = struct.unpack_from("<H", opt_data, 70)[0]
            else:
                entry_point = image_base = sec_align = file_align = size_image = size_headers = subsystem = dll_char = 0

            self.info['AddressOfEntryPoint'] = f"0x{entry_point:08X}"
            self.info['ImageBase'] = f"0x{image_base:016X}" if is_64 else f"0x{image_base:08X}"
            self.info['SizeOfImage'] = f"{size_image:,} bytes"
            self.info['SizeOfHeaders'] = f"{size_headers:,} bytes"
            self.info['Subsystem'] = SUBSYSTEMS.get(subsystem, f"Other (0x{subsystem:04X})")
            self.info['ASLR_Enabled'] = bool(dll_char & 0x0040)
            self.info['DEP_NX_Enabled'] = bool(dll_char & 0x0100)

        # 5. Section Headers (each 40 bytes)
        sec_table_offset = opt_offset + size_opt_hdr
        for i in range(num_sections):
            sec_hdr = self._read(sec_table_offset + i * 40, 40)
            if len(sec_hdr) < 40:
                break
            
            raw_name = sec_hdr[:8].rstrip(b"\x00")
            try:
                sec_name = raw_name.decode('utf-8', errors='replace')
            except Exception:
                sec_name = repr(raw_name)
                
            virt_size, virt_addr, raw_size, raw_ptr, _, _, _, _, characteristics = struct.unpack(
                "<IIIIIIHHI", sec_hdr[8:40]
            )
            
            # Read section sample for entropy
            sec_raw_data = self._read(raw_ptr, min(raw_size, 65536)) if raw_size > 0 else b""
            ent = calculate_entropy(sec_raw_data) if sec_raw_data else 0.0
            
            flags = []
            if characteristics & 0x20000000:
                flags.append("EXEC")
            if characteristics & 0x40000000:
                flags.append("READ")
            if characteristics & 0x80000000:
                flags.append("WRITE")
            if characteristics & 0x00000020:
                flags.append("CODE")

            self.sections.append({
                'name': sec_name,
                'virtual_address': f"0x{virt_addr:08X}",
                'virtual_size': f"{virt_size:,} B",
                'raw_offset': f"0x{raw_ptr:08X}",
                'raw_size': f"{raw_size:,} B",
                'entropy': f"{ent:.2f}",
                'flags': " | ".join(flags) if flags else "NONE"
            })
