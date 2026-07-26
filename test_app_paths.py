import os
import unittest
from unittest.mock import patch

import app_paths


class TestAppPaths(unittest.TestCase):
    @patch.object(app_paths.sys, "platform", "win32")
    @patch.dict(os.environ, {"LOCALAPPDATA": r"C:\\Users\\Test\\AppData\\Local", "USERPROFILE": r"C:\\Users\\Test"}, clear=True)
    def test_windows_data_and_documents_paths(self):
        self.assertEqual(str(app_paths.user_data_dir()), r"C:\Users\Test\AppData\Local\Expense App Desktop")
        self.assertEqual(str(app_paths.documents_dir()), r"C:\Users\Test\Documents")

    @patch.object(app_paths.sys, "platform", "linux")
    @patch.dict(os.environ, {"XDG_DATA_HOME": "/tmp/data", "XDG_CACHE_HOME": "/tmp/cache"}, clear=True)
    def test_linux_xdg_paths(self):
        self.assertEqual(app_paths.user_data_dir(), app_paths.Path("/tmp/data") / "expense-app-desktop")
        self.assertEqual(app_paths.user_cache_dir(), app_paths.Path("/tmp/cache") / "expense-app-desktop")
