import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:
    import pandas as pd
except ImportError:
    pd = None


class TestPandasAvailability(unittest.TestCase):

    @unittest.skipIf(pd is None, "pandas is not installed")
    def test_pandas_is_available(self):
        self.assertIsNotNone(pd)

@unittest.skipIf(pd is None, "pandas is not installed")
class TestStatisticsExportSelection(unittest.TestCase):

    def test_only_selected_categories_are_returned_for_export(self):
        from desktop_app import statistics_for_categories

        totals = pd.DataFrame({
            "Category": ["Food", "Rent", "Transport"],
            "Total spent (€)": [20.0, 900.0, 40.0],
        })

        result = statistics_for_categories(totals, ["Food", "Transport"])

        self.assertEqual(result["Category"].tolist(), ["Food", "Transport"])

    def test_empty_selection_returns_no_rows(self):
        from desktop_app import statistics_for_categories

        totals = pd.DataFrame({"Category": ["Food"], "Total spent (€)": [20.0]})

        self.assertTrue(statistics_for_categories(totals, []).empty)


@unittest.skipIf(pd is None, "pandas is not installed")
class TestListedAmountSum(unittest.TestCase):

    def test_sums_all_filtered_amounts_without_adding_a_column(self):
        from desktop_app import format_listed_amount_sum, listed_amount_sum

        frame = pd.DataFrame({
            "date": ["2026-07-01", "2026-07-02", "2026-07-03"],
            "amount": [-10.0, -20.5, 5.0],
        })

        self.assertEqual(listed_amount_sum(frame), -25.5)
        self.assertEqual(format_listed_amount_sum(-25.5), "Sum of listed transactions: -25.50 €")
        self.assertEqual(list(frame.columns), ["date", "amount"])

    def test_empty_or_missing_amount_is_zero(self):
        from desktop_app import listed_amount_sum

        self.assertEqual(listed_amount_sum(pd.DataFrame()), 0.0)
        self.assertEqual(listed_amount_sum(pd.DataFrame({"description": ["x"]})), 0.0)


try:
    from PySide6.QtWidgets import QApplication, QTableView
except ImportError:
    QApplication = None


