@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Archive Checker - Build EXE

echo ===========================================
echo       ARCHIVE CHECKER - BUILD EXE
echo ===========================================
if not exist "archive_checker.py" (
  echo ERROR: archive_checker.py not found.
  goto :failed
)
if not exist "config.json" (
  echo ERROR: config.json not found.
  goto :failed
)
where py >nul 2>&1
if not errorlevel 1 (
  set "PYTHON=py -3"
) else (
  where python >nul 2>&1
  if errorlevel 1 (
    echo ERROR: Python 3 is not installed.
    goto :failed
  )
  set "PYTHON=python"
)
%PYTHON% --version
if errorlevel 1 goto :failed
%PYTHON% -m pip install --upgrade pyinstaller
if errorlevel 1 goto :failed

echo Removing previous build files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "ArchiveChecker.spec" del /q "ArchiveChecker.spec"

echo Building fresh one-file executable...
%PYTHON% -m PyInstaller --noconfirm --clean --onefile --console --name ArchiveChecker archive_checker.py
if errorlevel 1 goto :failed
if not exist "dist\ArchiveChecker.exe" goto :failed
copy /Y "config.json" "dist\config.json" >nul
if errorlevel 1 goto :failed
copy /Y "run_checker_exe.bat" "dist\run_checker_exe.bat" >nul
if errorlevel 1 goto :failed

echo.
echo BUILD SUCCESSFUL: %~dp0dist\ArchiveChecker.exe
echo Keep config.json next to ArchiveChecker.exe.
echo Install 7-Zip on the target Windows machine.
pause
exit /b 0
:failed
echo.
echo BUILD FAILED. Review errors above.
pause
exit /b 1
