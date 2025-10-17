# FinTrack - CIBC Finance Tracker

A Python CLI tool for automatically parsing CIBC bank and credit card statements, categorizing transactions, and syncing to Google Sheets for financial tracking and analysis.

## Features

- 📄 **PDF Statement Parsing**: Automatically extracts transactions from CIBC bank account and credit card PDF statements
- 🏷️ **Smart Categorization**: Intelligent transaction categorization with keyword matching
- 📊 **Google Sheets Integration**: Sync all transactions to Google Sheets for analysis and reporting
- 🗄️ **SQLite Database**: Local storage with duplicate detection
- 🎯 **Hierarchical Categories**: Organized category system with parent/child relationships
- 📈 **Statistics & Analytics**: Built-in stats and uncategorized transaction tracking

## Supported Statement Types

- ✅ CIBC Bank Account Statements
- ✅ CIBC Credit Card Statements (Visa, Dividend, Aventura)
- ✅ Both PDF formats are automatically detected

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd Fintracker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Google Sheets Setup

1. **Create Google Cloud Project**: https://console.cloud.google.com/
   - Click "New Project" → Name it "FinTrack"

2. **Enable Sheets API**:
   - Go to "APIs & Services" → "Library"
   - Search "Google Sheets API" → Click "Enable"

3. **Create Service Account**:
   - Go to "APIs & Services" → "Credentials"
   - "Create Credentials" → "Service Account"
   - Name: "fintrack" → Create → Done

4. **Download Credentials**:
   - Click on the service account → "Keys" tab
   - "Add Key" → "Create New Key" → JSON
   - Save as `credentials.json` in project folder

5. **Create Google Sheet**:
   - Go to sheets.google.com → Create new spreadsheet
   - Name it "FinTrack"
   - Share → Add service account email (from credentials.json) → Editor access
   - Copy spreadsheet ID from URL

### 3. Configuration

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env` with your values:
```env
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here
```

### 4. Initialize & Run

```bash
# Initialize default categories
python main.py init-categories

# Create Statements/ folder and add your PDF statements
mkdir Statements
# Copy your CIBC PDF statements to Statements/ folder

# Parse all statements
python main.py parse-all

# Sync to Google Sheets
python main.py sync

# Check statistics
python main.py stats
```

## Usage

### Commands

```bash
# Parse a single PDF statement
python main.py parse path/to/statement.pdf

# Parse all PDFs in Statements/ folder
python main.py parse-all

# Sync database to Google Sheets
python main.py sync

# Add new category interactively
python main.py add-category

# List all categories
python main.py list-categories

# Show database statistics
python main.py stats

# Initialize default categories
python main.py init-categories
```

### Monthly Workflow

1. Download new CIBC statement PDF to `Statements/` folder
2. Run `python main.py parse-all` to process new statements
3. Run `python main.py sync` to update Google Sheets
4. Review and categorize any uncategorized transactions

## Project Structure

```
Fintracker/
├── main.py                 # Main CLI application
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── src/
│   ├── database.py        # SQLite database operations
│   ├── parser.py          # CIBC PDF statement parser
│   ├── categorizer.py     # Transaction categorization
│   └── sheets.py          # Google Sheets integration
├── Statements/            # Place your PDF statements here
└── fintrack.db           # SQLite database (created automatically)
```

## Database Schema

### Tables

- **accounts**: Bank/credit card account information
- **categories**: Hierarchical transaction categories with keywords
- **transactions**: Individual transactions with categorization

### Key Features

- **Duplicate Detection**: Uses transaction hash to prevent duplicates
- **Hierarchical Categories**: Parent/child category relationships
- **Keyword Matching**: Automatic categorization based on transaction descriptions

## Default Categories

The system comes with pre-configured categories:

- **Food**: Groceries, Dining, Coffee
- **Transportation**: Gas, Transit, Ride Share
- **Shopping**: Retail, Clothing, Electronics
- **Health**: Pharmacy, Medical, Cannabis
- **Education**: Tuition, Books, Supplies
- **Entertainment**: Streaming, Movies, Gaming
- **Utilities**: Internet, Phone, Hydro

## Troubleshooting

### Common Issues

1. **"Google Sheets dependencies not installed"**
   ```bash
   pip install -r requirements.txt
   ```

2. **"Missing Google Sheets configuration"**
   - Check your `.env` file has correct values
   - Ensure `credentials.json` exists and is valid

3. **"Statements/ directory not found"**
   ```bash
   mkdir Statements
   ```

4. **"No PDF files found"**
   - Ensure PDF files are in `Statements/` folder
   - Check PDF files are valid CIBC statements

### PDF Requirements

- Must be CIBC bank account or credit card statements
- PDF format (not scanned images)
- Standard CIBC statement layout

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for personal use. Please ensure compliance with CIBC's terms of service when using this tool.

## Security Note

- Keep your `credentials.json` file secure and never commit it to version control
- The `.env` file contains sensitive information and should not be shared
- All financial data is stored locally in SQLite database

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the QUICKSTART.md for detailed setup
3. Open an issue on GitHub


