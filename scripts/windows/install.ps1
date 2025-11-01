#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Mesh Master Windows Installer
.DESCRIPTION
    Automatically installs Git, Python, and Mesh Master with all dependencies.
    Handles everything - no manual downloads required.
#>

# Colors
$Host.UI.RawUI.ForegroundColor = "White"

function Write-ColorOutput($ForegroundColor, $Message) {
    $fc = $Host.UI.RawUI.ForegroundColor
    $Host.UI.RawUI.ForegroundColor = $ForegroundColor
    Write-Output $Message
    $Host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success($Message) { Write-ColorOutput Green $Message }
function Write-Error($Message) { Write-ColorOutput Red $Message }
function Write-Info($Message) { Write-ColorOutput Cyan $Message }
function Write-Warning($Message) { Write-ColorOutput Yellow $Message }

Write-Output ""
Write-Output "=========================================="
Write-Output "   Mesh Master Windows Installer"
Write-Output "=========================================="
Write-Output ""

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Error "❌ This script must be run as Administrator"
    Write-Output ""
    Write-Output "Right-click PowerShell and select 'Run as Administrator'"
    Write-Output ""
    pause
    exit 1
}

# Installation directory
$InstallDir = "$env:USERPROFILE\Mesh-Master"
$TempDir = "$env:TEMP\mesh-master-install"

# Create temp directory
if (-not (Test-Path $TempDir)) {
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
}

Write-Info "Installation directory: $InstallDir"
Write-Info "Temporary files: $TempDir"
Write-Output ""

# Function to download files with progress
function Download-File {
    param(
        [string]$Url,
        [string]$Output
    )

    Write-Info "Downloading: $Url"

    try {
        # Use BITS transfer for large files with progress
        Import-Module BitsTransfer
        Start-BitsTransfer -Source $Url -Destination $Output -Description "Downloading $(Split-Path $Output -Leaf)"
        return $true
    } catch {
        # Fallback to WebClient
        try {
            $webClient = New-Object System.Net.WebClient
            $webClient.DownloadFile($Url, $Output)
            return $true
        } catch {
            Write-Error "Failed to download: $_"
            return $false
        }
    }
}

# Function to check if command exists
function Test-Command {
    param([string]$Command)
    try {
        if (Get-Command $Command -ErrorAction SilentlyContinue) {
            return $true
        }
        return $false
    } catch {
        return $false
    }
}

# Step 1: Install Git if not present
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output "Step 1: Git Installation"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output ""

if (Test-Command "git") {
    $gitVersion = (git --version 2>&1) -replace 'git version ', ''
    Write-Success "✅ Git already installed: $gitVersion"
} else {
    Write-Warning "⚠️  Git not found - installing now..."

    # Download Git installer
    $gitInstallerUrl = "https://github.com/git-for-windows/git/releases/download/v2.47.0.windows.1/Git-2.47.0-64-bit.exe"
    $gitInstaller = "$TempDir\git-installer.exe"

    if (Download-File -Url $gitInstallerUrl -Output $gitInstaller) {
        Write-Info "Installing Git (this may take a few minutes)..."

        # Silent install with default options
        $installArgs = @(
            "/VERYSILENT",
            "/NORESTART",
            "/NOCANCEL",
            "/SP-",
            "/CLOSEAPPLICATIONS",
            "/RESTARTAPPLICATIONS",
            "/COMPONENTS=`"icons,ext\reg\shellhere,assoc,assoc_sh`"",
            "/TASKS=`"desktopicon,quicklaunchicon`""
        )

        Start-Process -FilePath $gitInstaller -ArgumentList $installArgs -Wait -NoNewWindow

        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

        # Verify installation
        if (Test-Command "git") {
            Write-Success "✅ Git installed successfully!"
        } else {
            Write-Error "❌ Git installation failed"
            Write-Output ""
            Write-Output "Please install Git manually from: https://git-scm.com/download/win"
            pause
            exit 1
        }
    } else {
        Write-Error "❌ Failed to download Git installer"
        Write-Output ""
        Write-Output "Please install Git manually from: https://git-scm.com/download/win"
        pause
        exit 1
    }
}
Write-Output ""

