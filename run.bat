@echo off
REM Daily runner for the news classifier. Used by Windows Task Scheduler.
REM Adjust the python path if you use a virtual environment.

cd /d "%~dp0"
python run.py >> run.log 2>&1
