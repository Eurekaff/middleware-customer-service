param(
    [switch]$UseDockerRedis
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$RunDir = Join-Path $Root ".run"
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
Set-Location $Root

function Step($Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Test-Http($Url, $Name) {
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
        Write-Host "$Name OK: $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "$Name not ready: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

function Test-PortInUse($Port) {
    $matches = netstat -ano | Select-String ":$Port"
    foreach ($match in $matches) {
        if ($match.Line -match "LISTENING") {
            return $true
        }
    }
    return $false
}

function Ensure-Redis {
    Step "Check Redis"
    if ($UseDockerRedis) {
        docker compose up -d redis
    } else {
        $redisService = Get-Service Redis -ErrorAction SilentlyContinue
        if ($redisService -and $redisService.Status -ne "Running") {
            Start-Service Redis
        } elseif (!$redisService -and (Get-Command docker -ErrorAction SilentlyContinue)) {
            docker compose up -d redis
        }
    }

    $redisCli = "redis-cli"
    $windowsRedisCli = "C:\Program Files\Redis\redis-cli.exe"
    if (Test-Path $windowsRedisCli) {
        $redisCli = $windowsRedisCli
    }

    try {
        $pong = & $redisCli ping
        if ($pong -ne "PONG") {
            throw "Redis ping returned $pong"
        }
        Write-Host "Redis OK: PONG" -ForegroundColor Green
    } catch {
        Write-Host "Redis is not reachable. Start Redis first or run scripts\setup.ps1 -UseDockerRedis." -ForegroundColor Red
        throw
    }
}

function Start-ManagedProcess($Name, $FilePath, $ArgumentList, $WorkingDirectory, $Port = 0) {
    $pidFile = Join-Path $RunDir "$Name.pid"
    if (Test-Path $pidFile) {
        $oldPid = Get-Content $pidFile -ErrorAction SilentlyContinue
        if ($oldPid -and (Get-Process -Id $oldPid -ErrorAction SilentlyContinue)) {
            Write-Host "$Name already running, pid=$oldPid"
            return
        }
    }

    if ($Port -and (Test-PortInUse $Port)) {
        Write-Host "$Name port $Port is already in use. Reuse the existing service or stop it first." -ForegroundColor Yellow
        return
    }

    $outLog = Join-Path $Root "run-$Name.out.log"
    $errLog = Join-Path $Root "run-$Name.err.log"
    Remove-Item $outLog, $errLog -ErrorAction SilentlyContinue

    Step "Start $Name"
    $process = Start-Process `
        -FilePath $FilePath `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory `
        -PassThru `
        -WindowStyle Hidden `
        -RedirectStandardOutput $outLog `
        -RedirectStandardError $errLog

    Set-Content -Path $pidFile -Value $process.Id
    Write-Host "$Name started, pid=$($process.Id), logs: run-$Name.out.log / run-$Name.err.log"
}

Ensure-Redis

$backendPython = Join-Path $Root "backend\.venv\Scripts\python.exe"
$workerPython = Join-Path $Root "worker\.venv\Scripts\python.exe"
$mcpPython = Join-Path $Root "mcp_server\.venv\Scripts\python.exe"

if (!(Test-Path $backendPython) -or !(Test-Path $workerPython) -or !(Test-Path $mcpPython) -or !(Test-Path (Join-Path $Root "frontend\node_modules"))) {
    Write-Host "Dependencies are missing. Run scripts\setup.ps1 first." -ForegroundColor Red
    exit 1
}

Start-ManagedProcess "backend" $backendPython @("-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000") (Join-Path $Root "backend") 8000
Start-ManagedProcess "worker" $workerPython @("worker.py") (Join-Path $Root "worker")

# The current worker uses local MCP tool wrappers for stable class demo.
# mcp_server is still started so the real MCP entry is available for inspection or future MCP Client replacement.
Start-ManagedProcess "mcp" $mcpPython @("server.py") (Join-Path $Root "mcp_server")

Start-ManagedProcess "frontend" "npm.cmd" @("run", "dev", "--", "--host", "127.0.0.1", "--port", "5173") (Join-Path $Root "frontend") 5173

Start-Sleep -Seconds 5
Step "Health check"
Test-Http "http://127.0.0.1:8000/api/health" "Backend"
Test-Http "http://127.0.0.1:5173/" "Frontend"

Write-Host ""
Write-Host "Open chat page:  http://127.0.0.1:5173" -ForegroundColor Green
Write-Host "Open admin page: http://127.0.0.1:5173/admin" -ForegroundColor Green
Write-Host "Stop services:   powershell -ExecutionPolicy Bypass -File scripts\stop.ps1"