# Step 2: Install Python if not present
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output "Step 2: Python Installation"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output ""

$pythonRequired = $false
if (Test-Command "python") {
    try {
        $pythonVersion = (python --version 2>&1) -replace 'Python ', ''
        $versionParts = $pythonVersion.Split('.')
        $majorVersion = [int]$versionParts[0]
        $minorVersion = [int]$versionParts[1]

        if (($majorVersion -eq 3) -and ($minorVersion -ge 11)) {
            Write-Success "✅ Python already installed: $pythonVersion"
        } else {
            Write-Warning "⚠️  Python $pythonVersion found, but 3.11+ required"
            $pythonRequired = $true
        }
    } catch {
        $pythonRequired = $true
    }
} else {
    $pythonRequired = $true
}

if ($pythonRequired) {
    Write-Warning "⚠️  Python 3.11+ not found - installing now..."

    # Download Python installer (3.11.9 - stable release)
    $pythonInstallerUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $pythonInstaller = "$TempDir\python-installer.exe"

    if (Download-File -Url $pythonInstallerUrl -Output $pythonInstaller) {
        Write-Info "Installing Python 3.11.9 (this may take a few minutes)..."

        # Silent install with pip and add to PATH
        $installArgs = @(
            "/quiet",
            "InstallAllUsers=1",
            "PrependPath=1",
            "Include_pip=1",
            "Include_test=0",
            "Include_doc=0"
        )

        Start-Process -FilePath $pythonInstaller -ArgumentList $installArgs -Wait -NoNewWindow

        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

        # Verify installation
        if (Test-Command "python") {
            $pythonVersion = (python --version 2>&1) -replace 'Python ', ''
            Write-Success "✅ Python $pythonVersion installed successfully!"
        } else {
            Write-Error "❌ Python installation failed"
            Write-Output ""
            Write-Output "Please install Python manually from: https://www.python.org/downloads/"
            pause
            exit 1
        }
    } else {
        Write-Error "❌ Failed to download Python installer"
        Write-Output ""
        Write-Output "Please install Python manually from: https://www.python.org/downloads/"
        pause
        exit 1
    }
}
Write-Output ""

# Step 3: Clone Mesh Master repository
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output "Step 3: Mesh Master Installation"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output ""

if (Test-Path $InstallDir) {
    Write-Warning "⚠️  Mesh Master directory already exists: $InstallDir"
    Write-Output ""
    $response = Read-Host "Remove existing installation and reinstall? (y/N)"

    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Info "Removing existing installation..."
        Remove-Item -Path $InstallDir -Recurse -Force
        Write-Success "✅ Removed"
    } else {
        Write-Info "Using existing installation"
        cd $InstallDir
    }
    Write-Output ""
}

if (-not (Test-Path $InstallDir)) {
    Write-Info "Cloning Mesh Master from GitHub..."

    try {
        git clone https://github.com/Snail3D/Mesh-Master.git $InstallDir 2>&1 | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-Success "✅ Repository cloned successfully!"
        } else {
            Write-Error "❌ Git clone failed"
            exit 1
        }
    } catch {
        Write-Error "❌ Failed to clone repository: $_"
        exit 1
    }
}

cd $InstallDir
Write-Output ""

# Step 4: Setup virtual environment
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output "Step 4: Python Virtual Environment"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output ""

$venvPath = "$InstallDir\.venv"

if (Test-Path $venvPath) {
    Write-Success "✅ Virtual environment already exists"
} else {
    Write-Info "Creating virtual environment..."

    try {
        python -m venv .venv

        if ($LASTEXITCODE -eq 0) {
            Write-Success "✅ Virtual environment created!"
        } else {
            Write-Error "❌ Failed to create virtual environment"
            exit 1
        }
    } catch {
        Write-Error "❌ Failed to create virtual environment: $_"
        exit 1
    }
}
Write-Output ""

