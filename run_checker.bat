@echo off
cd /d "%~dp0"
py -3 archive_checker.py --config config.json
if errorlevel 1 (
  echo Some files or folders need attention. See the report folder.
) else (
  echo All accessible archives passed the integrity test.
)
pause
