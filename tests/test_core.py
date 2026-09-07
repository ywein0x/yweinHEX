import unittest
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.data_source import FileSource, get_running_processes
from src.core.pe_analyzer import detect_file_format, PEAnalyzer
from src.core.entropy import calculate_entropy, calculate_entropy_blocks
from src.core.string_extractor import extract_strings

class TestCoreModules(unittest.TestCase):
    test_bin_path = os.path.abspath("test_sample_pe.bin")

    @classmethod
    def setUpClass(cls):
        # Create a mock binary file with MZ header and strings using exact offsets
        buf = bytearray(512)
        # DOS Magic 'MZ'
        buf[0:2] = b"MZ"
        # e_lfanew at 0x3C points to 0x80 (128)
        buf[0x3C:0x40] = (128).to_bytes(4, 'little')
        # DOS stub message
        dos_msg = b"This program cannot be run in DOS mode."
        buf[0x40:0x40 + len(dos_msg)] = dos_msg

        # PE Signature at 0x80
        pe_offset = 128
        buf[pe_offset:pe_offset + 4] = b"PE\x00\x00"

        # COFF File Header (20 bytes) at 132
        coff_offset = pe_offset + 4
        # Machine: AMD64 (0x8664), Sections: 1, TimeDateStamp: 0, SizeOfOptHdr: 112, Characteristics: 0x0022
        buf[coff_offset:coff_offset + 2] = (0x8664).to_bytes(2, 'little') # Machine
        buf[coff_offset + 2:coff_offset + 4] = (1).to_bytes(2, 'little')   # Sections
        buf[coff_offset + 4:coff_offset + 8] = (1700000000).to_bytes(4, 'little') # TimeDateStamp
        buf[coff_offset + 16:coff_offset + 18] = (112).to_bytes(2, 'little') # SizeOfOptionalHeader
        buf[coff_offset + 18:coff_offset + 20] = (0x0022).to_bytes(2, 'little') # Characteristics

        # Optional Header (112 bytes) at 152
        opt_offset = coff_offset + 20
        buf[opt_offset:opt_offset + 2] = (0x20B).to_bytes(2, 'little') # PE32+ (64-bit)
        buf[opt_offset + 16:opt_offset + 20] = (0x1000).to_bytes(4, 'little') # EntryPoint
        buf[opt_offset + 24:opt_offset + 32] = (0x00400000).to_bytes(8, 'little') # ImageBase

        # Section Header (40 bytes) at 152 + 112 = 264
        sec_offset = opt_offset + 112
        buf[sec_offset:sec_offset + 5] = b".text"
        buf[sec_offset + 8:sec_offset + 12] = (0x1000).to_bytes(4, 'little') # VirtualSize
        buf[sec_offset + 12:sec_offset + 16] = (0x1000).to_bytes(4, 'little') # VirtualAddress
        buf[sec_offset + 16:sec_offset + 20] = (0x200).to_bytes(4, 'little') # SizeOfRawData
        buf[sec_offset + 20:sec_offset + 24] = (320).to_bytes(4, 'little') # PointerToRawData
        buf[sec_offset + 36:sec_offset + 40] = (0x60000020).to_bytes(4, 'little') # Characteristics

        # Some test text in raw section (at 320)
        test_txt = b"Hello yweinHEX world! Testing string extraction."
        buf[320:320 + len(test_txt)] = test_txt
        u_txt = "Unicode Test".encode('utf-16le')
        buf[400:400 + len(u_txt)] = u_txt

        with open(cls.test_bin_path, "wb") as f:
            f.write(buf)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_bin_path):
            try:
                os.remove(cls.test_bin_path)
            except Exception:
                pass

    def test_file_source(self):
        source = FileSource(self.test_bin_path)
        self.assertGreater(source.size, 0)
        data = source.read(0, 2)
        self.assertEqual(data, b"MZ")
        source.close()

    def test_magic_detection(self):
        source = FileSource(self.test_bin_path)
        prefix = source.read(0, 256)
        fmt = detect_file_format(prefix)
        self.assertIn("PE Executable", fmt)
        source.close()

    def test_pe_analyzer(self):
        source = FileSource(self.test_bin_path)
        pe = PEAnalyzer(source)
        source.close()
        self.assertTrue(pe.is_pe)
        self.assertEqual(pe.info.get('Machine'), "AMD64 / x86-64 (64-bit)")
        self.assertEqual(pe.info.get('Architecture'), "PE32+ (64-bit)")
        self.assertGreaterEqual(len(pe.sections), 1)
        self.assertEqual(pe.sections[0]['name'], ".text")

    def test_entropy(self):
        # All zeros has 0.0 entropy
        self.assertEqual(calculate_entropy(b"\x00" * 100), 0.0)
        # Random/diverse bytes has high entropy
        diverse = bytes(range(256))
        self.assertAlmostEqual(calculate_entropy(diverse), 8.0, places=2)

    def test_string_extractor(self):
        source = FileSource(self.test_bin_path)
        strings = extract_strings(source, min_len=4)
        source.close()
        
        values = [s['value'] for s in strings]
        self.assertTrue(any("DOS mode" in v for v in values))
        self.assertTrue(any("yweinHEX" in v for v in values))
        self.assertTrue(any("Unicode Test" in v for v in values))

    def test_process_enumeration(self):
        procs = get_running_processes()
        self.assertIsInstance(procs, list)
        self.assertGreater(len(procs), 0)
        self.assertTrue(any("python" in p['name'].lower() or p['pid'] > 0 for p in procs))

if __name__ == "__main__":
    unittest.main()