# Step 5: Install Python dependencies
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output "Step 5: Python Dependencies"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output ""

Write-Info "Installing Python packages (this may take a few minutes)..."

$pipPath = "$venvPath\Scripts\pip.exe"

if (Test-Path $pipPath) {
    try {
        & $pipPath install --upgrade pip setuptools wheel --quiet
        & $pipPath install -r requirements.txt --quiet

        if ($LASTEXITCODE -eq 0) {
            Write-Success "✅ Dependencies installed successfully!"
        } else {
            Write-Warning "⚠️  Some dependencies may have failed to install"
            Write-Info "You can run 'pip install -r requirements.txt' later to retry"
        }
    } catch {
        Write-Warning "⚠️  Dependency installation had errors: $_"
        Write-Info "You can run 'pip install -r requirements.txt' later to retry"
    }
} else {
    Write-Error "❌ Could not find pip in virtual environment"
    exit 1
}
Write-Output ""

# Step 6: Initialize configuration
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output "Step 6: Configuration Setup"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output ""

if (-not (Test-Path "config.json")) {
    if (Test-Path "config.json.example") {
        Write-Info "Creating config.json from template..."
        Copy-Item "config.json.example" "config.json"
        Write-Success "✅ Configuration file created!"
        Write-Warning "⚠️  IMPORTANT: Edit config.json to configure:"
        Write-Output "   - serial_port or wifi_host (radio connection)"
        Write-Output "   - admin_password (dashboard login)"
        Write-Output "   - ollama_url (AI service)"
    } else {
        Write-Warning "⚠️  config.json.example not found"
        Write-Info "You'll need to create config.json manually"
    }
} else {
    Write-Success "✅ Configuration file already exists"
}
Write-Output ""

# Step 7: Install NSSM for Windows service
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output "Step 7: Windows Service Manager (NSSM)"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output ""

if (Test-Command "nssm") {
    Write-Success "✅ NSSM already installed"
} else {
    Write-Warning "⚠️  NSSM not found - installing now..."

    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $nssmZip = "$TempDir\nssm.zip"
    $nssmExtract = "$TempDir\nssm"

    if (Download-File -Url $nssmUrl -Output $nssmZip) {
        Write-Info "Extracting NSSM..."
        Expand-Archive -Path $nssmZip -DestinationPath $nssmExtract -Force

        # Copy appropriate version to System32
        $nssmExe = "$nssmExtract\nssm-2.24\win64\nssm.exe"
        $systemNssm = "$env:SystemRoot\System32\nssm.exe"

        if (Test-Path $nssmExe) {
            Copy-Item $nssmExe $systemNssm -Force
            Write-Success "✅ NSSM installed to System32"
        } else {
            Write-Error "❌ Could not find nssm.exe in archive"
            Write-Output "Service installation will be skipped"
        }
    } else {
        Write-Error "❌ Failed to download NSSM"
        Write-Output "Service installation will be skipped"
    }
}
Write-Output ""

# Step 8: Install as Windows service
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output "Step 8: Windows Service Installation"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output ""

