#Requires -RunAsAdministrator

<#
.SYNOPSIS
    Mesh Master Windows Uninstaller
.DESCRIPTION
    Removes Mesh Master service, shortcuts, and optionally the entire installation.
    Set $env:AUTO_DELETE="true" to delete everything including data and config.
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
Write-Output "   Mesh Master Windows Uninstaller"
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

$InstallDir = "$env:USERPROFILE\Mesh-Master"

# Check if installation exists
if (-not (Test-Path $InstallDir)) {
    Write-Warning "⚠️  Mesh Master installation not found at: $InstallDir"
    Write-Output ""
    Write-Output "Nothing to uninstall."
    pause
    exit 0
}

# Check for AUTO_DELETE environment variable
$autoDelete = $env:AUTO_DELETE -eq "true"

if ($autoDelete) {
    Write-Warning "⚠️  COMPLETE REMOVAL MODE"
    Write-Output ""
    Write-Output "This will permanently delete:"
    Write-Output "  - Windows service"
    Write-Output "  - Desktop shortcuts"
    Write-Output "  - All Mesh Master files"
    Write-Output "  - Configuration (config.json)"
    Write-Output "  - User data (logs, reports, mail, etc.)"
    Write-Output ""
    Write-Output "Installation directory: $InstallDir"
    Write-Output ""

    # Safety countdown
    Write-Warning "⏱️  Starting in 5 seconds... Press Ctrl+C to cancel"
    for ($i = 5; $i -gt 0; $i--) {
        Write-Output "$i..."
        Start-Sleep -Seconds 1
    }
    Write-Output ""
} else {
    Write-Info "SERVICE REMOVAL MODE"
    Write-Output ""
    Write-Output "This will remove:"
    Write-Output "  - Windows service"
    Write-Output "  - Desktop shortcuts"
    Write-Output "  - Running processes"
    Write-Output ""
    Write-Output "This will preserve:"
    Write-Output "  - Installation directory: $InstallDir"
    Write-Output "  - Configuration (config.json)"
    Write-Output "  - User data (logs, reports, mail, etc.)"
    Write-Output ""
}

# Step 1: Stop and remove service
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output "Step 1: Windows Service"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output ""

# Check if NSSM is available
if (Get-Command nssm -ErrorAction SilentlyContinue) {
    # Check if service exists
    $serviceExists = $false
    try {
        nssm status MeshMaster 2>&1 | Out-Null
        $serviceExists = ($LASTEXITCODE -eq 0)
    } catch {
        $serviceExists = $false
    }

    if ($serviceExists) {
        Write-Info "Stopping MeshMaster service..."
        nssm stop MeshMaster 2>&1 | Out-Null
        Start-Sleep -Seconds 2

        Write-Info "Removing MeshMaster service..."
        nssm remove MeshMaster confirm 2>&1 | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-Success "✅ Service removed successfully"
        } else {
            Write-Warning "⚠️  Failed to remove service (may not exist)"
        }
    } else {
        Write-Info "Service not found (already removed or never installed)"
    }
} else {
    Write-Info "NSSM not found (service may not have been installed)"
}
Write-Output ""

# Step 2: Kill any running processes
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output "Step 2: Running Processes"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output ""

$processes = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*mesh-master.py*"
}

if ($processes) {
    Write-Info "Stopping Mesh Master processes..."
    $processes | ForEach-Object {
        try {
            Stop-Process -Id $_.Id -Force
            Write-Success "✅ Stopped process PID: $($_.Id)"
        } catch {
            Write-Warning "⚠️  Could not stop PID: $($_.Id)"
        }
    }
} else {
    Write-Info "No running Mesh Master processes found"
}
Write-Output ""

# Step 3: Remove desktop shortcuts
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output "Step 3: Desktop Shortcuts"
Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
Write-Output ""

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcuts = @(
    "$desktopPath\Start Mesh Master.lnk",
    "$desktopPath\Stop Mesh Master.lnk",
    "$desktopPath\Mesh Master.lnk"
)

$removedShortcuts = 0
foreach ($shortcut in $shortcuts) {
    if (Test-Path $shortcut) {
        try {
            Remove-Item $shortcut -Force
            Write-Success "✅ Removed: $(Split-Path $shortcut -Leaf)"
            $removedShortcuts++
        } catch {
            Write-Warning "⚠️  Could not remove: $(Split-Path $shortcut -Leaf)"
        }
    }
}

if ($removedShortcuts -eq 0) {
    Write-Info "No desktop shortcuts found"
}
Write-Output ""

# Step 4: Remove installation directory (if AUTO_DELETE)
if ($autoDelete) {
    Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Output "Step 4: Installation Directory"
    Write-Output "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Write-Output ""

    # Safety checks
    $safeToDelete = $true

    # Path blacklist
    $blacklist = @("/", "C:\", "C:\Windows", "C:\Program Files", "C:\Program Files (x86)",
                   "$env:SystemRoot", "$env:ProgramFiles", "$env:ProgramFiles(x86)")

    foreach ($blocked in $blacklist) {
        if ($InstallDir -eq $blocked) {
            Write-Error "❌ SAFETY ABORT: Directory is blacklisted"
            Write-Output "Refusing to delete: $InstallDir"
            $safeToDelete = $false
            break
        }
    }

    # Name verification
    if ($safeToDelete -and $InstallDir -notmatch "Mesh-Master") {
        Write-Error "❌ SAFETY ABORT: Directory name doesn't contain 'Mesh-Master'"
        Write-Output "Refusing to delete: $InstallDir"
        $safeToDelete = $false
    }

    if ($safeToDelete) {
        Write-Warning "⚠️  Deleting installation directory..."
        Write-Info "Path: $InstallDir"

        try {
            Remove-Item -Path $InstallDir -Recurse -Force -ErrorAction Stop
            Write-Success "✅ Installation directory deleted"
        } catch {
            Write-Error "❌ Failed to delete installation directory: $_"
            Write-Output ""
            Write-Output "You may need to manually delete: $InstallDir"
        }
    }
    Write-Output ""
}

# Final summary
Write-Output ""
Write-Output "=========================================="
if ($autoDelete) {
    Write-Success "   ✅ Complete Removal Finished!"
} else {
    Write-Success "   ✅ Service Removal Complete!"
}
Write-Output "=========================================="
Write-Output ""

if ($autoDelete) {
    Write-Output "Mesh Master has been completely removed from your system."
    Write-Output ""
    Write-Output "To reinstall:"
    Write-Output "  irm https://raw.githubusercontent.com/Snail3D/Mesh-Master/main/scripts/windows/install.ps1 | iex"
} else {
    Write-Output "Service and shortcuts removed."
    Write-Output "Installation preserved at: $InstallDir"
    Write-Output ""
    Write-Output "To reinstall service:"
    Write-Output "  powershell -ExecutionPolicy Bypass -File `"$InstallDir\scripts\windows\install.ps1`""
    Write-Output ""
    Write-Output "To completely remove (delete everything):"
    Write-Output '  $env:AUTO_DELETE="true"; powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\Mesh-Master\scripts\windows\uninstall.ps1"'
}
Write-Output ""

pause
