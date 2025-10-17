"""CIBC PDF statement parser."""
import pdfplumber
import re
from datetime import datetime
from typing import List, Dict, Any, Optional


class CIBCParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf = pdfplumber.open(pdf_path)
        self.statement_type = self._detect_statement_type()
    
    def _detect_statement_type(self) -> str:
        """Detect if this is a credit card or bank account statement."""
        first_page = self.pdf.pages[0].extract_text()
        
        if "Account Statement" in first_page and "Branch transit number" in first_page:
            return "bank_account"
        elif "Visa" in first_page or "Credit Card" in first_page:
            return "credit_card"
        else:
            return "unknown"
    
    def extract_account_info(self) -> Dict[str, str]:
        """Extract account information from first page."""
        first_page = self.pdf.pages[0].extract_text()
        
        if self.statement_type == "bank_account":
            # Bank account format: "Account number\n87-40798"
            account_match = re.search(r'Account number\s*(\d{2}-\d{5})', first_page)
            account_number = account_match.group(1) if account_match else "UNKNOWN"
            account_type = "CIBC Bank Account"
        else:
            # Credit card format: "Account number 4505 XXXX XXXX 7008"
            account_match = re.search(r'Account number\s*(\d{4}\s+X+\s+X+\s+\d{4})', first_page)
            if not account_match:
                account_match = re.search(r'(\d{4}\s+X+\s+X+\s+\d{4})', first_page)
            
            account_number = account_match.group(1).replace(' ', '') if account_match else "UNKNOWN"
            
            # Extract credit card type
            account_type = "CIBC Credit Card"
            if "Dividend" in first_page:
                account_type = "CIBC Dividend Visa"
            elif "Aventura" in first_page:
                account_type = "CIBC Aventura"
        
        return {
            "account_number": account_number,
            "account_name": None,
            "account_type": account_type
        }
    
    def parse_transactions(self) -> List[Dict[str, Any]]:
        """Parse all transactions from the statement."""
        if self.statement_type == "bank_account":
            return self._parse_bank_account_transactions()
        else:
            return self._parse_credit_card_transactions()
    
    def _parse_credit_card_transactions(self) -> List[Dict[str, Any]]:
        """Parse credit card transactions."""
        transactions = []
        
        for page in self.pdf.pages:
            text = page.extract_text()
            
            # Look for transaction sections
            if "Your new charges and credits" in text or "Transactions" in text:
                transactions.extend(self._parse_transaction_page(text))
        
        return transactions
    
    def _parse_bank_account_transactions(self) -> List[Dict[str, Any]]:
        """Parse bank account transactions."""
        transactions = []
        current_year = datetime.now().year
        
        for page in self.pdf.pages:
            text = page.extract_text()
            lines = text.split('\n')
            
            in_transaction_section = False
            
            for line in lines:
                # Start parsing after header
                if "Date Description Withdrawals" in line or "Transaction details" in line:
                    in_transaction_section = True
                    continue
                
                if not in_transaction_section:
                    continue
                
                # Skip opening balance line
                if "Opening balance" in line:
                    continue
                
                # Parse transaction line
                # Format: Sep 2 VISA DEBIT RETAIL PURCHASE 37.67 898.18
                match = re.match(
                    r'([A-Z][a-z]{2}\s+\d{1,2})\s+(.+?)\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})$',
                    line
                )
                
                if match:
                    date_str = match.group(1)
                    description = match.group(2).strip()
                    amount = float(match.group(3).replace(',', ''))
                    balance = float(match.group(4).replace(',', ''))
                    
                    # Convert date
                    trans_date = self._parse_date(date_str, current_year)
                    
                    # Bank account shows withdrawals as positive, deposits on next column
                    # For consistency, withdrawals are negative in our system
                    transactions.append({
                        "date": trans_date,
                        "description": description,
                        "amount": -amount,  # Withdrawals as negative
                        "balance": balance
                    })
        
        return transactions
    
    def _parse_transaction_page(self, text: str) -> List[Dict[str, Any]]:
        """Parse transactions from a page of text."""
        transactions = []
        lines = text.split('\n')
        
        in_transaction_section = False
        current_year = datetime.now().year
        
        for i, line in enumerate(lines):
            # Detect transaction section start - check for the header or "Spend Categories"
            if ("Trans Post" in line) or ("date date Description" in line) or ("Spend Categories" in line):
                in_transaction_section = True
                continue
            
            # Skip card number line
            if "Card number" in line:
                continue
            
            # Stop at page footer or next section
            if ("Page" in line and "of" in line) or "Information about your" in line:
                in_transaction_section = False
                continue
            
            if not in_transaction_section:
                continue
            
            # Skip special characters and payment lines
            if "PAYMENT THANK YOU" in line or "Total payments" in line or line.strip() == "Ý":
                continue
            
            # Parse transaction line
            # Format: Sep 06 Sep 08 SHOPPERS DRUG MART #13 TORONTO ON Health and Education 26.88
            tx_match = re.match(
                r'([A-Z][a-z]{2}\s+\d{2})\s+([A-Z][a-z]{2}\s+\d{2})\s+(.+?)\s+([\d,]+\.\d{2})$',
                line
            )
            
            if tx_match:
                trans_date_str = tx_match.group(1)
                post_date_str = tx_match.group(2)
                description_raw = tx_match.group(3).strip()
                amount_str = tx_match.group(4)
                
                # Clean description (remove CIBC category if present at end)
                description = re.sub(
                    r'\s+(Health and Education|Restaurants|Retail and Grocery|Professional and Financial Services|Gas and Groceries|Gas Stations)$',
                    '', 
                    description_raw
                ).strip()
                
                # Convert date to YYYY-MM-DD
                trans_date = self._parse_date(trans_date_str, current_year)
                
                # Convert amount
                amount = float(amount_str.replace(',', ''))
                
                transactions.append({
                    "date": trans_date,
                    "description": description,
                    "amount": amount,
                    "balance": None  # CIBC credit card statements don't show running balance
                })
        
        return transactions
    
    def _parse_date(self, date_str: str, year: int) -> str:
        """Convert 'Sep 06' to '2025-09-06'."""
        try:
            date_obj = datetime.strptime(f"{date_str} {year}", "%b %d %Y")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            return date_str
    
    def close(self):
        """Close PDF file."""
        self.pdf.close()

