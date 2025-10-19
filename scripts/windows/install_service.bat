@echo off
REM Mesh Master Windows Service Installation Script
REM Requires NSSM (Non-Sucking Service Manager)

echo.
echo ==========================================
echo   Mesh Master Windows Service Installer
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

REM Get script directory
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..\..

echo Project directory: %PROJECT_DIR%
echo.

REM Verify we're in the Mesh Master project directory
if not exist "%PROJECT_DIR%\mesh-master.py" (
    echo ERROR: mesh-master.py not found!
    echo.
    echo This script must be run from the Mesh Master project directory.
    echo.
    echo Please navigate to your Mesh-Master folder and try again:
    echo   cd C:\path\to\Mesh-Master
    echo   scripts\windows\install_service.bat
    echo.
    echo Or right-click the script and "Run as administrator"
    echo from within the Mesh-Master folder.
    pause
    exit /b 1
)

REM Additional verification - check for key files
if not exist "%PROJECT_DIR%\config.json" (
    if not exist "%PROJECT_DIR%\config.json.example" (
        echo ERROR: This doesn't look like a Mesh Master directory
        echo.
        echo Expected to find config.json or config.json.example
        echo Current directory: %PROJECT_DIR%
        echo.
        echo Please make sure you're in the Mesh-Master project folder.
        pause
        exit /b 1
    )
)

echo [OK] Found Mesh Master installation
echo.

REM Check if NSSM is installed
where nssm >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: NSSM not found
    echo.
    echo Please install NSSM first:
    echo   1. Download from: https://nssm.cc/download
    echo   2. Extract nssm.exe to C:\Windows\System32
    echo   OR install via chocolatey: choco install nssm
    pause
    exit /b 1
)

REM Find Python
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3 and add it to PATH
    pause
    exit /b 1
)

for /f "delims=" %%i in ('where python') do set PYTHON_PATH=%%i
echo Using Python: %PYTHON_PATH%
echo.

REM Check if virtual environment exists
if exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    echo Virtual environment detected
    set PYTHON_PATH=%PROJECT_DIR%\.venv\Scripts\python.exe
    echo Using venv Python: %PYTHON_PATH%
)

REM Check if service already exists
nssm status MeshMaster >nul 2>&1
if %errorLevel% equ 0 (
    echo WARNING: MeshMaster service already exists
    echo.
    set /p REINSTALL="Do you want to reinstall? (y/N): "
    if /i not "%REINSTALL%"=="y" (
        echo Installation cancelled.
        pause
        exit /b 0
    )
    echo Removing existing service...
    nssm stop MeshMaster
    nssm remove MeshMaster confirm
)

echo Installing MeshMaster service...

REM Install the service
nssm install MeshMaster "%PYTHON_PATH%" "%PROJECT_DIR%\mesh-master.py"

REM Configure service
nssm set MeshMaster AppDirectory "%PROJECT_DIR%"
nssm set MeshMaster DisplayName "Mesh Master"
nssm set MeshMaster Description "Off-Grid AI Operations Suite for Meshtastic"
nssm set MeshMaster Start SERVICE_AUTO_START

REM Configure restart on failure
nssm set MeshMaster AppExit Default Restart
nssm set MeshMaster AppRestartDelay 2000

REM Configure logging
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"
nssm set MeshMaster AppStdout "%PROJECT_DIR%\logs\mesh-master-stdout.log"
nssm set MeshMaster AppStderr "%PROJECT_DIR%\logs\mesh-master-stderr.log"

REM Start the service
echo Starting MeshMaster service...
nssm start MeshMaster

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Check if running
nssm status MeshMaster | find "SERVICE_RUNNING" >nul
if %errorLevel% equ 0 (
    echo.
    echo ==========================================
    echo   Mesh Master Service Installed!
    echo ==========================================
    echo.
    echo The service is now running and will:
    echo   - Start automatically on boot
    echo   - Restart automatically if it crashes
    echo   - Restart automatically after /update
    echo.
    echo Useful commands:
    echo   Check status:  nssm status MeshMaster
    echo   View logs:     type "%PROJECT_DIR%\logs\mesh-master-stdout.log"
    echo   Stop service:  nssm stop MeshMaster
    echo   Start service: nssm start MeshMaster
    echo   Restart:       nssm restart MeshMaster
    echo   Uninstall:     scripts\windows\uninstall_service.bat
    echo.
    echo Dashboard: http://localhost:5001/dashboard
    echo.
) else (
    echo.
    echo ERROR: Service failed to start
    echo Check logs at: %PROJECT_DIR%\logs\mesh-master-stderr.log
    pause
    exit /b 1
)

pause
