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
        
        # Require at least Date, Description, and Amount
        required = ['Date', 'Description', 'Amount']
        if not all(k in final_cols for k in required):
            print(f"Missing essential columns in CSV. Found: {list(df.columns)}")
            return []

        transactions = []
        import hashlib
        for _, row in df.iterrows():
            try:
                # Handle empty/NaN values
                if pd.isna(row[final_cols['Amount']]) or pd.isna(row[final_cols['Date']]):
                    continue

                amount_val = row[final_cols['Amount']]
                if isinstance(amount_val, str):
                    # Handle formats like -100,00 or 1.234,56
                    amount_str = amount_val.replace('.', '').replace(',', '.')
                    amount = float(amount_str)
                else:
                    amount = float(amount_val)
                
                date_str = str(row[final_cols['Date']])
                
                # Robust Description Extraction
                # Combine all descriptive fields that exist and are not empty
                desc_parts = []
                potential_desc_keys = ['Description', 'Type'] # Description maps to Name/Item Title mapped in col_map
                
                # Re-map specifically for PayPal's multi-column descriptions
                # If 'Name' (mapped to Description) and 'Item Title' both exist, we want both.
                # In current col_map, 'Description' takes the first match. Let's be explicit:
                
                for col in ['Name', 'Item Title', 'Type', 'Buchungstext', 'Verwendungszweck']:
                    if col in df.columns and not pd.isna(row[col]):
                        val = str(row[col]).strip()
                        if val and val.lower() != 'nan' and val not in desc_parts:
                            desc_parts.append(val)
                
                desc_str = " - ".join(desc_parts) if desc_parts else "Unknown Transaction"
                
                # Exclude internal PayPal/Bitpanda records (Check descriptive fields)
                exclusions = ["General Currency Conversion", "General Authorization"]
                if any(ex in desc_str for ex in exclusions):
                    continue
                
                # Use provided Transaction ID if available, otherwise hash details
                tx_unique_id = str(row[final_cols['TxID']]) if 'TxID' in final_cols and not pd.isna(row[final_cols['TxID']]) else None
                
                if tx_unique_id:
                    hash_input = tx_unique_id.encode('utf-8')
                else:
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
