@echo off
echo ================================================
echo Healthcare Assistant - Starting Application
echo ================================================
echo.

echo [1/2] Starting FastAPI Backend...
echo Backend will run at: http://localhost:8000
echo.
start cmd /k "cd /d %~dp0 && uvicorn app.main:app"

timeout /t 3 /nobreak > nul

echo [2/2] Opening Frontend...
echo.
start "" "%~dp0frontend\index.html"

echo ================================================
echo Application Started!
echo ================================================
echo.
echo Backend: http://localhost:8000
echo Frontend: Opened in your browser
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to close this window...
pause > nul



