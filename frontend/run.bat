@echo off
title VAT RAG Frontend Server
echo ====================================================
echo [VAT RAG Chatbot Frontend] Starting local Next.js...
echo ====================================================
echo.
cd %~dp0
echo Installing frontend dependencies from package.json...
call npm install
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install npm packages. Please make sure Node.js (npm) is installed.
    pause
    exit /b %errorlevel%
)
echo.
echo Starting Next.js Dev Server on http://localhost:3000
call npm run dev
pause
