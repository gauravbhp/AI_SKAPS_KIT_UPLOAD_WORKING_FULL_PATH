@echo off

cd /d "E:\kit_upload"

call ".venv\Scripts\activate.bat"

:restart

echo Starting Django Server...

".venv\Scripts\python.exe" manage.py runserver_plus --cert-file cert.pem --key-file key.pem 192.168.3.48:6001

echo Server crashed or stopped. Restarting in 5 seconds...

timeout /t 5 /nobreak >nul

goto restart