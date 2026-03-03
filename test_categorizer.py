import unittest
import os
import tempfile
import shutil
from categorizer import Categorizer

class TestCategorizer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.rules_path = os.path.join(self.test_dir, "rules.json")
        self.categorizer = Categorizer(rules_path=self.rules_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_extract_keyword(self):
        test_cases = [
            ("REWE SAGT DANKE", "rewe sagt", "normal description"),
            ("AMAZON", "amazon", "single word"),
            ("", "", "empty string"),
            ("  APPLE   STORE  ", "apple store", "extra spaces"),
            ("NETTO MARKEN-DISCOUNT NUERNBERG", "netto marken-discount", "more than two words"),
        ]

        for description, expected, msg in test_cases:
            with self.subTest(msg=msg, description=description):
                self.assertEqual(self.categorizer.extract_keyword(description), expected)

if __name__ == "__main__":
    unittest.main()
