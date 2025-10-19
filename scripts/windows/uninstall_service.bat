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

echo.
echo ==========================================
echo   Mesh Master Service Uninstalled
echo ==========================================
echo.
echo The service has been removed.
echo Mesh Master will no longer start automatically.
echo.
echo To run manually:
echo   cd \path\to\Mesh-Master
echo   python mesh-master.py
echo.

pause
