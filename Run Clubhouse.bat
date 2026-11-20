@echo off
rem Starts Clubhouse. First time only: py -3.13 -m venv .venv  then  .venv\Scripts\pip install -r requirements.txt
cd /d "%~dp0"
start "" ".venv\Scripts\pythonw.exe" app\clubhouse.py %*
