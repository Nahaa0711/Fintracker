@echo off
REM FinTracker Setup and Run Script for Windows

REM Set UTF-8 encoding for Unicode support
chcp 65001 >nul
set PYTHONIOENCODING=utf-8

echo 🚀 Starting FinTracker setup...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python first.
    echo    Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo 📥 Installing requirements...
pip install -r requirements.txt

REM Check if .env file exists, if not copy from example
if not exist ".env" (
    if exist "env.example" (
        echo 📋 Creating .env file from example...
        copy env.example .env
        echo ⚠️  Please edit .env file with your configuration
    ) else (
        echo ⚠️  No .env file found. You may need to create one.
    )
)

echo ✅ Setup complete!
echo.
echo To run the application:
echo   python main.py --help
echo.
echo Common commands:
echo   python main.py parse-all     # Parse all PDFs in Statements/
echo   python main.py stats         # Show database statistics
echo   python main.py init-categories # Initialize default categories

pause
