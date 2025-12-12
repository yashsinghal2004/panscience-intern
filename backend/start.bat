@echo off
echo Starting RAG Backend Server...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Copying .env.example to .env
    copy .env.example .env
    echo.
    echo Please edit .env and add your OPENAI_API_KEY
    echo Press any key to continue after editing .env...
    pause > nul
)

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting server...
echo Backend will be available at http://localhost:8000
echo API docs at http://localhost:8000/docs
echo.
python -m app.main

pause

