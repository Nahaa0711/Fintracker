# Quick Start Guide

Get up and running in 5 minutes!

## 1. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Google Sheets Setup (5 minutes)

1. **Create Google Cloud Project**: https://console.cloud.google.com/
   - Click "New Project"
   - Name it "FinTrack"

2. **Enable Sheets API**:
   - Go to "APIs & Services" → "Library"
   - Search "Google Sheets API"
   - Click "Enable"

3. **Create Service Account**:
   - Go to "APIs & Services" → "Credentials"
   - "Create Credentials" → "Service Account"
   - Name: "fintrack" → Create
   - Click "Done" (skip optional steps)

4. **Download Credentials**:
   - Click on the service account you just created
   - "Keys" tab → "Add Key" → "Create New Key"
   - Select JSON → Create
   - Rename downloaded file to `credentials.json`
   - Move it to FinTrack folder

5. **Create Google Sheet**:
   - Go to sheets.google.com
   - Create new spreadsheet
   - Name it "FinTrack"
   - Click Share → paste service account email (from credentials.json)
   - Give it "Editor" access
   - Copy spreadsheet ID from URL

## 3. Configure

Create `.env` file:
```bash
echo "GOOGLE_CREDENTIALS_FILE=credentials.json" > .env
echo "GOOGLE_SPREADSHEET_ID=YOUR_SPREADSHEET_ID_HERE" >> .env
```

Replace `YOUR_SPREADSHEET_ID_HERE` with your actual ID!

## 4. Run

```bash
# Initialize default categories
python main.py init-categories

# Parse statements
python main.py parse-all

# Sync to Google Sheets
python main.py sync

# Check stats
python main.py stats
```

Done! Check your Google Sheet to see your transactions.

## Monthly Workflow

```bash
# Download new CIBC statement to Statements/ folder
python main.py parse-all  # Parse new statement
python main.py sync       # Upload to Sheets
```

That's it! 🎉




