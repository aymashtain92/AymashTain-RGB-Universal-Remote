# =====================================================================
# debug_run.ps1
# Standalone diagnostic for AymashTain LED RGB Remote.
# Does NOT modify any app file. Only reads and reports.
# Writes one timestamped log in the project root.
# =====================================================================
#Requires -Version 5.1
[CmdletBinding()]
param(
    [int]$LaunchTimeoutSeconds = 40
)

$ErrorActionPreference = "Continue"

# --- locate project root ------------------------------------------------
if ($PSScriptRoot) {
    $Root = $PSScriptRoot
} else {
    $Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
}
if (-not $Root) { $Root = (Get-Location).Path }
Set-Location $Root

$Stamp    = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile  = Join-Path $Root "debug_powershell_run_$Stamp.txt"
$IdeaFile = Join-Path $Root "NEXT_SESSION_DEBUG_BUTTON_IDEA.txt"

$DataDir  = Join-Path $env:LOCALAPPDATA "AymashTain"
$LogsDir  = Join-Path $DataDir "logs"

# --- logging helpers ----------------------------------------------------
function W {
    param([string]$Text = "")
    Write-Host $Text
    Add-Content -Path $LogFile -Value $Text -Encoding UTF8
}
function Section {
    param([string]$Title)
    W ""
    W ("=" * 78)
    W ("== " + $Title)
    W ("=" * 78)
}

# --- init log -----------------------------------------------------------
"# AymashTain debug run - $Stamp" | Out-File -FilePath $LogFile -Encoding UTF8 -Force
W "Log file : $LogFile"
W "Root     : $Root"
W "Data dir : $DataDir"
W "Launch timeout: $LaunchTimeoutSeconds s"

# =====================================================================
# 0. Clean up residue from previous runs
# =====================================================================
Section "0. Clean up lingering python processes from this project"
$killed = 0
try {
    $procs = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction SilentlyContinue
    foreach ($p in $procs) {
        $cmd = $p.CommandLine
        if (-not $cmd) { continue }
        if ($cmd -match [regex]::Escape($Root) -or $cmd -match "aymashtain" -or $cmd -match "main\.py") {
            W ("Killing PID {0} - {1}" -f $p.ProcessId, $cmd)
            try { Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop; $killed++ } catch { W "  (already gone)" }
        }
    }
} catch {
    W "Residue scan failed (harmless): $_"
}
W ("Killed {0} lingering process(es)." -f $killed)
Start-Sleep -Seconds 2

