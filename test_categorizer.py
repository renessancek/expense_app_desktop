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

    def test_suggest_category_via_rules(self):
        self.categorizer.add_rule(["rewe", "netto"], "Supermarkt")
        self.assertEqual(self.categorizer.suggest_category("REWE Sagt Danke"), "Supermarkt")
        self.assertEqual(self.categorizer.suggest_category("NETTO Marken"), "Supermarkt")

    def test_suggest_category_via_mappings(self):
        self.categorizer.add_mapping("amazon", "Amazon")
        self.assertEqual(self.categorizer.suggest_category("AMAZON MARKETPLACE"), "Amazon")

    def test_suggest_category_cache_refreshed_after_save_rules(self):
        # Before adding rule, description should not match
        self.assertEqual(self.categorizer.suggest_category("STEAM PURCHASE"), "Sonstiges")
        # Add a rule and save (which triggers cache refresh)
        self.categorizer.add_rule(["steam"], "Computerspiele")
        # After save, the new rule should be matched
        self.assertEqual(self.categorizer.suggest_category("STEAM PURCHASE"), "Computerspiele")

    def test_suggest_category_cache_refreshed_after_save_mappings(self):
        # Before adding mapping, description should not match
        self.assertEqual(self.categorizer.suggest_category("PAYPAL PAYMENT"), "Sonstiges")
        # Add a mapping and save (which triggers cache refresh)
        self.categorizer.add_mapping("paypal", "Transfer")
        # After save, the new mapping should be matched
        self.assertEqual(self.categorizer.suggest_category("PAYPAL PAYMENT"), "Transfer")

if __name__ == "__main__":
    unittest.main()
