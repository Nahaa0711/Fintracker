"""Google Sheets integration for transaction syncing."""
import os
from typing import List, Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class SheetsClient:
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=self.credentials)
    
    def get_or_create_sheet(self, sheet_name: str) -> str:
        """Get or create a sheet with the given name."""
        try:
            # Check if sheet exists
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheets = spreadsheet.get('sheets', [])
            for sheet in sheets:
                if sheet['properties']['title'] == sheet_name:
                    return sheet_name
            
            # Create new sheet
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            # Add header row
            self._write_header(sheet_name)
            
            return sheet_name
            
        except HttpError as e:
            print(f"Error accessing sheet: {e}")
            raise
    
    def _write_header(self, sheet_name: str):
        """Write header row to sheet."""
        headers = [['Date', 'Description', 'Amount', 'Balance', 'Category', 'Subcategory']]
        
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"{sheet_name}!A1:F1",
            valueInputOption='RAW',
            body={'values': headers}
        ).execute()
        
        # Format header row
        body = {
            'requests': [{
                'repeatCell': {
                    'range': {
                        'sheetId': self._get_sheet_id(sheet_name),
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                            'textFormat': {'bold': True}
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                }
            }]
        }
        
        self.service.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id,
            body=body
        ).execute()
    
    def _get_sheet_id(self, sheet_name: str) -> int:
        """Get sheet ID by name."""
        spreadsheet = self.service.spreadsheets().get(
            spreadsheetId=self.spreadsheet_id
        ).execute()
        
        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']
        
        return 0
    
    def get_existing_transactions(self, sheet_name: str, limit: int = 1000) -> List[List[str]]:
        """Get last N transactions from sheet to check for duplicates."""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A2:F{limit+2}"  # Skip header
            ).execute()
            
            return result.get('values', [])
        except HttpError:
            return []
    
    def append_transactions(self, sheet_name: str, transactions: List[Dict[str, Any]]):
        """Append transactions to sheet."""
        if not transactions:
            return
        
        # Convert transactions to rows
        rows = []
        for tx in transactions:
            rows.append([
                tx.get('date', ''),
                tx.get('description', ''),
                tx.get('amount', ''),
                tx.get('balance', '') if tx.get('balance') else '',
                tx.get('parent_category', ''),
                tx.get('category', '')
            ])
        
        # Append to sheet
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"{sheet_name}!A:F",
            valueInputOption='USER_ENTERED',
            body={'values': rows}
        ).execute()
        
        print(f"✓ Appended {len(rows)} transactions to '{sheet_name}'")
    
    def check_row_count(self, sheet_name: str) -> int:
        """Get row count for a sheet."""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:A"
            ).execute()
            
            rows = result.get('values', [])
            return len(rows)
        except HttpError:
            return 0
    
    def sync_transactions(self, transactions: List[Dict[str, Any]], account_number: str):
        """Sync transactions to appropriate sheet."""
        # Sanitize sheet name
        sheet_name = f"Account_{account_number.replace(' ', '_')}"
        
        # Get or create sheet
        self.get_or_create_sheet(sheet_name)
        
        # Check row count - create new sheet if over 10k
        row_count = self.check_row_count(sheet_name)
        if row_count > 10000:
            sheet_name = f"{sheet_name}_2"
            self.get_or_create_sheet(sheet_name)
        
        # Get existing transactions to avoid duplicates
        existing = self.get_existing_transactions(sheet_name)
        existing_set = {(row[0], row[1], row[2]) for row in existing if len(row) >= 3}
        
        # Filter out duplicates
        new_transactions = []
        for tx in transactions:
            key = (tx.get('date', ''), tx.get('description', ''), str(tx.get('amount', '')))
            if key not in existing_set:
                new_transactions.append(tx)
        
        # Append new transactions
        if new_transactions:
            self.append_transactions(sheet_name, new_transactions)
        else:
            print(f"✓ No new transactions to sync for '{sheet_name}'")




