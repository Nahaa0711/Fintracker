<!-- 36f9157d-294b-4b0b-893b-18116365e71a 974f54bf-c33a-4138-85dc-9de4cf9454ce -->
# CIBC Finance Tracker (Minimal)

## Overview

Python system that parses CIBC PDF statements, stores in local SQLite database with dynamic categorization, and syncs to Google Sheets for verification and analysis.

## Core Architecture

**Data Flow:**

PDF → Parser → SQLite DB (with categories) → Google Sheets

**Key Features:**

- Multi-account support (auto-detect from statements)
- Dynamic categories/subcategories (add/remove on the fly)
- Local database as source of truth
- Google Sheets for viewing/verification
- Auto-create new sheets when data grows

## Database Schema

```sql
accounts: id, account_number, account_name, account_type
categories: id, name, parent_id (for subcategories), keywords (JSON)
transactions: id, account_id, date, description, amount, balance, category_id, hash (for duplicates)
```

## Implementation Steps

### 1. Project Setup

- Python venv, install: `pdfplumber`, `google-api-python-client`, `pandas`
- SQLite database file
- `.env` for Google credentials
- `.gitignore` for sensitive files

### 2. Database Layer (`src/database.py`)

- Create tables with schema above
- CRUD operations for accounts, categories, transactions
- Duplicate detection using transaction hash
- Category matching by keywords (JSON field)

### 3. PDF Parser (`src/parser.py`)

- Extract account info from PDF header
- Parse transaction table (date, description, amount, balance)
- Auto-detect which account(s) in statement
- Return structured data

### 4. Categorization Engine (`src/categorizer.py`)

- Load categories and keywords from DB
- Match transaction description against keywords
- Support hierarchical categories (parent/child)
- Return "Uncategorized" if no match
- Simple JSON config for category rules:
```json
{
  "Food": {
    "Groceries": ["walmart", "safeway", "loblaws"],
    "Dining": ["restaurant", "pizza", "starbucks"]
  },
  "Transport": {
    "Gas": ["shell", "esso", "petro"],
    "Transit": ["ttc", "presto", "transit"]
  }
}
```


### 5. Google Sheets Sync (`src/sheets.py`)

- Authenticate with service account
- One sheet per account (auto-create if needed)
- Columns: Date | Description | Amount | Balance | Category | Subcategory
- Append-only (prevent duplicates by checking last N rows)
- Auto-create new sheet when rows exceed 10k

### 6. Main Script (`main.py`)

- CLI commands:
  - `python main.py parse <pdf>` - Parse single statement
  - `python main.py parse-all` - Parse all in Statements/
  - `python main.py sync` - Sync DB to Google Sheets
  - `python main.py add-category` - Add new category interactively
  - `python main.py list-categories` - Show all categories

### 7. Simple Documentation (`README.md`)

- Quick setup (5 steps)
- Google API setup (with screenshots)
- Usage examples
- How to add categories
- Troubleshooting (3 common issues)

## Key Files (Minimalist)

- `src/database.py` (~150 lines)
- `src/parser.py` (~100 lines)
- `src/categorizer.py` (~80 lines)
- `src/sheets.py` (~120 lines)
- `main.py` (~80 lines)
- `README.md` (concise, actionable)
- `requirements.txt` (5-6 packages)

## 80/20 Focus

**What matters most:**

1. ✅ Accurate PDF parsing (CIBC format)
2. ✅ Reliable duplicate detection
3. ✅ Flexible category system
4. ✅ Multi-account support
5. ✅ Simple CLI interface

**Skipping for now:**

- File watching (run manually)
- ML categorization (rule-based is fine)
- Complex error handling
- Dashboard creation (user will do later)
- Email integration

## Monthly Maintenance

1. Run `python main.py parse-all` when statements arrive
2. Review "Uncategorized" transactions
3. Add new categories as needed with `add-category`
4. Verify Google Sheets data

### To-dos

- [ ] Set up project structure, venv, dependencies, .gitignore
- [ ] Build SQLite database module with schema for accounts, categories, transactions
- [ ] Analyze CIBC PDF format and build parser to extract transactions and account info
- [ ] Build categorization engine with keyword matching and hierarchical categories
- [ ] Set up Google Cloud project, enable Sheets API, create service account
- [ ] Build Google Sheets sync module with multi-sheet support
- [ ] Create main.py CLI with parse, sync, and category management commands
- [ ] Write concise README with setup, usage, and troubleshooting