@unittest.skipIf(pd is None or QApplication is None, "pandas or PySide6 is not installed")
class TestTransactionListSumFooter(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import os

        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QApplication.instance() or QApplication([])

    def test_sum_sits_under_the_rows_and_follows_the_filtered_list(self):
        from desktop_app import ExpenseWindow

        window = ExpenseWindow()
        try:
            self.assertNotIn("Sum", ExpenseWindow.TABLE_COLUMNS)
            self.assertNotIn("Source", ExpenseWindow.TABLE_COLUMNS)
            self.assertNotIn("source", ExpenseWindow.FRAME_COLUMNS)
            self.assertEqual(window.transaction_table.model().columnCount(), len(ExpenseWindow.TABLE_COLUMNS))

            layout = window.transaction_table.parentWidget().layout()
            widgets = [layout.itemAt(index).widget() for index in range(layout.count()) if layout.itemAt(index).widget()]
            self.assertGreater(widgets.index(window.list_sum_label), widgets.index(window.transaction_table))
            self.assertIsInstance(window.transaction_table, QTableView)

            window.store.transactions = [
                {"date": "01.07.2026", "description": "Market", "amount": -10.0, "category": "Food", "file": "a.csv"},
                {"date": "02.07.2026", "description": "Landlord", "amount": -20.0, "category": "Rent", "file": "a.csv"},
            ]
            window.store.import_reports = []
            window.search_input.setText("Market")
            window.refresh_transactions()
            self.assertEqual(window.list_sum_label.text(), "Sum of listed transactions: -10.00 €")
        finally:
            window.close()

    def test_receipts_tab_is_present(self):
        from desktop_app import ExpenseWindow

        window = ExpenseWindow()
        try:
            titles = [window.tabs.tabText(index) for index in range(window.tabs.count())]
            self.assertEqual(titles[0], "Transactions")
            self.assertEqual(titles[1], "Receipts")
            self.assertEqual(window.receipt_choose_button.text(), "Choose folder…")
            self.assertEqual(window.receipt_table.model().columnCount(), 7)
        finally:
            window.close()

    def test_receipt_import_table_lists_files_with_details_button(self):
        from PySide6.QtWidgets import QPushButton

        from desktop_app import ExpenseWindow

        window = ExpenseWindow()
        try:
            window.set_receipt_imports([
                {
                    "file": "spar.pdf",
                    "merchant": "SPAR - SUPERMARKT",
                    "date": "2026-08-03",
                    "total": 10.85,
                    "item_count": 8,
                    "status": "Extracted",
                    "error": "",
                    "result": {"merchant": "SPAR - SUPERMARKT", "items": [], "raw_text": "SPAR"},
                },
                {
                    "file": "bad.png",
                    "merchant": None,
                    "date": None,
                    "total": None,
                    "item_count": 0,
                    "status": "Failed",
                    "error": "Could not read file",
                    "result": None,
                },
            ])
            self.assertEqual(window.receipt_table.model().rowCount(), 2)
            self.assertEqual(window.receipt_table.model().data(window.receipt_table.model().index(0, 0)), "spar.pdf")
            self.assertEqual(window.receipt_table.model().data(window.receipt_table.model().index(0, 3)), "10.85 €")
            button = window.receipt_table.indexWidget(window.receipt_import_model.index(0, 6))
            self.assertIsInstance(button, QPushButton)
            self.assertEqual(button.text(), "See extracted data")
        finally:
            window.close()

    def test_receipt_extract_dialog_fills_from_fixture(self):
        from PySide6.QtWidgets import QLabel, QTextEdit

        from desktop_app import ExpenseWindow, receipt_extract_dialog

        window = ExpenseWindow()
        try:
            result = {
                "merchant": "REWE",
                "merchant_category": "Supermarkt",
                "date": "2026-05-12",
                "currency": "EUR",
                "subtotal": 1.29,
                "tax": 0.08,
                "total": 1.29,
                "notes": "Test note",
                "raw_text": "REWE\nVollmilch 1L 1,29",
                "items": [{
                    "description": "Vollmilch 1L",
                    "quantity": 1.0,
                    "amount": 1.29,
                    "category": "Supermarkt",
                }],
            }
            dialog = receipt_extract_dialog(window, result)
            notes = dialog.findChild(QLabel, "receipt_notes")
            raw = dialog.findChild(QTextEdit, "receipt_raw_json")
            table = dialog.findChild(QTableView, "receipt_items_table")
            self.assertEqual(notes.text(), "Test note")
            self.assertIn("REWE", raw.toPlainText())
            self.assertIn("Vollmilch 1L", raw.toPlainText())
            self.assertEqual(table.model().rowCount(), 1)
            self.assertEqual(table.model().data(table.model().index(0, 0)), "Vollmilch 1L")
        finally:
            window.close()

@unittest.skipIf(pd is None, "pandas is not installed")
class TestYearlyStatisticsExport(unittest.TestCase):

    def test_yearly_export_matches_legacy_sheet_structure(self):
        import tempfile
        from pathlib import Path

        from desktop_app import selected_expenses_for_export, write_yearly_statistics_export

        frame = pd.DataFrame({
            "date": pd.to_datetime(["2026-01-10", "2026-01-12", "2026-02-03", "2026-02-05", "2026-03-02"]),
            "amount": [-10.0, -20.0, -30.0, 99.0, -40.0],
            "category": ["Food", "Rent", "Food", "Food", "Food"],
        })
        selected = selected_expenses_for_export(frame, ["Food"])
        rules = [
            {"category": "Food", "keywords": ["market"]},
            {"category": "Rent", "keywords": ["landlord"]},
        ]

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "yearly_report.xlsx"
            write_yearly_statistics_export(path, selected, ["Food"], rules)
            workbook = pd.ExcelFile(path)
            self.assertEqual(workbook.sheet_names, [
                "2026-01", "2026-02", "2026-03", "Monthly Totals", "Average Monthly Expenses",
                "Yearly Comparison", "Yearly Summary", "Configured Categories",
            ])
            workbook.close()
            january = pd.read_excel(path, sheet_name="2026-01")
            self.assertEqual(january.columns.tolist(), ["category", "amount"])
            self.assertEqual(january["category"].tolist(), ["Food", "TOTAL"])
            self.assertEqual(january["amount"].tolist(), [10.0, 10.0])
            monthly_totals = pd.read_excel(path, sheet_name="Monthly Totals")
            self.assertEqual(monthly_totals["Month"].tolist(), ["2026-01", "2026-02", "2026-03", "GRAND TOTAL"])
            configured = pd.read_excel(path, sheet_name="Configured Categories")
            self.assertEqual(configured["category"].tolist(), ["Food", "Rent"])
            from openpyxl import load_workbook
            workbook = load_workbook(path, data_only=True)
            averages_sheet = workbook["Average Monthly Expenses"]
            self.assertEqual(averages_sheet["B2"].value, 26.67)
            self.assertEqual(averages_sheet["B2"].number_format, "#,##0.##")
            workbook.close()
