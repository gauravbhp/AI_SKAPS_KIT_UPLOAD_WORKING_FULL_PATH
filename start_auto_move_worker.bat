@echo off
cd /d E:\tested\kit_upload

call .venv\Scripts\activate.bat

python auto_move_worker.py

pause
