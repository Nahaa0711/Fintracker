#!/usr/bin/env python3
"""FinTrack - CIBC Finance Tracker CLI"""
import sys
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.database import Database
from src.parser import CIBCParser
from src.categorizer import Categorizer


def parse_pdf(pdf_path: str, db: Database, categorizer: Categorizer):
    """Parse a single PDF statement."""
    print(f"📄 Parsing {pdf_path}...")
    
    parser = CIBCParser(pdf_path)
    
    # Extract account info
    account_info = parser.extract_account_info()
    account_id = db.add_account(
        account_info['account_number'],
        account_info['account_name'],
        account_info['account_type']
    )
    print(f"✓ Account: {account_info['account_number']} ({account_info['account_type']})")
    
    # Parse transactions
    transactions = parser.parse_transactions()
    print(f"✓ Found {len(transactions)} transactions")
    
    # Add to database with categorization
    new_count = 0
    for tx in transactions:
        category_id = categorizer.categorize(tx['description'])
        tx_id = db.add_transaction(
            account_id=account_id,
            date=tx['date'],
            description=tx['description'],
            amount=tx['amount'],
            balance=tx.get('balance'),
            category_id=category_id
        )
        if tx_id:
            new_count += 1
    
    print(f"✓ Added {new_count} new transactions ({len(transactions) - new_count} duplicates skipped)")
    parser.close()

def parse_all(db: Database, categorizer: Categorizer):
    """Parse all PDFs in Statements directory."""
    statements_dir = Path("Statements")
    
    if not statements_dir.exists():
        print("❌ Statements/ directory not found")
        return
    
    pdf_files = list(statements_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found in Statements/")
        return
    
    print(f"📁 Found {len(pdf_files)} statement(s)\n")
    
    for pdf_file in pdf_files:
        parse_pdf(str(pdf_file), db, categorizer)
        print()

def sync_to_sheets(db: Database):
    """Sync database to Google Sheets."""
    try:
        from src.sheets import SheetsClient
    except ImportError:
        print("❌ Google Sheets dependencies not installed")
        print("   Run: pip install -r requirements.txt")
        return
    
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE')
    spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
    
    if not credentials_file or not spreadsheet_id:
        print("❌ Missing Google Sheets configuration in .env")
        print("   Set GOOGLE_CREDENTIALS_FILE and GOOGLE_SPREADSHEET_ID")
        return
    
    if not Path(credentials_file).exists():
        print(f"❌ Credentials file not found: {credentials_file}")
        return
    
    print("📊 Syncing to Google Sheets...")
    
    try:
        sheets = SheetsClient(credentials_file, spreadsheet_id)
        accounts = db.get_accounts()
        
        for account in accounts:
            transactions = db.get_transactions(account_id=account['id'])
            sheets.sync_transactions(transactions, account['account_number'])
        
        print("\n✓ Sync complete!")
        
    except Exception as e:
        print(f"❌ Error syncing to sheets: {e}")

def add_category(db: Database, categorizer: Categorizer):
    """Interactive category addition."""
    print("\n=== Add New Category ===\n")
    
    # Show existing categories
    tree = categorizer.get_category_tree()
    print("Existing categories:")
    for parent, children in tree.items():
        print(f"  {parent}")
        for child in children:
            print(f"    - {child}")
    print()
    
    # Get input
    parent = input("Parent category (leave blank for new parent): ").strip()
    name = input("Category name: ").strip()
    keywords = input("Keywords (comma-separated): ").strip()
    
    if not name or not keywords:
        print("❌ Name and keywords required")
        return
    
    keyword_list = [k.strip() for k in keywords.split(',')]
    
    category_id = categorizer.add_category_with_keywords(
        name=name,
        keywords=keyword_list,
        parent_name=parent if parent else None
    )
    
    print(f"✓ Added category: {name} (ID: {category_id})")

def list_categories(categorizer: Categorizer):
    """List all categories."""
    print("\n=== Categories ===\n")
    
    tree = categorizer.get_category_tree()
    
    for parent, children in sorted(tree.items()):
        print(f"📁 {parent}")
        for child in children:
            print(f"   └─ {child}")
        print()

def show_stats(db: Database):
    """Show database statistics."""
    print("\n=== Stats ===\n")
    
    accounts = db.get_accounts()
    print(f"Accounts: {len(accounts)}")
    for acc in accounts:
        print(f"  - {acc['account_number']} ({acc['account_type']})")
    
    transactions = db.get_transactions()
    print(f"\nTotal Transactions: {len(transactions)}")
    
    uncategorized = db.get_uncategorized_count()
    print(f"Uncategorized: {uncategorized}")
    
    if uncategorized > 0:
        print(f"\n⚠️  {uncategorized} transactions need categorization")
        print("   Add categories with: python main.py add-category")


def init_categories(categorizer: Categorizer):
    """Initialize default categories."""
    print("🏷️  Initializing default categories...")
    categorizer.initialize_default_categories()
    print("✓ Default categories added!")


def main():
    if len(sys.argv) < 2:
        print("""
FinTrack - CIBC Finance Tracker

Usage:
  python main.py parse <pdf_file>     Parse single PDF statement
  python main.py parse-all            Parse all PDFs in Statements/
  python main.py sync                 Sync database to Google Sheets
  python main.py add-category         Add new category interactively
  python main.py list-categories      List all categories
  python main.py stats                Show database statistics
  python main.py init-categories      Initialize default categories
        """)
        return
    
    command = sys.argv[1]
    
    # Initialize database and categorizer
    db = Database()
    categorizer = Categorizer(db)
    
    try:
        if command == "parse":
            if len(sys.argv) < 3:
                print("❌ Usage: python main.py parse <pdf_file>")
                return
            parse_pdf(sys.argv[2], db, categorizer)
        
        elif command == "parse-all":
            parse_all(db, categorizer)
        
        elif command == "sync":
            sync_to_sheets(db)
        
        elif command == "add-category":
            add_category(db, categorizer)
        
        elif command == "list-categories":
            list_categories(categorizer)
        
        elif command == "stats":
            show_stats(db)
        
        elif command == "init-categories":
            init_categories(categorizer)
        
        else:
            print(f"❌ Unknown command: {command}")
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

