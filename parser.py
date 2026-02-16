import pandas as pd
import uuid
import os

class Parser:
    @staticmethod
    def parse_bank_statement(file_input):
        """
        Parses a bank statement from a CSV file.
        Expects columns: Date, Description, Amount
        Handles both dot and comma as decimal separators.
        """
        transactions = []
        try:
            # Try semicolon first (common in German banks), then comma
            try:
                df = pd.read_csv(file_input, sep=';', encoding='utf-8')
                if 'Amount' not in df.columns and 'Betrag' not in df.columns:
                    raise ValueError("Wrong separator")
            except:
                df = pd.read_csv(file_input, sep=',', encoding='utf-8')

            # Map common column names
            col_map = {
                'Date': ['Date', 'Datum', 'date'],
                'Description': ['Description', 'Verwendungszweck', 'description', 'Name'],
                'Amount': ['Amount', 'Betrag', 'amount', 'Wert']
            }
            
            final_cols = {}
            for target, options in col_map.items():
                for opt in options:
                    if opt in df.columns:
                        final_cols[target] = opt
                        break
            
            if len(final_cols) < 3:
                print(f"Missing columns in CSV. Found: {list(df.columns)}")
                return []

            for _, row in df.iterrows():
                try:
                    amount_val = row[final_cols['Amount']]
                    if isinstance(amount_val, str):
                        # Handle German format: 1.234,56
                        amount_str = amount_val.replace('.', '').replace(',', '.')
                        amount = float(amount_str)
                    else:
                        amount = float(amount_val)
                    
                    transactions.append({
                        'id': str(uuid.uuid4())[:9],
                        'date': str(row[final_cols['Date']]),
                        'description': str(row[final_cols['Description']])[:100],
                        'amount': amount,
                        'category': None
                    })
                except Exception as row_error:
                    print(f"Skipping row due to error: {row_error}")
                    
        except Exception as e:
            print(f"Error parsing CSV: {e}")
            
        return transactions
