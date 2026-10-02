<#
Live Actions installer (Windows).

  powershell -ExecutionPolicy Bypass -File install.ps1

What it does, all inside your user account (no admin rights):
  1. Creates .venv in this folder and installs the Python packages.
  2. Copies the Max for Live device into your Ableton User Library.
  3. Copies the optional browser Remote Script (LiveActionsRS) there too.
  4. Makes sure the bundled knowledge database is built.
  5. Adds a Desktop shortcut and the liveactions:// link the device's button uses.

It never asks for, reads or writes an API key. You add your own in the app.

Options:
  -UserLibrary "D:\Music\User Library"   use this folder instead of detecting it
  -NoShortcut                            skip the Desktop shortcut
  -NoProtocol                            skip the liveactions:// registration
  -SkipPackages                          skip creating .venv / pip install
#>
param(
    [string]$UserLibrary = "",
    [switch]$NoShortcut,
    [switch]$NoProtocol,
    [switch]$SkipPackages
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$bridge = Join-Path $root "bridge"
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$venvPythonw = Join-Path $root ".venv\Scripts\pythonw.exe"

function Write-Step([string]$text) { Write-Output ""; Write-Output "== $text" }

# ---- 1. Python + packages ----------------------------------------------------
function Find-Python {
    foreach ($candidate in @(@("py", "-3"), @("python"))) {
        $exe = $candidate[0]
        if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
        $rest = @($candidate | Select-Object -Skip 1)
        try {
            $version = & $exe @rest -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        } catch { continue }
        if ($version -match '^3\.(\d+)$' -and [int]$Matches[1] -ge 10) {
            return ,@($exe) + $rest
        }
    }
    return $null
}

Write-Step "Python packages"
if ($SkipPackages) {
    Write-Output "Skipped (-SkipPackages)."
} else {
    if (-not (Test-Path $venvPython)) {
        $python = Find-Python
        if (-not $python) {
            throw "Python 3.10 or newer was not found. Install Python 3.12 from python.org (tick 'Add python.exe to PATH'), then run this again."
        }
        $pyExe = $python[0]
        $pyArgs = @($python | Select-Object -Skip 1)
        & $pyExe @pyArgs -m venv (Join-Path $root ".venv")
        if ($LASTEXITCODE -ne 0) { throw "Could not create the .venv folder." }
    }
    & $venvPython -m pip install --disable-pip-version-check -q -r (Join-Path $root "requirements.txt")
    if ($LASTEXITCODE -ne 0) { throw "pip could not install the packages in requirements.txt." }
    Write-Output "Packages installed into .venv"
}
$runPython = if (Test-Path $venvPython) { $venvPython } else { "python" }

# ---- 2. Find the Ableton User Library -------------------------------------------
function Find-UserLibrary {
    # Live records the User Library location in Library.cfg (one per installed Live version).
    $prefs = Join-Path $env:APPDATA "Ableton"
    if (Test-Path $prefs) {
        $cfgs = Get-ChildItem -Path $prefs -Filter "Library.cfg" -Recurse -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending
        foreach ($cfg in $cfgs) {
            try {
                [xml]$doc = Get-Content -Path $cfg.FullName -Raw -Encoding UTF8
                $project = $doc.SelectSingleNode("//UserLibrary/LibraryProject")
                if (-not $project) { continue }
                $parent = $project.ProjectPath.Value
                $name = $project.ProjectName.Value
                if ($parent -and $name) {
                    $candidate = Join-Path ($parent -replace '/', '\') $name
                    if (Test-Path $candidate) { return $candidate }
                }
            } catch { continue }
        }
    }
    $default = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "Ableton\User Library"
    if (Test-Path $default) { return $default }
    return $null
}

Write-Step "Ableton User Library"
if (-not $UserLibrary) { $UserLibrary = Find-UserLibrary }
if (-not $UserLibrary) {
    Write-Output "Could not find your Ableton User Library automatically."
    Write-Output "In Live it is shown under Settings > Library > Location of User Library."
    $UserLibrary = Read-Host "Paste the full path to your User Library folder"
}
if (-not $UserLibrary -or -not (Test-Path $UserLibrary)) {
    throw "User Library folder not found: '$UserLibrary'. Run again with -UserLibrary `"<path>`"."
}
Write-Output "Using $UserLibrary"

# ---- 3. The Max for Live device --------------------------------------------------
Write-Step "Max for Live device"
$dest = Join-Path $UserLibrary "Presets\Audio Effects\Max Audio Effect\Live Actions"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
& $runPython (Join-Path $bridge "pack-amxd.py")
if ($LASTEXITCODE -ne 0) { throw "Could not build the Max for Live device." }

# Stamp a fresh build id into the DEPLOYED copy only. It lets the check at the
# end tell a freshly re-dropped device from one still running older code: Max
# only reloads the script when the device is removed and re-added to a track.
$buildId = Get-Date -Format "yyyyMMddTHHmmss"
# Read and write as UTF-8 explicitly: Windows PowerShell 5.1 defaults to the
# system ANSI codepage, which corrupts non-ASCII characters in the script.
$bridgeJs = Get-Content (Join-Path $bridge "live-actions-bridge.js") -Raw -Encoding UTF8
$bridgeJs = $bridgeJs -replace 'var BRIDGE_BUILD = "[^"]*";', "var BRIDGE_BUILD = `"$buildId`";"
[IO.File]::WriteAllText((Join-Path $dest "live-actions-bridge.js"), $bridgeJs, (New-Object Text.UTF8Encoding $false))

Copy-Item -Force (Join-Path $bridge "live-actions-pal.js") $dest
Copy-Item -Force (Join-Path $bridge "Live Actions Bridge.maxpat") $dest
Copy-Item -Force (Join-Path $bridge "Live Actions Bridge.amxd") (Join-Path $dest "Live Actions.amxd")
Set-Content -Path (Join-Path $dest "host-path.txt") -Value (Join-Path $root "Launch Live Actions.bat") -Encoding ascii
Write-Output "Installed to $dest"

# ---- 4. Browser Remote Script (optional engine) ------------------------------------
# Live's browser panel is not reachable from Max for Live, only from a MIDI
# Remote Script. It goes in the User Library, so no admin rights are needed and
# a Live update cannot remove it.
Write-Step "Browser engine (LiveActionsRS)"
$rsSrc = Join-Path $root "remote_script\LiveActionsRS"
$rsDest = Join-Path $UserLibrary "Remote Scripts\LiveActionsRS"
New-Item -ItemType Directory -Force -Path $rsDest | Out-Null
Copy-Item -Force (Join-Path $rsSrc "__init__.py") $rsDest
Write-Output "Installed to $rsDest"

# ---- 5. Knowledge database ---------------------------------------------------------
Write-Step "Knowledge database"
$dbRoot = Join-Path $root "database"
$missing = @(Get-ChildItem -Path $dbRoot -Directory | Where-Object {
    (Test-Path (Join-Path $_.FullName "markdown")) -and -not (Test-Path (Join-Path $_.FullName ($_.Name + ".db")))
})
if ($missing.Count -gt 0) {
    & $runPython (Join-Path $dbRoot "build_database.py")
    if ($LASTEXITCODE -ne 0) { throw "Could not build the knowledge database." }
} else {
    $count = @(Get-ChildItem -Path $dbRoot -Directory | Where-Object { Test-Path (Join-Path $_.FullName "search.py") }).Count
    Write-Output "$count datasets ready in $dbRoot"
}

# ---- 6. Shortcut + liveactions:// link ------------------------------------------------
Write-Step "Shortcut and link"
if ($NoShortcut) {
    Write-Output "Desktop shortcut skipped (-NoShortcut)."
} else {
    $desktop = [Environment]::GetFolderPath("Desktop")
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut((Join-Path $desktop "Live Actions.lnk"))
    $shortcut.TargetPath = Join-Path $root "Launch Live Actions.bat"
    $shortcut.WorkingDirectory = $root
    $shortcut.WindowStyle = 7
    $shortcut.Description = "Live Actions"
    $shortcut.Save()
    Write-Output "Desktop shortcut: Live Actions.lnk"
}
if ($NoProtocol) {
    Write-Output "liveactions:// link skipped (-NoProtocol)."
} else {
    $pythonw = if (Test-Path $venvPythonw) { $venvPythonw } else { (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source }
    if ($pythonw) {
        $proto = "HKCU:\Software\Classes\liveactions"
        New-Item -Path $proto -Force | Out-Null
        Set-ItemProperty -Path $proto -Name "(default)" -Value "URL:Live Actions Protocol"
        New-ItemProperty -Path $proto -Name "URL Protocol" -Value "" -Force | Out-Null
        New-Item -Path "$proto\shell\open\command" -Force | Out-Null
        Set-ItemProperty -Path "$proto\shell\open\command" -Name "(default)" -Value ("`"{0}`" `"{1}`"" -f $pythonw, (Join-Path $root "app\shell.py"))
        Write-Output "Link registered: liveactions://open (the device's 'Open desktop host' button)"
    } else {
        Write-Warning "pythonw.exe not found, so the device's 'Open desktop host' button will not work. Use the Desktop shortcut."
    }
}

# ---- 7. Checks ----------------------------------------------------------------------
$webview2 = $null
foreach ($key in @(
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
    "HKLM:\SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
    "HKCU:\Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
)) {
    $pv = (Get-ItemProperty -Path $key -Name pv -ErrorAction SilentlyContinue).pv
    if ($pv -and $pv -ne "0.0.0.0") { $webview2 = $pv; break }
}
Write-Step "Checks"
if ($webview2) {
    Write-Output "WebView2 Runtime $webview2 found."
} else {
    Write-Output "*** Microsoft Edge WebView2 Runtime not found. Install the Evergreen runtime from microsoft.com/edge/webview2 before starting the app. ***"
}
if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
    Write-Output "ffmpeg found on PATH."
} else {
    Write-Output "ffmpeg not found on PATH. Only TTS Vocal and Audio Sample need it; set its path in Preferences if you install it."
}

# Is the device running in Live this build? Copying the file is not enough: a
# device already on a track keeps its old in-memory script until it is re-dropped.
function Test-BridgeBuild {
    param([int]$SendPort = 11924, [int]$ListenPort = 11925, [int]$TimeoutMs = 2500)
    $listener = $null
    $sender = $null
    try {
        $sock = New-Object System.Net.Sockets.Socket([System.Net.Sockets.AddressFamily]::InterNetwork, [System.Net.Sockets.SocketType]::Dgram, [System.Net.Sockets.ProtocolType]::Udp)
        $sock.SetSocketOption([System.Net.Sockets.SocketOptionLevel]::Socket, [System.Net.Sockets.SocketOptionName]::ReuseAddress, $true)
        $sock.Bind((New-Object System.Net.IPEndPoint([System.Net.IPAddress]::Parse("127.0.0.1"), $ListenPort)))
        $listener = New-Object System.Net.Sockets.UdpClient
        $listener.Client = $sock
        $listener.Client.ReceiveTimeout = $TimeoutMs

        $addrBytes = [System.Text.Encoding]::UTF8.GetBytes("/live-actions/ping" + "`0")
        $addrBytes += New-Object byte[] ((4 - ($addrBytes.Length % 4)) % 4)
        $tagBytes = [System.Text.Encoding]::UTF8.GetBytes("," + "`0")
        $tagBytes += New-Object byte[] ((4 - ($tagBytes.Length % 4)) % 4)
        $msg = $addrBytes + $tagBytes

        $sender = New-Object System.Net.Sockets.UdpClient
        $sender.Send($msg, $msg.Length, "127.0.0.1", $SendPort) | Out-Null

        $remote = New-Object System.Net.IPEndPoint([System.Net.IPAddress]::Any, 0)
        $deadline = (Get-Date).AddMilliseconds($TimeoutMs)
        while ((Get-Date) -lt $deadline) {
            $data = $listener.Receive([ref]$remote)
            $nul = [Array]::IndexOf($data, [byte]0)
            if ($nul -lt 0) { continue }
            $recvAddr = [System.Text.Encoding]::UTF8.GetString($data, 0, $nul)
            if ($recvAddr -ne "/live-actions/pong") { continue }
            $off = [Math]::Ceiling(($nul + 1) / 4.0) * 4
            $tagNul = [Array]::IndexOf($data, [byte]0, $off)
            $off = [Math]::Ceiling(($tagNul + 1) / 4.0) * 4
            $argNul = [Array]::IndexOf($data, [byte]0, $off)
            $json = [System.Text.Encoding]::UTF8.GetString($data, $off, $argNul - $off)
            return ($json | ConvertFrom-Json).build
        }
        return $null
    } catch {
        return $null
    } finally {
        if ($listener) { $listener.Close() }
        if ($sender) { $sender.Close() }
    }
}

$runningBuild = Test-BridgeBuild
if (-not $runningBuild) {
    Write-Output "Device not reachable yet (Live is closed, the device is not on a track, or the app is open). That is normal on a first install."
} elseif ($runningBuild -eq $buildId) {
    Write-Output "The device running in Live is this build ($buildId)."
} else {
    Write-Output "*** The device running in Live is an older build. Remove 'Live Actions' from its track and drag it back on. ***"
}

$rsOk = $false
try {
    $client = New-Object System.Net.Sockets.TcpClient
    $iar = $client.BeginConnect("127.0.0.1", 11926, $null, $null)
    if ($iar.AsyncWaitHandle.WaitOne(1500) -and $client.Connected) {
        $client.EndConnect($iar)
        $stream = $client.GetStream()
        $payload = [System.Text.Encoding]::UTF8.GetBytes('{"id":1,"action":"ping","params":{}}' + "`n")
        $stream.Write($payload, 0, $payload.Length)
        $stream.ReadTimeout = 3000
        $buf = New-Object byte[] 8192
        $n = $stream.Read($buf, 0, $buf.Length)
        if ($n -gt 0 -and [System.Text.Encoding]::UTF8.GetString($buf, 0, $n) -match '"ok"\s*:\s*true') { $rsOk = $true }
    }
    $client.Close()
} catch { }
if ($rsOk) {
    Write-Output "Browser engine is answering on port 11926."
} else {
    Write-Output 'Browser engine not running. Optional: in Live, Settings > Link, Tempo & MIDI, set a free Control Surface slot to "LiveActionsRS", then restart Live.'
}

Write-Output ""
Write-Output "Done. Next:"
Write-Output "  1. In Live, drag User Library > Presets > Audio Effects > Max Audio Effect > Live Actions onto a track."
Write-Output "  2. Open Live Actions from the Desktop shortcut."
Write-Output "  3. Genius needs your own AI provider API key: Preferences > AI provider. The other tools work without one."
