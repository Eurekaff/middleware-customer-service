$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$RunDir = Join-Path $Root ".run"

function Stop-ManagedProcess($Name) {
    $pidFile = Join-Path $RunDir "$Name.pid"
    if (!(Test-Path $pidFile)) {
        Write-Host "$Name pid file not found, skipped."
        return
    }

    $pidValue = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($pidValue -and (Get-Process -Id $pidValue -ErrorAction SilentlyContinue)) {
        Stop-Process -Id $pidValue -Force
        Write-Host "$Name stopped, pid=$pidValue"
    } else {
        Write-Host "$Name process not running."
    }

    Remove-Item $pidFile -ErrorAction SilentlyContinue
}

Stop-ManagedProcess "frontend"
Stop-ManagedProcess "worker"
Stop-ManagedProcess "mcp"
Stop-ManagedProcess "backend"

Write-Host "Managed services stopped."
