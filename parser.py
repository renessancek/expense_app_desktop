import pandas as pd
import uuid
import os
import io

class Parser:
    @staticmethod
    def parse_bank_statement(file_input):
        """
        Parses a bank statement from a CSV file.
        Supports various separators, encodings, and regional column names.
        """
        df = None
        
        # Possible separators and encodings
        separators = [';', ',']
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        # Try different combinations of separator and encoding
        for sep in separators:
            for enc in encodings:
                try:
                    # Handle Streamlit UploadedFile (has seek) or file path
                    if hasattr(file_input, 'seek'):
                        file_input.seek(0)
                        
                    df = pd.read_csv(file_input, sep=sep, encoding=enc)
                    
                    # Heuristic to check if we found the right separator
                    # Check for amount or common German variants
                    possible_amount_cols = ['Amount', 'Betrag', 'amount', 'Wert']
                    if any(col in df.columns for col in possible_amount_cols):
                        print(f"Successfully loaded CSV with separator='{sep}' and encoding='{enc}'")
                        break
                except Exception:
                    continue
            if df is not None and any(col in df.columns for col in possible_amount_cols):
                break
        
        if df is None:
            print("Failed to parse CSV with standard separators and encodings.")
            return []

        # Map common column names (Prioritizing specific regional headers)
        col_map = {
            'Date': ['Buchungsdatum', 'Datum', 'Date'],
            'Description': ['Buchungstext', 'Verwendungszweck', 'Description'],
            'Amount': ['Betrag', 'Amount', 'Wert']
        }
        
        final_cols = {}
        for target, options in col_map.items():
            for opt in options:
                if opt in df.columns:
                    final_cols[target] = opt
                    break
        
        if len(final_cols) < 3:
            print(f"Missing essential columns in CSV. Found: {list(df.columns)}")
            return []

        transactions = []
        import hashlib
        for _, row in df.iterrows():
            try:
                amount_val = row[final_cols['Amount']]
                if isinstance(amount_val, str):
                    # Handle German/Austrian format: 1.234,56
                    # Remove thousands separator and fix decimal
                    amount_str = amount_val.replace('.', '').replace(',', '.')
                    amount = float(amount_str)
                else:
                    amount = float(amount_val)
                
                date_str = str(row[final_cols['Date']])
                desc_str = str(row[final_cols['Description']])
                
                # Generate a stable ID based on transaction data
                hash_input = f"{date_str}{desc_str}{amount}".encode('utf-8')
                tx_id = hashlib.md5(hash_input).hexdigest()[:10]
                
                transactions.append({
                    'id': tx_id,
                    'date': date_str,
                    'description': desc_str[:150],
                    'amount': amount,
                    'category': None
                })
            except Exception as row_error:
                print(f"Skipping row due to error: {row_error}")
                
        return transactions
