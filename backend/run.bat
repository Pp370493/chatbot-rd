@echo off
title VAT RAG Backend Server
echo ===================================================
echo [VAT RAG Chatbot Backend] Starting local FastAPI...
echo ===================================================
echo.
cd %~dp0
echo Installing Python dependencies from requirements.txt...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies. Please ensure Python is on your system PATH.
    pause
    exit /b %errorlevel%
)
echo.
echo Starting FastAPI application using Uvicorn on http://127.0.0.1:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
