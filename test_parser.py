import unittest
from unittest.mock import MagicMock, patch
from parser import Parser

class TestParser(unittest.TestCase):

    def setUp(self):
        self.parser = Parser()

    @patch('parser.pd')
    def test_parse_bank_statement_failed_load(self, mock_pd):
        # Mock read_csv to always raise Exception
        mock_pd.read_csv.side_effect = Exception("Failed")
        file_input = MagicMock()

        result = self.parser.parse_bank_statement(file_input)
        self.assertEqual(result, [])

    @patch('parser.pd')
    def test_parse_bank_statement_missing_columns(self, mock_pd):
        mock_df = MagicMock()
        mock_df.columns = ['Unknown1', 'Unknown2']
        mock_pd.read_csv.return_value = mock_df

        file_input = MagicMock()
        result = self.parser.parse_bank_statement(file_input)
        self.assertEqual(result, [])

    @patch('parser.pd')
    def test_parse_bank_statement_success(self, mock_pd):
        mock_df = MagicMock()
        # Ensure it passes the amount column check in the heuristic
        mock_columns = MagicMock()
        mock_columns.__iter__.return_value = ['Datum', 'Name', 'Betrag']
        mock_columns.__contains__.side_effect = lambda col: col in ['Datum', 'Name', 'Betrag']

        def mock_get_loc(col):
            return ['Datum', 'Name', 'Betrag'].index(col)
        mock_columns.get_loc = mock_get_loc

        mock_df.columns = mock_columns

        # Mock itertuples
        # row: (Datum, Name, Betrag)
        row1 = ('2023-01-01', 'Test Transaction 1', '1.234,56')
        row2 = ('2023-01-02', 'Test Transaction 2', '-50,00')
        row3 = ('2023-01-03', 'General Currency Conversion', '10.0') # Should be excluded
        row4 = ('2023-01-04', float('nan'), '100.0') # nan description

        mock_df.itertuples.return_value = [row1, row2, row3, row4]

        # Mock isna
        def mock_isna(val):
            if isinstance(val, float) and str(val) == 'nan':
                return True
            return False
        mock_pd.isna.side_effect = mock_isna

        mock_pd.read_csv.return_value = mock_df

        file_input = MagicMock()
        result = self.parser.parse_bank_statement(file_input)

        self.assertEqual(len(result), 3) # row3 excluded

        tx1 = result[0]
        self.assertEqual(tx1['date'], '2023-01-01')
        self.assertEqual(tx1['description'], 'Test Transaction 1')
        self.assertEqual(tx1['amount'], 1234.56)

        tx2 = result[1]
        self.assertEqual(tx2['date'], '2023-01-02')
        self.assertEqual(tx2['description'], 'Test Transaction 2')
        self.assertEqual(tx2['amount'], -50.00)

        tx4 = result[2]
        self.assertEqual(tx4['date'], '2023-01-04')
        self.assertEqual(tx4['description'], 'Unknown Transaction')
        self.assertEqual(tx4['amount'], 1000.0)

if __name__ == '__main__':
    unittest.main()
