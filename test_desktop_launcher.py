import unittest

import desktop_app
import desktop_launcher


class TestDesktopLauncher(unittest.TestCase):
    def test_launcher_uses_native_application_entry_point(self):
        self.assertIs(desktop_launcher.main, desktop_app.main)
