import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import desktop_app
import desktop_launcher


class TestDesktopLauncher(unittest.TestCase):
    def test_launcher_uses_native_application_entry_point(self):
        self.assertIs(desktop_launcher.main, desktop_app.main)
