@echo off
echo Starting RAG Frontend...
echo.

REM Check if node_modules exists
if not exist "node_modules\" (
    echo Installing dependencies...
    call npm install
)

REM Check if .env.local exists
if not exist ".env.local" (
    echo Copying .env.local.example to .env.local
    copy .env.local.example .env.local
)

echo.
echo Starting Next.js development server...
echo Frontend will be available at http://localhost:3000
echo.
call npm run dev

pause

