@echo off
title AlphaPulse GO::OS Institutional Terminal
color 0A

echo ====================================================================
echo  [AlphaPulse GO::OS] Institutional Quantitative Trading Terminal
echo ====================================================================
echo.

cd /d "%~dp0"

:: 1. Check if port 8000 is stuck from a previous session and free it cleanly
echo [*] Checking network port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo [*] Freeing port 8000 from previous background process (PID %%a)...
    taskkill /f /pid %%a >nul 2>&1
)

:: 2. Launch browser automatically in background after 2 seconds
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:8000"

:: 3. Launch Python Quantitative Server
echo [*] Starting Quant Engine and Gemini 3.6 Intelligence...
echo [*] Local Terminal URL:   http://localhost:8000
echo [*] Mobile / Phone URL:   http://10.0.0.42:8000
echo.
echo ====================================================================
echo  Press CTRL+C in this window anytime to stop the server.
echo ====================================================================
echo.

python backend/run.py

if errorlevel 1 (
    echo.
    echo [ERROR] The server encountered an issue. Please check the error above.
    pause
)
