#!/usr/bin/env python3
"""
Mesh Master Desktop Shortcut Creator
Creates branded start/stop shortcuts for Windows, macOS, and Linux
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def get_project_dir():
    """Get the Mesh Master project directory"""
    # This script is in scripts/desktop/, so go up two levels
    return Path(__file__).parent.parent.parent.absolute()

def get_desktop_dir():
    """Get user's desktop directory cross-platform"""
    system = platform.system()

    if system == "Windows":
        return Path.home() / "Desktop"
    elif system == "Darwin":  # macOS
        return Path.home() / "Desktop"
    else:  # Linux/Unix
        # Try XDG standard first
        xdg_desktop = os.environ.get("XDG_DESKTOP_DIR")
        if xdg_desktop:
            return Path(xdg_desktop)
        return Path.home() / "Desktop"

def create_start_script():
    """Create the start script that kills old instances and opens browser"""
    project_dir = get_project_dir()
    system = platform.system()

    if system == "Windows":
        script_path = project_dir / "start-mesh-master.bat"
        content = f"""@echo off
REM Mesh Master Start Script - Windows
echo ========================================
echo   Starting Mesh Master
echo ========================================
echo.

REM Kill any existing instances
echo Checking for old instances...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq mesh-master*" 2>nul
taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq mesh-master*" 2>nul

REM Kill zombies by checking for mesh-master.py processes
for /f "tokens=2" %%i in ('tasklist ^| findstr /i "python.*mesh-master"') do taskkill /F /PID %%i 2>nul

echo Starting Mesh Master...
cd /d "{project_dir}"

REM Activate virtual environment if it exists
if exist .venv\\Scripts\\activate.bat (
    call .venv\\Scripts\\activate.bat
)

REM Start Mesh Master in background
start /B pythonw mesh-master.py

REM Wait a few seconds for server to start
timeout /t 5 /nobreak >nul

REM Open browser
echo Opening dashboard...
start http://localhost:5001/dashboard

echo.
echo ========================================
echo   Mesh Master Started!
echo   Dashboard: http://localhost:5001
echo ========================================
echo.
pause
"""
    else:  # macOS and Linux
        script_path = project_dir / "start-mesh-master.sh"
        content = f"""#!/bin/bash
# Mesh Master Start Script - Unix/macOS

echo "========================================"
echo "  Starting Mesh Master"
echo "========================================"
echo ""

# Kill any existing instances
echo "Checking for old instances..."
pkill -f "python.*mesh-master.py" 2>/dev/null || true
pkill -f "mesh-master.py" 2>/dev/null || true

# Kill zombies
ps aux | grep "[m]esh-master.py" | awk '{{print $2}}' | xargs kill -9 2>/dev/null || true

# Change to project directory
cd "{project_dir}"

# Activate virtual environment if it exists
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
fi

# Start Mesh Master in background
echo "Starting Mesh Master..."
nohup python3 mesh-master.py > /dev/null 2>&1 &

# Wait for server to start
sleep 5

# Open browser (platform-specific)
echo "Opening dashboard..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open http://localhost:5001/dashboard
else
    # Linux
    xdg-open http://localhost:5001/dashboard 2>/dev/null || \
    sensible-browser http://localhost:5001/dashboard 2>/dev/null || \
    x-www-browser http://localhost:5001/dashboard 2>/dev/null || \
    echo "Please open http://localhost:5001/dashboard in your browser"
fi

echo ""
echo "========================================"
echo "  Mesh Master Started!"
echo "  Dashboard: http://localhost:5001"
echo "========================================"
"""

    # Write script
    with open(script_path, 'w', newline='' if system == "Windows" else None) as f:
        f.write(content)

    # Make executable on Unix systems
    if system != "Windows":
        os.chmod(script_path, 0o755)

    return script_path

def create_stop_script():
    """Create the stop script that kills all instances"""
    project_dir = get_project_dir()
    system = platform.system()

    if system == "Windows":
        script_path = project_dir / "stop-mesh-master.bat"
        content = """@echo off
REM Mesh Master Stop Script - Windows
echo ========================================
echo   Stopping Mesh Master
echo ========================================
echo.

REM Kill all Python instances running mesh-master
taskkill /F /IM python.exe /FI "WINDOWTITLE eq mesh-master*"
taskkill /F /IM pythonw.exe /FI "WINDOWTITLE eq mesh-master*"

REM Kill by process name
for /f "tokens=2" %%i in ('tasklist ^| findstr /i "python.*mesh-master"') do taskkill /F /PID %%i

echo.
echo ========================================
echo   Mesh Master Stopped
echo ========================================
echo.
pause
"""
    else:  # macOS and Linux
        script_path = project_dir / "stop-mesh-master.sh"
        content = """#!/bin/bash
# Mesh Master Stop Script - Unix/macOS

echo "========================================"
echo "  Stopping Mesh Master"
echo "========================================"
echo ""

# Kill all instances
pkill -f "python.*mesh-master.py"
pkill -f "mesh-master.py"

# Kill zombies forcefully
ps aux | grep "[m]esh-master.py" | awk '{print $2}' | xargs kill -9 2>/dev/null || true

# Also kill any Flask processes on port 5001
lsof -ti:5001 | xargs kill -9 2>/dev/null || true

echo ""
echo "========================================"
echo "  Mesh Master Stopped"
echo "========================================"
"""

    # Write script
    with open(script_path, 'w', newline='' if system == "Windows" else None) as f:
        f.write(content)

    # Make executable on Unix systems
    if system != "Windows":
        os.chmod(script_path, 0o755)

    return script_path