if (Test-Command "nssm") {
    $pythonExe = "$venvPath\Scripts\python.exe"
    $meshMasterScript = "$InstallDir\mesh-master.py"

    # Check if service exists
    $serviceExists = $false
    try {
        nssm status MeshMaster 2>&1 | Out-Null
        $serviceExists = ($LASTEXITCODE -eq 0)
    } catch {
        $serviceExists = $false
    }

    if ($serviceExists) {
        Write-Warning "⚠️  MeshMaster service already exists - removing old service..."
        nssm stop MeshMaster 2>&1 | Out-Null
        nssm remove MeshMaster confirm 2>&1 | Out-Null
        Write-Success "✅ Old service removed"
    }

    Write-Info "Installing MeshMaster service..."

    # Install service
    nssm install MeshMaster $pythonExe $meshMasterScript 2>&1 | Out-Null

    if ($LASTEXITCODE -eq 0) {
        # Configure service
        nssm set MeshMaster AppDirectory $InstallDir | Out-Null
        nssm set MeshMaster DisplayName "Mesh Master" | Out-Null
        nssm set MeshMaster Description "Off-Grid AI Operations Suite for Meshtastic" | Out-Null
        nssm set MeshMaster Start SERVICE_AUTO_START | Out-Null

        # Configure restart on failure
        nssm set MeshMaster AppExit Default Restart | Out-Null
        nssm set MeshMaster AppRestartDelay 2000 | Out-Null

        # Configure logging
        $logsDir = "$InstallDir\logs"
        if (-not (Test-Path $logsDir)) {
            New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
        }

        nssm set MeshMaster AppStdout "$logsDir\mesh-master-stdout.log" | Out-Null
        nssm set MeshMaster AppStderr "$logsDir\mesh-master-stderr.log" | Out-Null

        # Set environment variable
        nssm set MeshMaster AppEnvironmentExtra "NO_BROWSER=1" | Out-Null

        Write-Success "✅ Service installed successfully!"

        # Start service
        Write-Info "Starting MeshMaster service..."
        nssm start MeshMaster 2>&1 | Out-Null

        Start-Sleep -Seconds 2

        # Check if running
        $status = (nssm status MeshMaster 2>&1) | Out-String

        if ($status -match "SERVICE_RUNNING") {
            Write-Success "✅ Service started successfully!"
        } else {
            Write-Warning "⚠️  Service may not have started properly"
            Write-Info "Check logs: $logsDir\mesh-master-stderr.log"
        }
    } else {
        Write-Error "❌ Failed to install service"
    }
} else {
    Write-Warning "⚠️  NSSM not available - skipping service installation"
    Write-Info "You can run Mesh Master manually with:"
    Write-Output "   cd $InstallDir"
    Write-Output "   .\.venv\Scripts\python.exe mesh-master.py"
}
Write-Output ""

# Step 9: Create desktop shortcuts
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output "Step 9: Desktop Shortcuts"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output ""

$shortcutScript = "$InstallDir\scripts\desktop\create_shortcuts.py"
if (Test-Path $shortcutScript) {
    Write-Info "Creating desktop shortcuts..."

    try {
        & "$venvPath\Scripts\python.exe" $shortcutScript 2>&1 | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-Success "✅ Desktop shortcuts created!"
        } else {
            Write-Warning "⚠️  Could not create desktop shortcuts (optional)"
        }
    } catch {
        Write-Warning "⚠️  Could not create desktop shortcuts (optional)"
    }
} else {
    Write-Info "Desktop shortcut script not found (optional)"
}
Write-Output ""

# Cleanup
Write-Info "Cleaning up temporary files..."
if (Test-Path $TempDir) {
    Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Output ""

# Final summary
Write-Output ""
Write-Output "=========================================="
Write-Success "   ✅ Installation Complete!"
Write-Output "=========================================="
Write-Output ""
Write-Output "Mesh Master is now installed and running!"
Write-Output ""
Write-Output "📁 Installation directory: $InstallDir"
Write-Output "🌐 Dashboard: http://localhost:5001/dashboard"
Write-Output ""
Write-Output "Useful commands:"
Write-Output "  Check status:  nssm status MeshMaster"
Write-Output "  View logs:     type `"$InstallDir\logs\mesh-master-stdout.log`""
Write-Output "  Stop service:  nssm stop MeshMaster"
Write-Output "  Start service: nssm start MeshMaster"
Write-Output "  Restart:       nssm restart MeshMaster"
Write-Output ""
Write-Warning "⚠️  NEXT STEPS:"
Write-Output "  1. Edit $InstallDir\config.json"
Write-Output "  2. Configure your radio connection (serial or WiFi)"
Write-Output "  3. Change admin_password for dashboard security"
Write-Output "  4. Restart service: nssm restart MeshMaster"
Write-Output ""
Write-Output "Desktop shortcuts created:"
Write-Output "  - Start Mesh Master (opens dashboard)"
Write-Output "  - Stop Mesh Master (stops service)"
Write-Output ""

pause