# =====================================================================
# 1. Environment
# =====================================================================
Section "1. Environment"
W ("Date  : " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
try { W ("OS    : " + (Get-CimInstance Win32_OperatingSystem).Caption) } catch { W "OS    : unknown" }
try { W ("Build : " + [System.Environment]::OSVersion.Version) } catch {}

$py = $null
foreach ($c in @("python","py")) {
    if (Get-Command $c -ErrorAction SilentlyContinue) { $py = $c; break }
}
if (-not $py) {
    W "FATAL: no python on PATH."
    W "Save this log and send it to the next session."
    exit 1
}
W "Python launcher: $py"
try { W ("Python version : " + ((& $py --version 2>&1) -join " ").Trim()) } catch {}

W ""
W "Package versions:"
foreach ($pkg in @("bleak","numpy","opencv-python","PySide6","sounddevice","soundfile","pytest")) {
    try {
        $show = & $py -m pip show $pkg 2>$null
        if ($show) {
            $v = ($show | Where-Object { $_ -like "Version:*" } | Select-Object -First 1)
            W ("  {0,-18} {1}" -f $pkg, ($v -replace "^Version:\s*",""))
        } else {
            W ("  {0,-18} NOT INSTALLED" -f $pkg)
        }
    } catch { W ("  {0,-18} (error querying)" -f $pkg) }
}

# =====================================================================
# 2. py_compile every .py under aymashtain\
# =====================================================================
Section "2. py_compile every .py under aymashtain\"
$pkgDir = Join-Path $Root "aymashtain"
$allPy  = @()
if (Test-Path $pkgDir) {
    $allPy = @(Get-ChildItem -Path $pkgDir -Filter *.py -Recurse -File)
}
W ("Found {0} .py file(s)" -f $allPy.Count)

$failedCompile = @()
foreach ($f in $allPy) {
    $rel = $f.FullName.Substring($Root.Length).TrimStart('\')
    $o = & $py -m py_compile $f.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
        W ("FAIL  {0}" -f $rel)
        if ($o) { foreach ($ln in $o) { W ("      " + $ln) } }
        $failedCompile += $rel
    }
}
if ($failedCompile.Count -eq 0) {
    W "All files compile clean."
} else {
    W ("{0} file(s) failed to compile." -f $failedCompile.Count)
}

# =====================================================================
# 3. pytest
# =====================================================================
Section "3. python -m pytest -q"
try {
    $pt = & $py -m pytest -q 2>&1 | Out-String
    W $pt
} catch {
    W ("pytest raised: $_")
}

# =====================================================================
# 4 / 5. Launch attempt
# =====================================================================
Section ("4. Launch attempt - run.bat, then python .\main.py (grace {0} s)" -f $LaunchTimeoutSeconds)

$runBat = Join-Path $Root "run.bat"
$appProc  = $null
$launchUsed = ""

function Start-AppProc {
    param([string]$FileName, [string[]]$ArgList)
    $outFile = Join-Path $env:TEMP "ay_debug_out.txt"
    $errFile = Join-Path $env:TEMP "ay_debug_err.txt"
    Remove-Item $outFile, $errFile -ErrorAction SilentlyContinue
    try {
        $p = Start-Process -FilePath $FileName -ArgumentList $ArgList -PassThru `
             -WorkingDirectory $Root -NoNewWindow `
             -RedirectStandardOutput $outFile -RedirectStandardError $errFile
        return @{ proc = $p; out = $outFile; err = $errFile }
    } catch {
        W ("Start-Process failed for {0}: {1}" -f $FileName, $_)
        return $null
    }
}

$attempts = @()
if (Test-Path $runBat) {
    $attempts += @{ file = "cmd.exe"; args = @("/c", $runBat); label = "run.bat" }
}
$attempts += @{ file = $py; args = @(".\main.py"); label = "python .\main.py" }

foreach ($a in $attempts) {
    W ""
    W ("Trying: {0}" -f $a.label)
    $r = Start-AppProc -FileName $a.file -ArgList $a.args
    if (-not $r) { continue }

    Start-Sleep -Seconds $LaunchTimeoutSeconds
    try { $r.proc.Refresh() } catch {}

    if ($r.proc.HasExited) {
        W ("{0}: EXITED within {1} s - exit code {2}" -f $a.label, $LaunchTimeoutSeconds, $r.proc.ExitCode)
        $so = Get-Content $r.out -Raw -ErrorAction SilentlyContinue
        $se = Get-Content $r.err -Raw -ErrorAction SilentlyContinue
        if ($so) { W "--- STDOUT ---"; W $so.Trim(); W "--- END STDOUT ---" }
        if ($se) { W "--- STDERR ---"; W $se.Trim(); W "--- END STDERR ---" }
        continue
    }

    # Still alive -> it launched OK. Wait for the user to close it.
    $appProc    = $r.proc
    $launchUsed = $a.label
    W ("{0}: ALIVE after {1} s - launched OK." -f $a.label, $LaunchTimeoutSeconds)
    W "Now waiting for you to close the app window yourself."
    W "Process-level tracking: exit code + duration only."
    W "Individual clicks are NOT captured (needs app instrumentation)."
    W ""
    $started = Get-Date
    try { $appProc.WaitForExit() } catch {}
    $ended = Get-Date
    $dur = ($ended - $started).TotalSeconds

    W ("App CLOSED. Exit code: {0}" -f $appProc.ExitCode)
    W ("Wall time: {0:N1} s" -f $dur)
    $so = Get-Content $r.out -Raw -ErrorAction SilentlyContinue
    $se = Get-Content $r.err -Raw -ErrorAction SilentlyContinue
    if ($so) { W "--- STDOUT ---"; W $so.Trim(); W "--- END STDOUT ---" }
    if ($se) { W "--- STDERR ---"; W $se.Trim(); W "--- END STDERR ---" }
    break
}

if (-not $appProc) {
    W ""
    W "NEITHER launch method stayed alive. The app cannot start."
}

# =====================================================================
# 6. Session logs + crash log
# =====================================================================
Section "6. Session logs from %LOCALAPPDATA%\AymashTain\logs"
if (Test-Path $LogsDir) {
    $sess = @(Get-ChildItem -Path $LogsDir -Filter "session_*" -File -ErrorAction SilentlyContinue |
              Sort-Object LastWriteTime -Descending | Select-Object -First 6)
    if ($sess.Count -gt 0) {
        W "Newest 6 session files:"
        foreach ($s in $sess) {
            W ("  {0}  {1}  ({2} bytes)" -f $s.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss"), $s.Name, $s.Length)
        }
        $newestLog  = $sess | Where-Object { $_.Name -like "*.log"  } | Select-Object -First 1
        $newestJson = $sess | Where-Object { $_.Name -like "*.json" } | Select-Object -First 1
        if ($newestLog) {
            W ""
            W ("--- {0} ---" -f $newestLog.Name)
            W ((Get-Content $newestLog.FullName -Raw -ErrorAction SilentlyContinue))
            W "--- END LOG ---"
        }
        if ($newestJson) {
            W ""
            W ("--- {0} ---" -f $newestJson.Name)
            W ((Get-Content $newestJson.FullName -Raw -ErrorAction SilentlyContinue))
            W "--- END JSON ---"
        }
    } else {
        W "No session_* files found."
    }

    $crash = Join-Path $DataDir "crash.log"
    if (Test-Path $crash) {
        W ""
        W "--- crash.log ---"
        W ((Get-Content $crash -Raw -ErrorAction SilentlyContinue))
        W "--- END crash.log ---"
    }
} else {
    W ("Logs dir does not exist: {0}" -f $LogsDir)
}

# =====================================================================
# 7. Isolated imports
# =====================================================================
Section "7. Isolated imports (catches the Session 8 __init__.py bug)"
W "7a. import aymashtain"
$r1 = (& $py -c "import aymashtain; print('OK', aymashtain.APP_VERSION)" 2>&1 | Out-String)
W $r1.Trim()

W ""
W "7b. import aymashtain.app"
$r2 = (& $py -c "import aymashtain.app; print('OK app')" 2>&1 | Out-String)
W $r2.Trim()

W ""
W "7c. from aymashtain.ui.main_window import MainWindow"
$r3 = (& $py -c "from aymashtain.ui.main_window import MainWindow; print('OK MainWindow')" 2>&1 | Out-String)
W $r3.Trim()

W ""
W "7d. import aymashtain.ui.tabs"
$r4 = (& $py -c "import aymashtain.ui.tabs as t; print('OK tabs', [x for x in dir(t) if x.endswith('Tab')])" 2>&1 | Out-String)
W $r4.Trim()

# =====================================================================
# 8. Priority file inventory
# =====================================================================
Section "8. Priority file inventory"
$priority = @(
    "aymashtain\config.py",
    "aymashtain\ui\context.py",
    "aymashtain\ui\theme.py",
    "aymashtain\ui\main_window.py",
    "aymashtain\ui\tabs\console_tab.py",
    "aymashtain\ui\tabs\sweep_tab.py",
    "aymashtain\ui\tabs\options_tab.py",
    "aymashtain\ui\tabs\camera_tab.py",
    "aymashtain\ui\tabs\music_tab.py",
    "aymashtain\ui\tabs\remote_tab.py"
)
W "Files touched in Session 12:"
foreach ($rel in $priority) {
    $full = Join-Path $Root $rel
    if (Test-Path $full) {
        $f = Get-Item $full
        $status = "OK"
        if ($failedCompile -contains $rel) { $status = "COMPILE FAILED" }
        W ("  {0,-50} {1,8} bytes  {2}  [{3}]" -f $rel, $f.Length, $f.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss"), $status)
    } else {
        W ("  {0,-50} MISSING" -f $rel)
    }
}

W ""
W "All .py files sorted by most recently modified (top 20):"
Get-ChildItem -Path $Root -Filter *.py -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch "\\\.venv\\|\\__pycache__\\|\\build\\|\\dist\\" } |
    Sort-Object LastWriteTime -Descending | Select-Object -First 20 | ForEach-Object {
        $rel = $_.FullName.Substring($Root.Length).TrimStart('\')
        W ("  {0}  {1}" -f $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss"), $rel)
    }

# =====================================================================
# 9. Summary
# =====================================================================
Section "9. SUMMARY"
if ($failedCompile.Count -gt 0) {
    W ("py_compile failures : {0}" -f ($failedCompile -join ", "))
} else {
    W "py_compile failures : none"
}
if ($launchUsed) {
    W ("Launch result       : OK via {0} (user closed it)" -f $launchUsed)
} else {
    W "Launch result       : FAILED - neither run.bat nor python .\main.py stayed alive"
}
W ""
W ("Log saved to        : {0}" -f $LogFile)

# =====================================================================
# 10. Debug-button idea for next session
# =====================================================================
Section "10. Debug button idea for next session (NOT part of the app yet)"
$idea = @"
PROMPT FOR NEXT AI SESSION - ADD A DEBUG BUTTON INSIDE THE APP

Goal: a small "Run diagnostics" button inside the app that performs
the same checks this PowerShell script performs, and writes the
report to the same folder.

Placement (suggested): Help menu -> "Run diagnostics", or a new
"Diagnostics" group box on the Options tab.

Behaviour when clicked:
  1. Run in a background thread (do not block the UI):
     - py_compile every .py under aymashtain\
     - collect pip versions of the six key packages
     - import aymashtain, aymashtain.app, and MainWindow in
       subprocesses so a broken module cannot crash the running app
  2. Write the report to:
       <project root>\debug_button_YYYYMMDD_HHMMSS.txt
  3. Show a message box: "Diagnostics saved to <path>. Open folder?"
  4. Never touch app state. Never send frames. Never modify any file
     except the one report it writes.

Files to touch (one at a time, full replacements):
  - aymashtain/ui/main_window.py   (menu item + handler)
  - aymashtain/ui/tabs/options_tab.py   (optional - button placement)

Do NOT add this until Round 3 verification is complete and the
launch failure from Session 12 is fixed.
"@
W $idea
$idea | Out-File -FilePath $IdeaFile -Encoding UTF8 -Force
W ""
W ("Idea file also written to: {0}" -f $IdeaFile)

W ""
W "=== END OF DEBUG RUN ==="