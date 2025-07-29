@echo off
echo ============================================================
echo   SSH AUTOMATION DATABASE SETUP
echo ============================================================
echo.

echo 📦 Installing required Python packages...
pip install mysql-connector-python python-dotenv cryptography

echo.
echo 🔧 Setting up database configuration...
if not exist "database\.env" (
    copy "database\.env.example" "database\.env"
    echo ✅ Created database\.env from example
    echo ⚠️  Please edit database\.env with your MySQL credentials
    echo.
) else (
    echo ✅ Database configuration file already exists
)

echo 🚀 Running database initialization...
python setup_database.py

echo.
echo ============================================================
echo   DATABASE SETUP COMPLETED
echo ============================================================
echo.
echo Next steps:
echo 1. Edit database\.env with your MySQL credentials
echo 2. Run: python setup_database.py
echo 3. Start the web interface: python web_gui\app.py
echo.
pause
