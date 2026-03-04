import unittest

try:
    import pandas as pd
except ImportError:
    pd = None


class TestPandasAvailability(unittest.TestCase):

    @unittest.skipIf(pd is None, "pandas is not installed")
    def test_pandas_is_available(self):
        self.assertIsNotNone(pd)