def create_windows_shortcut(script_path, name, icon_path):
    """Create Windows .lnk shortcut"""
    desktop = get_desktop_dir()
    shortcut_path = desktop / f"{name}.lnk"

    # Use PowerShell to create shortcut
    ps_command = f"""
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut('{shortcut_path}')
$Shortcut.TargetPath = '{script_path}'
$Shortcut.WorkingDirectory = '{script_path.parent}'
$Shortcut.IconLocation = '{icon_path}'
$Shortcut.Save()
"""

    subprocess.run(["powershell", "-Command", ps_command], check=True)
    return shortcut_path

def create_macos_app(script_path, name, icon_path):
    """Create macOS .app bundle"""
    desktop = get_desktop_dir()
    app_path = desktop / f"{name}.app"

    # Create .app bundle structure
    contents = app_path / "Contents"
    macos = contents / "MacOS"
    resources = contents / "Resources"

    macos.mkdir(parents=True, exist_ok=True)
    resources.mkdir(parents=True, exist_ok=True)

    # Copy icon if it's an .icns file
    if icon_path and Path(icon_path).suffix == '.icns':
        import shutil
        shutil.copy(icon_path, resources / "AppIcon.icns")

    # Create Info.plist
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launch</string>
    <key>CFBundleName</key>
    <string>{name}</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
</dict>
</plist>
"""

    with open(contents / "Info.plist", 'w') as f:
        f.write(plist_content)

    # Create launch script
    launch_script = macos / "launch"
    with open(launch_script, 'w') as f:
        f.write(f"""#!/bin/bash
cd "{script_path.parent}"
{script_path}
""")

    os.chmod(launch_script, 0o755)

    return app_path

def create_linux_desktop_entry(script_path, name, icon_path, comment):
    """Create Linux .desktop file"""
    desktop = get_desktop_dir()
    desktop_file = desktop / f"{name}.desktop"

    content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={name}
Comment={comment}
Exec={script_path}
Icon={icon_path}
Terminal=false
Categories=Network;Utility;
"""

    with open(desktop_file, 'w') as f:
        f.write(content)

    # Make executable
    os.chmod(desktop_file, 0o755)

    return desktop_file

def create_desktop_shortcuts():
    """Main function to create all shortcuts"""
    system = platform.system()
    project_dir = get_project_dir()

    print(f"Creating Mesh Master desktop shortcuts for {system}...")
    print(f"Project directory: {project_dir}")

    # Create scripts
    start_script = create_start_script()
    stop_script = create_stop_script()

    print(f"✓ Created start script: {start_script}")
    print(f"✓ Created stop script: {stop_script}")

    # Icon paths
    svg_icon = str(project_dir / "static" / "mesh-master-icon.svg")

    try:
        if system == "Windows":
            # Try ICO first, fall back to SVG (Windows 10+ supports SVG in some contexts)
            ico_path = project_dir / "static" / "mesh-master-icon.ico"
            icon_file = str(ico_path) if ico_path.exists() else svg_icon
            create_windows_shortcut(start_script, "Start Mesh Master", icon_file)
            create_windows_shortcut(stop_script, "Stop Mesh Master", icon_file)
            print("✓ Created Windows shortcuts on Desktop")
            if not ico_path.exists():
                print("  ℹ️  Using SVG icon (for best results, generate .ico file)")

        elif system == "Darwin":  # macOS
            # Try ICNS first, fall back to SVG
            icns_path = project_dir / "static" / "mesh-master-icon.icns"
            icon_file = str(icns_path) if icns_path.exists() else svg_icon
            create_macos_app(start_script, "Start Mesh Master", icon_file)
            create_macos_app(stop_script, "Stop Mesh Master", icon_file)
            print("✓ Created macOS apps on Desktop")
            if not icns_path.exists():
                print("  ℹ️  Using SVG icon (for best results, generate .icns file)")

        else:  # Linux
            # Linux desktop entries support SVG natively
            create_linux_desktop_entry(
                start_script,
                "Start Mesh Master",
                svg_icon,
                "Start Mesh Master and open dashboard"
            )
            create_linux_desktop_entry(
                stop_script,
                "Stop Mesh Master",
                svg_icon,
                "Stop all Mesh Master instances"
            )
            print("✓ Created Linux desktop entries")
            print("  ✓ Using SVG icon (native Linux support)")

        print("")
        print("========================================")
        print("  Desktop Shortcuts Created!")
        print("========================================")
        print("")
        print("Look for these on your desktop:")
        print("  • Start Mesh Master")
        print("  • Stop Mesh Master")
        print("")

        return True

    except Exception as e:
        print(f"✗ Error creating shortcuts: {e}")
        return False

if __name__ == "__main__":
    success = create_desktop_shortcuts()
    sys.exit(0 if success else 1)
