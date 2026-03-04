import pandas as pd
import hashlib

class Parser:
    @staticmethod
    def parse_bank_statement(file_input):
        """
        Parses a bank statement from a CSV file.
        Supports various separators, encodings, and regional column names.
        """
        df = Parser._load_csv(file_input)
        if df is None:
            return []

        final_cols = Parser._map_columns(df)
        if not final_cols:
            return []

        return Parser._extract_transactions(df, final_cols)

    @staticmethod
    def _load_csv(file_input):
        separators = [';', ',']
        encodings = ['utf-8', 'latin-1', 'cp1252']
        possible_amount_cols = ['Amount', 'Betrag', 'amount', 'Wert']
        df = None

        for sep in separators:
            for enc in encodings:
                try:
                    if hasattr(file_input, 'seek'):
                        file_input.seek(0)
                        
                    df = pd.read_csv(file_input, sep=sep, encoding=enc)
                    
                    if any(col in df.columns for col in possible_amount_cols):
                        print(f"Successfully loaded CSV with separator='{sep}' and encoding='{enc}'")
                        break
                except Exception:
                    continue
            if df is not None and any(col in df.columns for col in possible_amount_cols):
                break
        
        if df is None:
            print("Failed to parse CSV with standard separators and encodings.")
            return None
        return df

    @staticmethod
    def _map_columns(df):
        col_map = {
            'Date': ['Buchungsdatum', 'Datum', 'Date'],
            'Description': ['Buchungstext', 'Verwendungszweck', 'Description', 'Name', 'Item Title'],
            'Amount': ['Betrag', 'Amount', 'Wert', 'Total'],
            'TxID': ['Transaction ID', 'Referenz', 'id'],
            'Type': ['Type', 'Status']
        }
        
        final_cols = {}
        for target, options in col_map.items():
            for opt in options:
                if opt in df.columns:
                    final_cols[target] = opt
                    break
        
        required = ['Date', 'Description', 'Amount']
        if not all(k in final_cols for k in required):
            print(f"Missing essential columns in CSV. Found: {list(df.columns)}")
            return None
        return final_cols

    @staticmethod
    def _extract_transactions(df, final_cols):
        amount_idx = df.columns.get_loc(final_cols['Amount'])
        date_idx = df.columns.get_loc(final_cols['Date'])
        txid_col = final_cols.get('TxID')
        txid_idx = df.columns.get_loc(txid_col) if txid_col else None

        potential_desc_cols = ['Description', 'Name', 'Item Title', 'Type', 'Buchungstext', 'Verwendungszweck']
        desc_col_indices = [df.columns.get_loc(col) for col in potential_desc_cols if col in df.columns]

        transactions = []
        for row in df.itertuples(index=False, name=None):
            try:
                if pd.isna(row[amount_idx]) or pd.isna(row[date_idx]):
                    continue

                amount_val = row[amount_idx]
                if isinstance(amount_val, str):
                    amount_str = amount_val.replace('.', '').replace(',', '.')
                    amount = float(amount_str)
                else:
                    amount = float(amount_val)
                
                date_str = str(row[date_idx])
                
                desc_parts = []
                for idx in desc_col_indices:
                    val_raw = row[idx]
                    if not pd.isna(val_raw):
                        val = str(val_raw).strip()
                        if val and val.lower() != 'nan' and val not in desc_parts:
                            desc_parts.append(val)
                
                desc_str = " - ".join(desc_parts) if desc_parts else "Unknown Transaction"
                
                exclusions = ["General Currency Conversion", "General Authorization", "User Initiated Withdrawal"]
                if any(ex in desc_str for ex in exclusions):
                    continue
                
                tx_unique_id = str(row[txid_idx]) if txid_idx is not None and not pd.isna(row[txid_idx]) else None
                
                if tx_unique_id:
                    hash_input = tx_unique_id.encode('utf-8')
                else:
                    hash_input = f"{date_str}{desc_str}{amount}".encode('utf-8')
                
                tx_id = hashlib.sha256(hash_input).hexdigest()[:10]
                
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
