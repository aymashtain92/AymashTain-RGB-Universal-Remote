# install_and_repair.ps1
# AymashTain LED RGB Remote - installer + repair
# Free software. No ads. No telemetry.

$ErrorActionPreference = "Stop"

function Write-Header($text) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  $text" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Write-OK($text)    { Write-Host "  [OK]   $text" -ForegroundColor Green }
function Write-Warn($text)  { Write-Host "  [WARN] $text" -ForegroundColor Yellow }
function Write-Err($text)   { Write-Host "  [ERR]  $text" -ForegroundColor Red }
function Write-Info($text)  { Write-Host "  [INFO] $text" -ForegroundColor Gray }

Write-Header "AymashTain LED RGB Remote - Install and Repair"

# ---------------------------------------------------------------
# 1. Python
# ---------------------------------------------------------------
Write-Header "1. Python"

$python = $null
foreach ($candidate in @("py", "python", "python3")) {
    try {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) {
            $python = $cmd.Source
            break
        }
    } catch {}
}

if (-not $python) {
    Write-Err "Python not found on PATH."
    Write-Host ""
    Write-Host "Install Python 3.10 or newer (3.12 recommended) from:" -ForegroundColor Yellow
    Write-Host "   https://www.python.org/downloads/windows/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "During installation, check 'Add python.exe to PATH'." -ForegroundColor Yellow
    Read-Host "Press Enter to open the download page"
    Start-Process "https://www.python.org/downloads/windows/"
    exit 1
}

# Get version
if ($python -like "*py.exe" -or $python -like "*\py") {
    $pyVersionRaw = & py -V 2>&1
} else {
    $pyVersionRaw = & $python -V 2>&1
}

Write-Info "Detected: $pyVersionRaw"

if ($pyVersionRaw -match "Python (\d+)\.(\d+)\.(\d+)") {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
        Write-Err "Python 3.10+ is required. You have $major.$minor."
        exit 1
    }
    Write-OK "Python version is acceptable."
} else {
    Write-Warn "Could not parse Python version. Continuing anyway."
}

# Helper to run python
function Invoke-Py {
    param([Parameter(ValueFromRemainingArguments=$true)]$Args)
    if ($python -like "*py.exe" -or $python -like "*\py") {
        & py @Args
    } else {
        & $python @Args
    }
}

# ---------------------------------------------------------------
# 2. pip and required packages
# ---------------------------------------------------------------
Write-Header "2. Python packages"

Write-Info "Upgrading pip, setuptools, wheel..."
Invoke-Py -m pip install --upgrade pip setuptools wheel | Out-Null

$requirements = Join-Path $PSScriptRoot "requirements.txt"
if (Test-Path $requirements) {
    Write-Info "Installing from requirements.txt..."
    Invoke-Py -m pip install -r $requirements
} else {
    Write-Warn "requirements.txt not found. Installing essential packages directly."
    Invoke-Py -m pip install PySide6 "bleak>=0.22.0" qasync numpy opencv-python soundfile sounddevice
}

# ---------------------------------------------------------------
# 3. Verify imports
# ---------------------------------------------------------------
Write-Header "3. Verifying imports"

$check = @"
import sys
mods = [
    ("PySide6", "PySide6"),
    ("PySide6.QtMultimedia", "PySide6.QtMultimedia"),
    ("bleak", "bleak"),
    ("qasync", "qasync"),
    ("numpy", "numpy"),
    ("cv2", "opencv-python"),
    ("sounddevice", "sounddevice"),
    ("soundfile", "soundfile"),
]
ok = True
for mod, pipname in mods:
    try:
        __import__(mod)
        print(f"[OK]   {mod}")
    except Exception as e:
        print(f"[FAIL] {mod}  ({pipname})  -> {e}")
        ok = False
sys.exit(0 if ok else 1)
"@

$tmpFile = Join-Path $env:TEMP "aymashtain_imports.py"
Set-Content -Path $tmpFile -Value $check -Encoding UTF8

try {
    Invoke-Py $tmpFile
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Some imports failed. Try installing them manually:"
        Write-Host "   py -m pip install PySide6 bleak qasync numpy opencv-python soundfile sounddevice"
    } else {
        Write-OK "All essential imports OK."
    }
} finally {
    Remove-Item $tmpFile -ErrorAction SilentlyContinue
}

# ---------------------------------------------------------------
# 4. Visual C++ Redistributable
# ---------------------------------------------------------------
Write-Header "4. Visual C++ Redistributable"

$vcKeys = @(
    "HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"
)

$vcInstalled = $false
foreach ($k in $vcKeys) {
    if (Test-Path $k) {
        try {
            $installed = (Get-ItemProperty -Path $k -ErrorAction Stop).Installed
            if ($installed -eq 1) {
                $vcInstalled = $true
                break
            }
        } catch {}
    }
}

if ($vcInstalled) {
    Write-OK "Visual C++ Redistributable is installed."
} else {
    Write-Warn "Visual C++ Redistributable not detected."
    $answer = Read-Host "Download and install it now from Microsoft? (y/n)"
    if ($answer -eq "y" -or $answer -eq "Y") {
        $url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
        $out = Join-Path $env:TEMP "vc_redist.x64.exe"
        try {
            Write-Info "Downloading $url ..."
            Invoke-WebRequest -Uri $url -UseBasicParsing -OutFile $out
            Write-Info "Running installer (needs admin, click Yes)..."
            Start-Process -FilePath $out -ArgumentList "/install","/quiet","/norestart" -Wait
            Write-OK "Visual C++ Redistributable installed."
        } catch {
            Write-Err "Could not install VC++ Redistributable: $_"
            Write-Info "Manual link: https://aka.ms/vs/17/release/vc_redist.x64.exe"
        } finally {
            Remove-Item $out -ErrorAction SilentlyContinue
        }
    } else {
        Write-Info "Skipped. If the app crashes on start, install it manually:"
        Write-Host "   https://aka.ms/vs/17/release/vc_redist.x64.exe"
    }
}

# ---------------------------------------------------------------
# 5. Bluetooth service
# ---------------------------------------------------------------
Write-Header "5. Bluetooth"

$btService = Get-Service -Name "bthserv" -ErrorAction SilentlyContinue
if ($btService) {
    if ($btService.Status -eq "Running") {
        Write-OK "Bluetooth service is running."
    } else {
        Write-Warn "Bluetooth service is not running. Starting it..."
        try {
            Start-Service -Name "bthserv"
            Write-OK "Bluetooth started."
        } catch {
            Write-Warn "Could not start Bluetooth service. Enable it in Windows Settings."
        }
    }
} else {
    Write-Warn "Bluetooth service not found. Check Windows Settings > Devices > Bluetooth."
}

# ---------------------------------------------------------------
# 6. Folder structure
# ---------------------------------------------------------------
Write-Header "6. Project files"

$logs = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $logs)) {
    New-Item -ItemType Directory -Path $logs | Out-Null
    Write-OK "Created logs folder."
} else {
    Write-OK "logs folder exists."
}

$required = @("main.py", "mrstar_protocol.py")
foreach ($file in $required) {
    $p = Join-Path $PSScriptRoot $file
    if (Test-Path $p) {
        Write-OK "$file present."
    } else {
        Write-Err "$file missing."
    }
}

# ---------------------------------------------------------------
# Done
# ---------------------------------------------------------------
Write-Header "All done"
Write-Host ""
Write-Host "  To launch:  run the .bat file or:  py .\main.py" -ForegroundColor Green
Write-Host "  Free software. No ads. No telemetry." -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to close"