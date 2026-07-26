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
