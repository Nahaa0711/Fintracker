"""Database layer for financial tracking."""
import sqlite3
import hashlib
import json
from datetime import datetime
from typing import Optional, List, Dict, Any


class Database:
    def __init__(self, db_path: str = "fintrack.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """Create database schema."""
        cursor = self.conn.cursor()
        
        # Accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_number TEXT UNIQUE NOT NULL,
                account_name TEXT,
                account_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Categories table (hierarchical)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER,
                keywords TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES categories(id),
                UNIQUE(name, parent_id)
            )
        """)
        
        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                balance REAL,
                category_id INTEGER,
                hash TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id),
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id)")
        
        self.conn.commit()
    
    def add_account(self, account_number: str, account_name: str = None, account_type: str = None) -> int:
        """Add or get account ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO accounts (account_number, account_name, account_type) VALUES (?, ?, ?)",
            (account_number, account_name, account_type)
        )
        self.conn.commit()
        
        cursor.execute("SELECT id FROM accounts WHERE account_number = ?", (account_number,))
        return cursor.fetchone()[0]
    
    def add_category(self, name: str, parent_id: Optional[int] = None, keywords: List[str] = None) -> int:
        """Add category with optional keywords."""
        cursor = self.conn.cursor()
        keywords_json = json.dumps(keywords) if keywords else None
        
        try:
            cursor.execute(
                "INSERT INTO categories (name, parent_id, keywords) VALUES (?, ?, ?)",
                (name, parent_id, keywords_json)
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Category already exists
            cursor.execute(
                "SELECT id FROM categories WHERE name = ? AND parent_id IS ?",
                (name, parent_id)
            )
            return cursor.fetchone()[0]
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories with hierarchy."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, parent_id, keywords FROM categories")
        return [dict(row) for row in cursor.fetchall()]
    
    def add_transaction(self, account_id: int, date: str, description: str, 
                       amount: float, balance: float = None, category_id: int = None) -> Optional[int]:
        """Add transaction if not duplicate."""
        # Create hash for duplicate detection
        hash_str = f"{account_id}|{date}|{description}|{amount}"
        tx_hash = hashlib.md5(hash_str.encode()).hexdigest()
        
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO transactions (account_id, date, description, amount, balance, category_id, hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (account_id, date, description, amount, balance, category_id, tx_hash))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Duplicate transaction
            return None
    
    def get_transactions(self, account_id: Optional[int] = None, limit: int = None) -> List[Dict[str, Any]]:
        """Get transactions with category info."""
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                t.id, t.date, t.description, t.amount, t.balance,
                c.name as category, pc.name as parent_category,
                a.account_number, a.account_name
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            LEFT JOIN categories pc ON c.parent_id = pc.id
            LEFT JOIN accounts a ON t.account_id = a.id
        """
        
        if account_id:
            query += " WHERE t.account_id = ?"
            params = (account_id,)
        else:
            params = ()
        
        query += " ORDER BY t.date DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_uncategorized_count(self) -> int:
        """Get count of uncategorized transactions."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE category_id IS NULL")
        return cursor.fetchone()[0]
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get all accounts."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, account_number, account_name, account_type FROM accounts")
        return [dict(row) for row in cursor.fetchall()]
    
    def update_account_name(self, account_number: str, custom_name: str) -> bool:
        """Update the custom name for an account."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE accounts SET account_name = ? WHERE account_number = ?",
            (custom_name, account_number)
        )
        self.conn.commit()
        return cursor.rowcount > 0
    
    def close(self):
        """Close database connection."""
        self.conn.close()




