import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scanner import Scanner


class TestScanner(unittest.TestCase):
    def test_scan_finds_csv_extensions_case_insensitively(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            lower = folder / "bank.csv"
            upper = folder / "paypal.CSV"
            mixed = folder / "statement.Csv"
            ignored = folder / "notes.txt"
            lower.write_text("a", encoding="utf-8")
            upper.write_text("b", encoding="utf-8")
            mixed.write_text("c", encoding="utf-8")
            ignored.write_text("d", encoding="utf-8")

            found = Scanner(watch_path=str(folder)).scan_for_csvs()

            self.assertEqual(set(found), {str(lower), str(mixed), str(upper)})
            self.assertEqual(found, sorted(found))

    def test_scan_returns_empty_list_for_empty_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            found = Scanner(watch_path=tmp).scan_for_csvs()
            self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
