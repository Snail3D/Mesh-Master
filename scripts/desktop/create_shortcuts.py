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
        script_path = project_dir / "mesh-master.bat"
        content = f"""@echo off
REM Mesh Master Launcher - Windows
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

REM Activate virtual environment and start
if exist .venv\\Scripts\\python.exe (
    set PYTHON_EXEC=.venv\\Scripts\\python.exe
) else (
    set PYTHON_EXEC=python
)

REM Set PYTHONPATH
set PYTHONPATH={project_dir};{project_dir}\\scripts\\utilities;%PYTHONPATH%

REM Start Mesh Master in background
start /B %PYTHON_EXEC% mesh-master.py

REM Wait a few seconds for server to start
timeout /t 5 /nobreak >nul

REM Open browser to login page
echo Opening dashboard...
start http://localhost:5001/login

echo.
echo ========================================
echo   Mesh Master Started!
echo   Dashboard: http://localhost:5001
echo ========================================
echo.
pause
"""
    else:  # macOS and Linux
        script_path = project_dir / "mesh-master.sh"
        content = f"""#!/bin/bash
# Mesh Master Launcher - Unix/macOS

echo "========================================"
echo "  Starting Mesh Master"
echo "========================================"
echo ""

# Kill any existing instances
echo "Checking for old instances..."
pkill -f "python.*mesh-master\\.py" 2>/dev/null || true
pkill -f "mesh-master\\.py" 2>/dev/null || true

# Kill zombies
ps aux | grep "[m]esh-master.py" | awk '{{print $2}}' | xargs kill -9 2>/dev/null || true

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"

# Change to project directory
cd "$SCRIPT_DIR"

# Set PYTHONPATH for project root and utilities
export PYTHONPATH="$SCRIPT_DIR:$SCRIPT_DIR/scripts/utilities:${{PYTHONPATH:-}}"

# Activate virtualenv if present
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
elif [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Read port from config.json (default 5001)
PORT=5001
if [ -f "$SCRIPT_DIR/config.json" ]; then
    cfg_port=$(python3 -c "import json; d=json.load(open('config.json')); print(d.get('web_port') or d.get('flask_port') or d.get('port') or 5001)" 2>/dev/null || echo "5001")
    if [ -n "$cfg_port" ] && [ "$cfg_port" != "None" ]; then
        PORT="$cfg_port"
    fi
fi

# Start Mesh Master in background
echo "Starting Mesh Master..."
nohup python "$SCRIPT_DIR/mesh-master.py" >> "$SCRIPT_DIR/mesh-master.log" 2>&1 &

# Wait for the web server to come up (max 30 seconds)
echo "Waiting for server..."
for i in $(seq 1 30); do
    if curl -s -o /dev/null -w "%{{http_code}}" "http://localhost:$PORT/login" 2>/dev/null | grep -q "200"; then
        break
    fi
    sleep 1
done

# Open browser (platform-specific)
echo "Opening dashboard..."
DASHBOARD_URL="http://localhost:$PORT/login"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$DASHBOARD_URL"
else
    # Linux
    xdg-open "$DASHBOARD_URL" 2>/dev/null || \
    sensible-browser "$DASHBOARD_URL" 2>/dev/null || \
    x-www-browser "$DASHBOARD_URL" 2>/dev/null || \
    echo "Please open $DASHBOARD_URL in your browser"
fi

echo ""
echo "========================================"
echo "  Mesh Master Started!"
echo "  Dashboard: http://localhost:$PORT"
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
    project_dir = get_project_dir()
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
    <key>CFBundleIdentifier</key>
    <string>com.meshmaster.app</string>
    <key>CFBundleVersion</key>
    <string>2.5</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
</dict>
</plist>
"""

    with open(contents / "Info.plist", 'w') as f:
        f.write(plist_content)

    # Read port from config if available
    config_path = project_dir / "config.json"
    port = 5001
    if config_path.exists():
        try:
            import json
            with open(config_path) as cf:
                cfg = json.load(cf)
            port = cfg.get("web_port") or cfg.get("flask_port") or cfg.get("port") or 5001
        except Exception:
            pass

    # Create self-contained launch script for the .app bundle
    launch_script = macos / "launch"
    with open(launch_script, 'w') as f:
        f.write(f"""#!/bin/bash
# Mesh Master .app Launcher
PROJECT_DIR="{project_dir}"

cd "$PROJECT_DIR"

# Read port from config.json (default {port})
PORT={port}
if [ -f "$PROJECT_DIR/config.json" ]; then
    cfg_port=$(python3 -c "import json; d=json.load(open('config.json')); print(d.get('web_port') or d.get('flask_port') or d.get('port') or {port})" 2>/dev/null || echo "{port}")
    if [ -n "$cfg_port" ] && [ "$cfg_port" != "None" ]; then
        PORT="$cfg_port"
    fi
fi
DASHBOARD_URL="http://localhost:$PORT/login"

# Kill any existing Mesh Master process
pkill -f "python.*mesh-master\\.py" 2>/dev/null
sleep 1

# Activate virtualenv
if [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    source "$PROJECT_DIR/.venv/bin/activate"
elif [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

# Set PYTHONPATH so mesh_master package imports work
export PYTHONPATH="$PROJECT_DIR:$PROJECT_DIR/scripts/utilities:${{PYTHONPATH:-}}"

# Start Mesh Master in background
python "$PROJECT_DIR/mesh-master.py" >> "$PROJECT_DIR/mesh-master.log" 2>&1 &
MESH_PID=$!

# Wait for the web server to come up (max 30 seconds)
for i in $(seq 1 30); do
    if curl -s -o /dev/null -w "%{{http_code}}" "http://localhost:$PORT/login" 2>/dev/null | grep -q "200"; then
        break
    fi
    sleep 1
done

# Open the dashboard in the default browser
open "$DASHBOARD_URL"

# Keep the script running so the app stays alive
wait $MESH_PID
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
    """Main function to create single Mesh Master shortcut"""
    system = platform.system()
    project_dir = get_project_dir()

    print(f"Creating Mesh Master desktop shortcut for {system}...")
    print(f"Project directory: {project_dir}")

    # Create single start script (kills old instances automatically)
    start_script = create_start_script()

    print(f"✓ Created launcher script: {start_script}")

    # Icon paths
    svg_icon = str(project_dir / "static" / "mesh-master-icon.svg")

    try:
        if system == "Windows":
            # Try ICO first, fall back to SVG (Windows 10+ supports SVG in some contexts)
            ico_path = project_dir / "static" / "mesh-master-icon.ico"
            icon_file = str(ico_path) if ico_path.exists() else svg_icon
            create_windows_shortcut(start_script, "Mesh Master", icon_file)
            print("✓ Created Windows shortcut on Desktop")
            if not ico_path.exists():
                print("  ℹ️  Using SVG icon (for best results, generate .ico file)")

        elif system == "Darwin":  # macOS
            # Try ICNS first, fall back to SVG
            icns_path = project_dir / "static" / "mesh-master-icon.icns"
            icon_file = str(icns_path) if icns_path.exists() else svg_icon
            create_macos_app(start_script, "Mesh Master", icon_file)
            print("✓ Created macOS app on Desktop")
            if not icns_path.exists():
                print("  ℹ️  Using SVG icon (for best results, generate .icns file)")

        else:  # Linux
            # Linux desktop entries support SVG natively
            create_linux_desktop_entry(
                start_script,
                "Mesh Master",
                svg_icon,
                "Kill old instances and restart Mesh Master with dashboard"
            )
            print("✓ Created Linux desktop entry")
            print("  ✓ Using SVG icon (native Linux support)")

        print("")
        print("========================================")
        print("  Desktop Shortcut Created!")
        print("========================================")
        print("")
        print("Look for this on your desktop:")
        print("  • Mesh Master")
        print("")
        print("What it does:")
        print("  • Kills any old/zombie Mesh Master processes")
        print("  • Starts fresh Mesh Master instance")
        print("  • Opens dashboard in browser")
        print("")

        return True

    except Exception as e:
        print(f"✗ Error creating shortcut: {e}")
        return False

if __name__ == "__main__":
    success = create_desktop_shortcuts()
    sys.exit(0 if success else 1)
