param(
    [switch]$UseDockerRedis
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$needSetup = $false
if (!(Test-Path ".env")) { $needSetup = $true }
if (!(Test-Path "backend\.venv\Scripts\python.exe")) { $needSetup = $true }
if (!(Test-Path "worker\.venv\Scripts\python.exe")) { $needSetup = $true }
if (!(Test-Path "mcp_server\.venv\Scripts\python.exe")) { $needSetup = $true }
if (!(Test-Path "frontend\node_modules")) { $needSetup = $true }

if ($needSetup) {
    Write-Host "First run detected. Running setup..." -ForegroundColor Cyan
    if ($UseDockerRedis) {
        & (Join-Path $PSScriptRoot "setup.ps1") -UseDockerRedis
    } else {
        & (Join-Path $PSScriptRoot "setup.ps1")
    }
} else {
    Write-Host "Dependencies found. Skipping setup." -ForegroundColor Green
}

if ($UseDockerRedis) {
    & (Join-Path $PSScriptRoot "start.ps1") -UseDockerRedis
} else {
    & (Join-Path $PSScriptRoot "start.ps1")
}
