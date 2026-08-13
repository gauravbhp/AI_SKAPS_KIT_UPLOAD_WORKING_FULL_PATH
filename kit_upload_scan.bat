@echo off
setlocal

:: Name of your NSSM service
set SERVICE_NAME=GUI_kit_upload_scan_6001
:: URL to check
set SITE_URL=https://192.168.3.48:6001

:loop
    call ".venv\Scripts\activate.bat"
    ".venv\Scripts\python.exe" serve.py

    echo.
    echo Exit Code: %ERRORLEVEL%

    :: Health check
    powershell -Command ^
      "try { (Invoke-WebRequest -Uri '%SITE_URL%' -UseBasicParsing -TimeoutSec 5).StatusCode } catch { 0 }" > status.txt

    set /p STATUS=<status.txt

    if "%STATUS%"=="200" (
        echo Site is reachable (%STATUS%)
    ) else (
        echo Site unreachable, restarting NSSM service...
        nssm restart %SERVICE_NAME%
        timeout /t 10
    )

    :: Wait before next check
    timeout /t 30
goto loop
