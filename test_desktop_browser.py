import unittest
from pathlib import Path

import desktop_app


class TestDesktopBrowser(unittest.TestCase):
    def test_native_desktop_app_does_not_import_browser_launcher_modules(self):
        source = Path(desktop_app.__file__).read_text(encoding="utf-8")
        self.assertNotIn("webbrowser", source)
        self.assertNotIn("streamlit", source.lower())
