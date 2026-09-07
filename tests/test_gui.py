import unittest
import os
import sys

# Set offscreen platform for headless test
os.environ["QT_QPA_PLATFORM"] = "offscreen"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.ui.styles import DARK_THEME
from src.core.data_source import FileSource

class TestGUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)
        cls.app.setStyleSheet(DARK_THEME)

        # Create small test file
        cls.test_path = os.path.abspath("test_gui_dummy.bin")
        with open(cls.test_path, "wb") as f:
            f.write(b"yweinHEX GUI Test Data " * 20)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_path):
            try:
                os.remove(cls.test_path)
            except Exception:
                pass

    def test_window_creation_and_load(self):
        window = MainWindow()
        self.assertIsNotNone(window)
        self.assertIn("yweinHEX", window.windowTitle())

        # Load file
        window.open_file_path(self.test_path)
        self.assertIsNotNone(window.data_source)
        self.assertGreater(window.data_source.size, 0)

        # Test cursor navigation
        window.hex_widget.jump_to_offset(10)
        self.assertEqual(window.hex_widget.cursor_offset, 10)

        # Test selection
        window.hex_widget.select_all()
        self.assertEqual(window.hex_widget.selection_start, 0)

        # Test copying
        hex_data = window.hex_widget.get_selected_bytes()
        self.assertGreater(len(hex_data), 0)

        window.close()

if __name__ == "__main__":
    unittest.main()
