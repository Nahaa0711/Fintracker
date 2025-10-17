#!/usr/bin/env python3
"""FinTrack - CIBC Finance Tracker CLI"""
import sys
import os
import io
from pathlib import Path

# Set UTF-8 encoding for Windows Unicode support
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

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
            account_name = account.get('account_name')
            display_name = account_name if account_name else account['account_number']
            print(f"📋 Syncing account: {display_name}")
            transactions = db.get_transactions(account_id=account['id'])
            
            # Debug: Show category info for first few transactions
            print(f"   Found {len(transactions)} transactions")
            if transactions:
                sample_tx = transactions[0]
                print(f"   Sample transaction categories: parent='{sample_tx.get('parent_category', 'None')}', category='{sample_tx.get('category', 'None')}'")
            
            sheets.sync_transactions(transactions, account['account_number'], account_name)
        
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

def recategorize_all(db: Database, categorizer: Categorizer):
    """Recategorize all uncategorized transactions."""
    print("🔄 Recategorizing all transactions...")
    
    # Get all uncategorized transactions
    cursor = db.conn.cursor()
    cursor.execute("SELECT id, description FROM transactions WHERE category_id IS NULL")
    uncategorized = cursor.fetchall()
    
    if not uncategorized:
        print("✓ All transactions are already categorized!")
        return
    
    print(f"Found {len(uncategorized)} uncategorized transactions")
    
    updated_count = 0
    for tx_id, description in uncategorized:
        category_id = categorizer.categorize(description)
        if category_id:
            cursor.execute("UPDATE transactions SET category_id = ? WHERE id = ?", (category_id, tx_id))
            updated_count += 1
            print(f"✓ Categorized: {description[:50]}...")
    
    db.conn.commit()
    print(f"✓ Updated {updated_count} transactions with categories")

def debug_categories(db: Database, categorizer: Categorizer):
    """Debug category information."""
    print("\n=== Category Debug ===\n")
    
    # Show all categories
    categories = db.get_categories()
    print(f"Total categories in database: {len(categories)}")
    
    if not categories:
        print("No categories found! Run: python main.py init-categories")
        return
    
    # Show category tree
    tree = categorizer.get_category_tree()
    print("\nCategory structure:")
    for parent, children in tree.items():
        print(f"  {parent}")
        for child in children:
            print(f"     - {child}")
    
    # Show uncategorized count
    uncategorized = db.get_uncategorized_count()
    print(f"\nUncategorized transactions: {uncategorized}")
    
    # Show sample transactions
    transactions = db.get_transactions(limit=5)
    print(f"\nSample transactions:")
    for tx in transactions:
        print(f"  {tx['date']} | {tx['description'][:30]}... | {tx.get('parent_category', 'None')} | {tx.get('category', 'None')}")
    
    # Test categorization on sample transactions
    print(f"\nTesting categorization on sample transactions:")
    for tx in transactions[:3]:  # Test first 3
        print(f"\nTransaction: {tx['description']}")
        category_id = categorizer.categorize(tx['description'], debug=True)
        if category_id:
            # Find category name
            for cat in categories:
                if cat['id'] == category_id:
                    print(f"  Result: {cat['name']}")
                    break
        else:
            print(f"  Result: No match")

def list_accounts(db: Database):
    """List all accounts with their names."""
    print("\n=== Accounts ===\n")
    
    accounts = db.get_accounts()
    if not accounts:
        print("No accounts found!")
        return
    
    for i, account in enumerate(accounts, 1):
        name = account['account_name'] or "Unnamed"
        print(f"{i}. {account['account_number']}")
        print(f"   Name: {name}")
        print(f"   Type: {account['account_type']}")
        print()

def set_account_name(db: Database, account_number: str = None, new_name: str = None):
    """Set custom name for an account."""
    print("\n=== Set Account Name ===\n")
    
    accounts = db.get_accounts()
    if not accounts:
        print("No accounts found!")
        return
    
    # If account_number and new_name provided via command line
    if account_number and new_name:
        if db.update_account_name(account_number, new_name):
            print(f"✓ Updated account {account_number} name to: {new_name}")
        else:
            print(f"❌ Account {account_number} not found")
        return
    
    # Interactive mode
    print("Available accounts:")
    for i, account in enumerate(accounts, 1):
        name = account['account_name'] or "Unnamed"
        print(f"{i}. {account['account_number']} - {name}")
    
    try:
        choice = int(input("\nSelect account (number): ")) - 1
        if choice < 0 or choice >= len(accounts):
            print("❌ Invalid selection")
            return
        
        account = accounts[choice]
        new_name = input(f"Enter new name for {account['account_number']}: ").strip()
        
        if not new_name:
            print("❌ Name cannot be empty")
            return
        
        if db.update_account_name(account['account_number'], new_name):
            print(f"✓ Updated account name to: {new_name}")
        else:
            print("❌ Failed to update account name")
            
    except (ValueError, KeyboardInterrupt, EOFError):
        print("\n❌ Operation cancelled")


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
  python main.py recategorize         Recategorize all transactions
  python main.py debug-categories     Debug category information
  python main.py list-accounts        List all accounts
  python main.py set-account-name     Set custom name for an account (interactive)
  python main.py set-account-name <account_number> <name>  Set account name via command line
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
        
        elif command == "recategorize":
            recategorize_all(db, categorizer)
        
        elif command == "debug-categories":
            debug_categories(db, categorizer)
        
        elif command == "list-accounts":
            list_accounts(db)
        
        elif command == "set-account-name":
            if len(sys.argv) >= 4:
                # Command line mode: python main.py set-account-name <account_number> <new_name>
                account_number = sys.argv[2]
                new_name = sys.argv[3]
                set_account_name(db, account_number, new_name)
            else:
                # Interactive mode
                set_account_name(db)
        
        else:
            print(f"❌ Unknown command: {command}")
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

