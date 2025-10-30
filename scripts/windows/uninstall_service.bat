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

REM Kill any running Mesh Master processes
echo Stopping any running Mesh Master processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *mesh-master*" >nul 2>&1
taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq *mesh-master*" >nul 2>&1
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /NH ^| findstr /C:"mesh-master"') do taskkill /F /PID %%a >nul 2>&1
timeout /t 1 /nobreak >nul
echo [OK] Processes stopped

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

REM Also remove the launcher shortcut created by setup.sh
if exist "%DESKTOP%\Mesh Master.lnk" (
    del "%DESKTOP%\Mesh Master.lnk"
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
echo   - All processes stopped
echo.

REM Handle directory deletion
REM Get Mesh-Master directory (passed as argument or detect)
set MESH_DIR=%~1
if not defined MESH_DIR (
    REM Try to detect from script location
    set MESH_DIR=%~dp0..\..
)

REM Resolve to absolute path
pushd "%MESH_DIR%" 2>nul
if %errorLevel% equ 0 (
    set MESH_DIR=%CD%
    popd
) else (
    echo ERROR: Could not detect Mesh Master directory
    echo.
    echo To manually remove Mesh Master:
    echo   cd C:\path\to\Mesh-Master\.. ^&^& rmdir /S /Q Mesh-Master
    pause
    exit /b 1
)

REM CRITICAL SAFETY CHECK: Prevent deletion of system directories
REM Check if MESH_DIR is empty or a system directory
if "%MESH_DIR%"=="" (
    echo ERROR: Could not safely detect Mesh Master directory
    echo Detected path is empty
    echo.
    echo To manually remove Mesh Master:
    echo   cd C:\path\to\Mesh-Master\.. ^&^& rmdir /S /Q Mesh-Master
    pause
    exit /b 1
)

REM Check for common system directories
echo %MESH_DIR% | findstr /I /C:"C:\" >nul && (
    if "%MESH_DIR%"=="C:\" (
        echo ERROR: Refusing to delete C:\
        pause
        exit /b 1
    )
)
echo %MESH_DIR% | findstr /I /C:"C:\Windows" >nul && (
    echo ERROR: Refusing to delete Windows directory
    pause
    exit /b 1
)
echo %MESH_DIR% | findstr /I /C:"C:\Program Files" >nul && (
    echo ERROR: Refusing to delete Program Files
    pause
    exit /b 1
)
echo %MESH_DIR% | findstr /I /C:"C:\Users" >nul && (
    if "%MESH_DIR%"=="C:\Users" (
        echo ERROR: Refusing to delete Users directory
        pause
        exit /b 1
    )
)

REM Additional safety: Check if directory name contains "Mesh-Master" or "mesh-master"
echo %MESH_DIR% | findstr /I /C:"Mesh-Master" >nul
if %errorLevel% neq 0 (
    echo ERROR: Directory path doesn't look like Mesh Master
    echo Detected path: %MESH_DIR%
    echo.
    echo For safety, refusing to delete. To manually remove:
    echo   rmdir /S /Q "%MESH_DIR%"
    pause
    exit /b 1
)

REM Check if AUTO_DELETE is set (from dashboard)
if "%AUTO_DELETE%"=="true" (
    echo Auto-deleting Mesh Master directory...
    cd /d "%USERPROFILE%"
    timeout /t 2 /nobreak >nul
    rmdir /S /Q "%MESH_DIR%" 2>nul
    if not exist "%MESH_DIR%" (
        echo [OK] Mesh Master directory deleted: %MESH_DIR%
        echo.
        echo Mesh Master has been completely removed!
    ) else (
        echo [ERROR] Failed to delete directory
        echo Please run manually: rmdir /S /Q "%MESH_DIR%"
    )
) else (
    REM Interactive mode - ask user
    echo.
    echo DIRECTORY DELETION IN PROGRESS
    echo.
    echo The Mesh Master directory will be DELETED:
    echo   %MESH_DIR%
    echo.
    echo This includes:
    echo   - config.json (your settings and passwords)
    echo   - data\ (logs, reports, mail, saved contexts)
    echo   - All source code
    echo.
    echo Deleting in 5 seconds... Press Ctrl+C to cancel!
    echo.
    timeout /t 5 /nobreak
    echo.
    echo Deleting Mesh Master directory...
    cd /d "%USERPROFILE%"
    rmdir /S /Q "%MESH_DIR%" 2>nul
    if not exist "%MESH_DIR%" (
        echo [OK] Mesh Master directory deleted: %MESH_DIR%
        echo.
        echo Mesh Master has been completely removed!
    ) else (
        echo [ERROR] Failed to delete directory
        echo Please run manually: rmdir /S /Q "%MESH_DIR%"
    )
)

echo.
pause
