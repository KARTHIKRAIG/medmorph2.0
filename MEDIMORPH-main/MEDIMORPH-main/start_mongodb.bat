@echo off
echo ========================================
echo    MEDIMORPH - MongoDB Version
echo ========================================
echo.

echo Checking MongoDB connection...
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Test MongoDB connection first
python -c "from mongodb_config import get_mongodb_client; client = get_mongodb_client(); print('MongoDB connection:', 'SUCCESS' if client else 'FAILED'); client.close() if client else None"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: MongoDB connection failed!
    echo Please ensure MongoDB is running on localhost:27017
    echo.
    echo To start MongoDB:
    echo 1. Install MongoDB Community Server
    echo 2. Start MongoDB service
    echo 3. Or run: mongod --dbpath C:\data\db
    echo.
    pause
    exit /b 1
)

echo.
echo MongoDB connection successful!
echo.

echo Starting MEDIMORPH application...
echo.
echo Access the application at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the application
echo.

REM Start the Flask application
python app.py

pause

