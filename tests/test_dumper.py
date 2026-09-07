import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.data_source import FileSource
from src.core.dumper import OffsetDumper
from src.core.pe_analyzer import PEAnalyzer
from src.ui.pe_dialog import PEDialog
from PySide6.QtWidgets import QApplication

class TestOffsetDumper(unittest.TestCase):
    test_bin = os.path.abspath("test_dumper_sample.bin")

    @classmethod
    def setUpClass(cls):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        cls.app = QApplication.instance() or QApplication(sys.argv)

        buf = bytearray(4096)
        # Add basic MZ and DOS header
        buf[0:2] = b"MZ"
        buf[0x3C:0x40] = (128).to_bytes(4, 'little')
        buf[128:132] = b"PE\x00\x00"

        # Mock dwLocalPlayer pattern: \x8B\x0D(....)\x85\xC9\x74
        buf[500:502] = b"\x8B\x0D"
        buf[502:506] = (0x002A1234).to_bytes(4, 'little')
        buf[506:509] = b"\x85\xC9\x74"

        with open(cls.test_bin, "wb") as f:
            f.write(buf)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_bin):
            try:
                os.remove(cls.test_bin)
            except Exception:
                pass

    def test_dumper_dump(self):
        source = FileSource(self.test_bin)
        dumper = OffsetDumper(source)
        offsets = dumper.dump()
        source.close()

        self.assertGreater(len(offsets), 0)
        names = [o.name for o in offsets]
        self.assertTrue(any("base_" in n for n in names))
        self.assertTrue(any("m_iHealth" in n for n in names))
        self.assertTrue(any("dwLocalPlayer" in n for n in names))

    def test_dumper_exports(self):
        source = FileSource(self.test_bin)
        dumper = OffsetDumper(source)
        dumper.dump()
        source.close()

        cpp = dumper.generate_cpp_header()
        self.assertIn("namespace Offsets", cpp)
        self.assertIn("constexpr uintptr_t", cpp)

        cs = dumper.generate_csharp_class()
        self.assertIn("public static class Offsets", cs)

        py = dumper.generate_python_class()
        self.assertIn("class Offsets:", py)

    def test_pe_dialog_no_regression(self):
        source = FileSource(self.test_bin)
        pe = PEAnalyzer(source)
        source.close()
        
        # Test creating PEDialog without any AttributeError
        dlg = PEDialog(pe)
        self.assertIsNotNone(dlg)
        dlg.close()

if __name__ == "__main__":
    unittest.main()
