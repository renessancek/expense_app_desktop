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

    # --- suggest_category tests ---

    def test_suggest_category_default(self):
        """Returns 'Sonstiges' when no rules or mappings match."""
        self.assertEqual(self.categorizer.suggest_category("unknown vendor xyz"), "Sonstiges")

    def test_suggest_category_matches_rule(self):
        """Matches a rule keyword and returns its category."""
        self.categorizer.add_rule(["rewe"], "Supermarkt")
        self.assertEqual(self.categorizer.suggest_category("REWE SAGT DANKE"), "Supermarkt")

    def test_suggest_category_matches_mapping(self):
        """Matches a learned mapping and returns its category."""
        self.categorizer.add_mapping("amazon", "Shopping")
        self.assertEqual(self.categorizer.suggest_category("AMAZON PRIME"), "Shopping")

    def test_suggest_category_rules_take_precedence_over_mappings(self):
        """Rules have higher priority than mappings for the same keyword."""
        self.categorizer.add_mapping("rewe", "Shopping")
        self.categorizer.add_rule(["rewe"], "Supermarkt")
        self.assertEqual(self.categorizer.suggest_category("REWE SAGT DANKE"), "Supermarkt")

    def test_suggest_category_word_boundary(self):
        """Word-boundary matching prevents partial-word false positives."""
        self.categorizer.add_rule(["net"], "NetCategory")
        # 'net' should not match 'netto' due to word boundary
        self.assertEqual(self.categorizer.suggest_category("NETTO DISCOUNT"), "Sonstiges")
        # but should match standalone 'net'
        self.assertEqual(self.categorizer.suggest_category("pay via net transfer"), "NetCategory")

    def test_suggest_category_case_insensitive(self):
        """Matching is case-insensitive."""
        self.categorizer.add_rule(["REWE"], "Supermarkt")
        self.assertEqual(self.categorizer.suggest_category("rewe sagt danke"), "Supermarkt")

    # --- mutation operation tests ---

    def test_add_mapping_takes_effect_immediately(self):
        """suggest_category reflects a new mapping right after add_mapping."""
        self.assertEqual(self.categorizer.suggest_category("AMAZON PRIME"), "Sonstiges")
        self.categorizer.add_mapping("amazon", "Shopping")
        self.assertEqual(self.categorizer.suggest_category("AMAZON PRIME"), "Shopping")

    def test_delete_mapping_takes_effect_immediately(self):
        """suggest_category no longer matches after delete_mapping."""
        self.categorizer.add_mapping("amazon", "Shopping")
        self.categorizer.delete_mapping("amazon")
        self.assertEqual(self.categorizer.suggest_category("AMAZON PRIME"), "Sonstiges")

    def test_delete_mapping_case_insensitive(self):
        """delete_mapping works regardless of the case passed by the caller."""
        self.categorizer.add_mapping("amazon", "Shopping")
        self.categorizer.delete_mapping("AMAZON")
        self.assertEqual(self.categorizer.suggest_category("AMAZON PRIME"), "Sonstiges")

    def test_add_rule_takes_effect_immediately(self):
        """suggest_category reflects a new rule right after add_rule."""
        self.assertEqual(self.categorizer.suggest_category("REWE SAGT DANKE"), "Sonstiges")
        self.categorizer.add_rule(["rewe"], "Supermarkt")
        self.assertEqual(self.categorizer.suggest_category("REWE SAGT DANKE"), "Supermarkt")

    def test_delete_rule_takes_effect_immediately(self):
        """suggest_category no longer matches a rule after delete_rule."""
        self.categorizer.add_rule(["rewe"], "Supermarkt")
        self.categorizer.delete_rule("Supermarkt")
        self.assertEqual(self.categorizer.suggest_category("REWE SAGT DANKE"), "Sonstiges")

    def test_update_rule_keywords_takes_effect_immediately(self):
        """suggest_category uses the updated keywords after update_rule_keywords."""
        self.categorizer.add_rule(["rewe"], "Supermarkt")
        self.categorizer.update_rule_keywords("Supermarkt", ["aldi"])
        self.assertEqual(self.categorizer.suggest_category("REWE SAGT DANKE"), "Sonstiges")
        self.assertEqual(self.categorizer.suggest_category("ALDI SUED"), "Supermarkt")

if __name__ == "__main__":
    unittest.main()
