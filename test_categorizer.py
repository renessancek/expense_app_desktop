import json
import os
import shutil
import tempfile
import unittest

from categorizer import Categorizer


class TestCategorizer(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.rules_path = os.path.join(self.test_dir, "rules.json")
        self.categorizer = Categorizer(rules_path=self.rules_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_unknown_description_uses_fallback(self):
        self.assertEqual(self.categorizer.suggest_category("unknown vendor xyz"), "Sonstiges")

    def test_rule_matches_case_insensitively(self):
        self.categorizer.add_rule(["REWE"], "Supermarkt")
        self.assertEqual(self.categorizer.suggest_category("rewe sagt danke"), "Supermarkt")

    def test_rule_uses_word_boundaries(self):
        self.categorizer.add_rule(["net"], "Internet")
        self.assertEqual(self.categorizer.suggest_category("NETTO DISCOUNT"), "Sonstiges")
        self.assertEqual(self.categorizer.suggest_category("pay via net transfer"), "Internet")

    def test_update_and_delete_rule_take_effect_immediately(self):
        self.categorizer.add_rule(["rewe"], "Supermarkt")
        self.assertTrue(self.categorizer.update_rule_keywords("Supermarkt", ["aldi"]))
        self.assertEqual(self.categorizer.suggest_category("REWE"), "Sonstiges")
        self.assertEqual(self.categorizer.suggest_category("ALDI SUED"), "Supermarkt")
        self.categorizer.delete_rule("Supermarkt")
        self.assertEqual(self.categorizer.suggest_category("ALDI SUED"), "Sonstiges")

    def test_rename_category_updates_rule(self):
        self.categorizer.add_rule(["rewe"], "Supermarkt")
        self.assertTrue(self.categorizer.rename_category("Supermarkt", "Groceries"))
        self.assertEqual(self.categorizer.suggest_category("REWE"), "Groceries")

    def test_import_uses_rules_and_discards_legacy_mappings(self):
        self.categorizer.import_rules({
            "mappings": {"amazon": "Shopping"},
            "rules": [{"category": "Groceries", "keywords": ["rewe"]}],
        })
        self.assertEqual(self.categorizer.suggest_category("REWE"), "Groceries")
        self.assertEqual(self.categorizer.suggest_category("AMAZON PRIME"), "Sonstiges")
        with open(self.rules_path, encoding="utf-8") as rules_file:
            self.assertEqual(json.load(rules_file), {"rules": [{"category": "Groceries", "keywords": ["rewe"]}]})


if __name__ == "__main__":
    unittest.main()
