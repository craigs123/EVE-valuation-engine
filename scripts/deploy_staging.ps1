#requires -Version 5.1
# PowerShell wrapper for scripts/deploy_staging.sh.
#
# 1. Runs the bash deploy script (rebuilds image, redeploys service + Job).
# 2. Starts `gcloud run services proxy` in a new PowerShell window if nothing
#    is already listening on the proxy port.
# 3. Opens http://localhost:<port> in the default browser.
#
# Usage:
#   .\scripts\deploy_staging.ps1            # default port 8080
#   .\scripts\deploy_staging.ps1 -Port 8090
#   .\scripts\deploy_staging.ps1 -SkipDeploy # just open the proxy + browser

param(
    [int]$Port = 8080,
    [switch]$SkipDeploy
)

$ErrorActionPreference = 'Stop'

$ProjectId = 'eve-solutions-482317'
$Region    = 'us-central1'
$Service   = 'eve-valuation-engine-staging'

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (-not $SkipDeploy) {
    Write-Host "=== Running bash scripts/deploy_staging.sh ===" -ForegroundColor Cyan
    bash scripts/deploy_staging.sh
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Deploy failed (exit $LASTEXITCODE). Not opening proxy." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Write-Host ""
Write-Host "=== Checking for existing proxy on port $Port ===" -ForegroundColor Cyan
$portInUse = $false
try {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
    if ($listener) { $portInUse = $true }
} catch {
    $portInUse = $false
}

if ($portInUse) {
    Write-Host "Port $Port already has a listener -- reusing it." -ForegroundColor Yellow
} else {
    Write-Host "Starting proxy in a new window..." -ForegroundColor Cyan
    $proxyCmd = "gcloud run services proxy $Service --region $Region --project $ProjectId --port $Port"
    Start-Process powershell -ArgumentList @(
        '-NoExit',
        '-Command',
        "Write-Host 'Staging proxy: http://localhost:$Port' -ForegroundColor Green; $proxyCmd"
    )
    # Give the proxy a moment to bind the port before launching the browser.
    Start-Sleep -Seconds 3
}

$url = "http://localhost:$Port"
Write-Host ""
Write-Host "Opening $url" -ForegroundColor Green
Start-Process $url
