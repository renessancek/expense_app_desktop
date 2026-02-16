import pdfplumber
import re
import uuid

class Parser:
    @staticmethod
    def parse_bank_statement(file_input):
        transactions = []
        try:
            with pdfplumber.open(file_input) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        transactions.extend(Parser.extract_transactions_from_text(text))
        except Exception as e:
            print(f"Error parsing: {e}")
        return transactions

    @staticmethod
    def extract_transactions_from_text(text):
        transactions = []
        # Regex for Date (DD.MM.YYYY or DD.MM.YY)
        date_regex = r'\d{2}\.\d{2}\.\d{2,4}'
        
        # Split text into lines to process each line or group of lines
        lines = text.split('\n')
        
        for line in lines:
            date_match = re.search(date_regex, line)
            if date_match:
                # Look for amount (e.g., -123,45 or 1.234,56)
                # German bank statements often use comma for decimals
                amount_regex = r'(-?\d{1,3}(\.\d{3})*,\d{2})'
                amount_match = re.search(amount_regex, line)
                
                if amount_match:
                    date = date_match.group(0)
                    amount_str = amount_match.group(1).replace('.', '').replace(',', '.')
                    amount = float(amount_str)
                    
                    # The description is usually what's left between the date and the amount
                    description = line.replace(date, '').replace(amount_match.group(0), '').strip()
                    
                    if description:
                        transactions.append({
                            'id': str(uuid.uuid4())[:9],
                            'date': date,
                            'description': description[:100],
                            'amount': amount,
                            'category': None
                        })
        return transactions
