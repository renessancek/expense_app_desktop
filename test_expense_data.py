import unittest

from expense_data import ExpenseDataStore


class ScannerStub:
    def scan_for_csvs(self):
        return ["scanned.csv"]


class ParserStub:
    def parse_bank_statement_with_report(self, path):
        return ([
            {"date": "01.07.2026", "description": "MAYER Energie", "amount": -10.0},
            {"date": "02.07.2026", "description": "Other payment", "amount": -20.0},
        ], {"status": "Imported"})


class CategorizerStub:
    def suggest_category(self, description):
        return "Utilities" if "Energie" in description else "Sonstiges"


class TestExpenseDataStore(unittest.TestCase):
    def setUp(self):
        self.store = ExpenseDataStore(ScannerStub(), ParserStub(), CategorizerStub())
        self.store.reload([])

    def test_search_is_case_insensitive_literal_and_combines_with_filters(self):
        self.assertEqual(len(self.store.filtered(query="mayer")), 1)
        self.assertEqual(len(self.store.filtered(query="MAYER")), 1)
        self.assertEqual(len(self.store.filtered(query="mayer.*")), 0)
        self.assertEqual(len(self.store.filtered(category="Utilities", month="2026-07", query="energie")), 1)

    def test_reports_keep_the_import_source_file(self):
        self.assertEqual(self.store.import_reports[0]["File"], "scanned.csv")

    def test_reload_does_not_import_a_scanned_file_twice_when_it_was_also_selected(self):
        self.store.reload(["scanned.csv"])

        self.assertEqual(len(self.store.transactions), 2)
        self.assertEqual([transaction["source"] for transaction in self.store.transactions], ["Scanned", "Scanned"])
