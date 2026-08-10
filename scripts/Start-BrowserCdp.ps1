param(
    [ValidateSet("edge", "chrome")]
    [string]$Browser = "edge",

    [string]$ExecutablePath,
    [string]$ProfileSource,

    [int]$Port = 9225,
    [string]$WslHostAddress
)

$ErrorActionPreference = "Stop"
$StartupTimeoutSeconds = 20

function Resolve-BrowserExecutable {
    param([string]$Browser)

    if ($Browser -eq "edge") {
        $candidates = @(
            "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
            "${env:ProgramFiles}\Microsoft\Edge\Application\msedge.exe"
        )
    } else {
        $candidates = @(
            "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
            "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
        )
    }

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    throw "Cannot find $Browser executable. Pass -ExecutablePath explicitly."
}

function Resolve-ProfileSource {
    param([string]$Browser)

    if ($Browser -eq "edge") {
        return Join-Path $env:LOCALAPPDATA "Microsoft\Edge\User Data"
    }

    return Join-Path $env:LOCALAPPDATA "Google\Chrome\User Data"
}

function Copy-BrowserProfile {
    param(
        [string]$Source,
        [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Profile source does not exist: $Source"
    }

    if (Test-Path -LiteralPath $Destination) {
        Remove-Item -LiteralPath $Destination -Recurse -Force
    }

    New-Item -ItemType Directory -Path $Destination -Force | Out-Null

    $excludeDirs = @(
        "BrowserMetrics",
        "Crashpad",
        "GPUCache",
        "GrShaderCache",
        "ShaderCache",
        "Cache",
        "Code Cache",
        "DawnCache",
        "Service Worker",
        "Safe Browsing"
    )
    $excludeFiles = @(
        "Singleton*",
        "lockfile",
        "*.tmp"
    )

    $robocopyArgs = @(
        $Source,
        $Destination,
        "/E",
        "/R:1",
        "/W:1",
        "/NFL",
        "/NDL",
        "/NP",
        "/NJH",
        "/NJS",
        "/XD"
    ) + $excludeDirs + @("/XF") + $excludeFiles

    & robocopy @robocopyArgs | Out-Null
    if ($LASTEXITCODE -gt 7) {
        throw "robocopy failed with exit code $LASTEXITCODE"
    }
}

if (-not $ExecutablePath) {
    $ExecutablePath = Resolve-BrowserExecutable -Browser $Browser
}
if (-not (Test-Path -LiteralPath $ExecutablePath)) {
    throw "Browser executable does not exist: $ExecutablePath"
}

if (-not $ProfileSource) {
    $ProfileSource = Resolve-ProfileSource -Browser $Browser
}
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$ProfileDir = Join-Path $env:TEMP "browser-cdp-profile-$Browser-$Port-$timestamp"
Copy-BrowserProfile -Source $ProfileSource -Destination $ProfileDir

$browserArgs = @(
    "--remote-debugging-port=$Port",
    "--user-data-dir=`"$ProfileDir`"",
    "--no-first-run",
    "--no-default-browser-check"
) + @("about:blank")

$process = Start-Process -FilePath $ExecutablePath -ArgumentList $browserArgs -PassThru
$localCdpUrl = "http://127.0.0.1:$Port"
$versionUrl = "$localCdpUrl/json/version"
$deadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
$lastError = $null

while ((Get-Date) -lt $deadline) {
    try {
        Invoke-RestMethod -Uri $versionUrl -TimeoutSec 1 | Out-Null
        $lastError = $null
        break
    } catch {
        $lastError = $_
        Start-Sleep -Milliseconds 250
    }
}

if ($lastError) {
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    throw "CDP did not become ready at $versionUrl. Last error: $lastError"
}

Write-Host "Browser CDP is ready."
Write-Host "ProcessId: $($process.Id)"
Write-Host "ProfileDir: $ProfileDir"
Write-Host "Local CDP URL: $localCdpUrl"

if ($WslHostAddress) {
    $wslCdpUrl = "http://${WslHostAddress}:$Port"
    Write-Host "WSL CDP URL: $wslCdpUrl"
} else {
    Write-Host ""
    Write-Host "If WSL accesses this through a Windows portproxy, pass -WslHostAddress <windows-wsl-facing-ip>."
}

Write-Host ""
Write-Host "Stop command:"
Write-Host "Stop-Process -Id $($process.Id) -Force"
Write-Host ""
Write-Host "Cleanup command:"
Write-Host "Remove-Item -LiteralPath '$ProfileDir' -Recurse -Force"
