import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.elevation import is_admin, enable_debug_privilege

class TestElevation(unittest.TestCase):
    def test_is_admin_returns_bool(self):
        result = is_admin()
        self.assertIsInstance(result, bool)

    def test_enable_debug_privilege(self):
        # Should return bool without throwing exceptions
        result = enable_debug_privilege()
        self.assertIsInstance(result, bool)

if __name__ == "__main__":
    unittest.main()
