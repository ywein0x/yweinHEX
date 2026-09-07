import unittest
import os
import sys
import struct

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.data_source import FileSource
from src.core.scanner import SmartScanner, CRYPTO_PATTERNS
from src.core.annotations import AnnotationManager, Annotation

class TestScannerAndContext(unittest.TestCase):
    test_bin = os.path.abspath("test_scanner_sample.bin")

    @classmethod
    def setUpClass(cls):
        buf = bytearray(2048)
        # 1. Place AES S-Box at offset 64
        sbox = CRYPTO_PATTERNS[0]['bytes']
        buf[64:64 + len(sbox)] = sbox

        # 2. Place Unity signature at offset 200
        unity_sig = b"GameAssembly.dll - UnityPlayer.dll"
        buf[200:200 + len(unity_sig)] = unity_sig

        # 3. Place Game Health float pattern (100.0f Current, 100.0f Max) at offset 400
        f100 = struct.pack("<f", 100.0)
        buf[400:404] = f100
        buf[404:408] = f100

        # 4. Place a pointer at offset 500 pointing to offset 400
        buf[500:504] = (400).to_bytes(4, 'little')

        # 5. Place VirtualAlloc string at offset 600
        buf[600:612] = b"VirtualAlloc"

        with open(cls.test_bin, "wb") as f:
            f.write(buf)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_bin):
            try:
                os.remove(cls.test_bin)
            except Exception:
                pass

    def test_smart_scanner(self):
        source = FileSource(self.test_bin)
        scanner = SmartScanner(source)
        results = scanner.scan()
        source.close()

        names = [r['name'] for r in results]
        categories = [r['category'] for r in results]

        # Verify crypto found
        self.assertTrue(any("AES" in n for n in names))
        # Verify Unity found
        self.assertTrue(any("Unity" in n for n in names))
        # Verify Game Health found
        self.assertTrue(any("Can" in n or "Health" in n for n in names))
        # Verify API found
        self.assertTrue(any("VirtualAlloc" in n for n in names))

    def test_annotation_manager_and_context_linker(self):
        source = FileSource(self.test_bin)
        mgr = AnnotationManager()

        # Add annotation at pointer offset (500)
        ann_ptr = mgr.add(
            offset=500,
            label="Player Pointer -> Health Struct",
            category="Pointer / Referans",
            length=4
        )

        # Add target annotation at 400
        ann_target = mgr.add(
            offset=400,
            label="Player Health Struct",
            category="Oyun Değişkeni / Can",
            length=8
        )

        # Test pointer link resolution
        target = mgr.resolve_pointer_link(ann_ptr, source, is_64bit=False)
        self.assertEqual(target, 400)
        self.assertEqual(ann_ptr.linked_target, 400)

        # Test JSON export & import
        json_path = os.path.abspath("test_ann.json")
        try:
            mgr.export_json(json_path)
            self.assertTrue(os.path.exists(json_path))

            mgr2 = AnnotationManager()
            count = mgr2.import_json(json_path)
            self.assertEqual(count, 2)
            self.assertEqual(mgr2.get(500).linked_target, 400)
        finally:
            if os.path.exists(json_path):
                os.remove(json_path)

        source.close()

if __name__ == "__main__":
    unittest.main()
