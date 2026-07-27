import unittest

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
            configured = pd.read_excel(path, sheet_name="Configured Categories")
            self.assertEqual(configured["category"].tolist(), ["Food", "Rent"])
