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
    echo WARNING: Mesh-Master not found in current directory
    echo.
    echo Would you like to download Mesh-Master to %USERPROFILE%\Mesh-Master?
    echo.
    set /p DOWNLOAD_CHOICE="Download? (Y/n): "

    if /i "%DOWNLOAD_CHOICE%"=="n" (
        echo.
        echo Please clone Mesh-Master manually:
        echo   git clone https://github.com/Snail3D/Mesh-Master.git
        echo   cd Mesh-Master
        echo   scripts\windows\install_service.bat
        pause
        exit /b 1
    )

    REM Check if git is installed
    where git >nul 2>&1
    if %errorLevel% neq 0 (
        echo ERROR: git is not installed
        echo.
        echo Please install Git for Windows from: https://git-scm.com/download/win
        pause
        exit /b 1
    )

    REM Check if directory already exists
    if exist "%USERPROFILE%\Mesh-Master" (
        echo ERROR: %USERPROFILE%\Mesh-Master already exists
        echo Please remove it first or clone manually to a different location
        pause
        exit /b 1
    )

    echo Cloning Mesh-Master repository...
    git clone https://github.com/Snail3D/Mesh-Master.git "%USERPROFILE%\Mesh-Master"

    if %errorLevel% neq 0 (
        echo ERROR: Failed to clone repository
        pause
        exit /b 1
    )

    echo [OK] Downloaded Mesh-Master to %USERPROFILE%\Mesh-Master
    set PROJECT_DIR=%USERPROFILE%\Mesh-Master
    echo.
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

REM Check if service already exists and remove it automatically
nssm status MeshMaster >nul 2>&1
if %errorLevel% equ 0 (
    echo WARNING: Removing existing MeshMaster service...
    nssm stop MeshMaster >nul 2>&1
    nssm remove MeshMaster confirm >nul 2>&1
    echo [OK] Old service removed
    echo.
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

REM Create desktop shortcuts
echo Creating desktop shortcuts...
if exist "%PROJECT_DIR%\scripts\desktop\create_shortcuts.py" (
    "%PYTHON_PATH%" "%PROJECT_DIR%\scripts\desktop\create_shortcuts.py" >nul 2>&1
    if %errorLevel% equ 0 (
        echo [OK] Desktop shortcuts created
    ) else (
        echo [SKIP] Desktop shortcuts skipped ^(optional^)
    )
) else (
    echo [SKIP] Desktop shortcut script not found ^(optional^)
)
echo.

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
    echo Desktop shortcuts created:
    echo   - Start Mesh Master ^(launches dashboard^)
    echo   - Stop Mesh Master ^(stops service^)
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
