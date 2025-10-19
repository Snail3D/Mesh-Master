@echo off
REM Mesh Master Windows Service Uninstallation Script

echo.
echo ==========================================
echo   Mesh Master Windows Service Uninstaller
echo ==========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script must be run as Administrator
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

REM Check if NSSM is installed
where nssm >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: NSSM not found
    pause
    exit /b 1
)

REM Check if service exists
nssm status MeshMaster >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: MeshMaster service is not installed
    pause
    exit /b 0
)

echo Found MeshMaster service
echo.

REM Confirm uninstallation
set /p CONFIRM="Are you sure you want to uninstall? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo Uninstallation cancelled.
    pause
    exit /b 0
)

echo.
echo Stopping service...
nssm stop MeshMaster

echo Removing service...
nssm remove MeshMaster confirm

REM Remove desktop shortcuts
echo Removing desktop shortcuts...
set DESKTOP=%USERPROFILE%\Desktop
set removed_count=0

if exist "%DESKTOP%\Start Mesh Master.lnk" (
    del "%DESKTOP%\Start Mesh Master.lnk"
    set /a removed_count+=1
)

if exist "%DESKTOP%\Stop Mesh Master.lnk" (
    del "%DESKTOP%\Stop Mesh Master.lnk"
    set /a removed_count+=1
)

if %removed_count% gtr 0 (
    echo [OK] Removed %removed_count% desktop shortcut^(s^)
) else (
    echo [SKIP] No desktop shortcuts found
)

echo.
echo ==========================================
echo   Mesh Master Service Uninstalled
echo ==========================================
echo.
echo The service has been removed:
echo   - Service stopped and disabled
echo   - Auto-start on boot disabled
echo   - Desktop shortcuts removed
echo.
echo Your data and config files are preserved.
echo.
echo To run manually:
echo   cd \path\to\Mesh-Master
echo   python mesh-master.py
echo.

pause
