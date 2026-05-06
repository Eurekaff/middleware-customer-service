param(
    [switch]$UseDockerRedis
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Step($Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Ensure-PythonVenv($ProjectDir, $RequirementsFile) {
    $VenvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
    if (!(Test-Path $VenvPython)) {
        Step "Create Python venv: $ProjectDir"
        python -m venv (Join-Path $ProjectDir ".venv")
    }

    Step "Install Python requirements: $RequirementsFile"
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r $RequirementsFile
}

Step "Prepare .env"
if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example. Fill LLM_API_KEY only if you need real LLM calls."
} else {
    Write-Host ".env already exists, skipped."
}

Step "Prepare Redis"
if ($UseDockerRedis) {
    docker compose up -d redis
} else {
    $redisService = Get-Service Redis -ErrorAction SilentlyContinue
    if ($redisService) {
        if ($redisService.Status -ne "Running") {
            Start-Service Redis
        }
        Write-Host "Redis service is running."
    } elseif (Get-Command docker -ErrorAction SilentlyContinue) {
        Write-Host "Redis Windows service not found. Starting Redis by docker compose."
        docker compose up -d redis
    } else {
        Write-Host "Redis service not found. Install Redis or Docker, then run setup again." -ForegroundColor Yellow
        Write-Host "Windows install command: winget install --id Redis.Redis -e --accept-package-agreements --accept-source-agreements"
    }
}

Ensure-PythonVenv (Join-Path $Root "backend") (Join-Path $Root "backend\requirements.txt")
Ensure-PythonVenv (Join-Path $Root "worker") (Join-Path $Root "worker\requirements.txt")
Ensure-PythonVenv (Join-Path $Root "mcp_server") (Join-Path $Root "mcp_server\requirements.txt")

Step "Install frontend dependencies"
Set-Location (Join-Path $Root "frontend")
npm install
Set-Location $Root

Step "Setup complete"
Write-Host "Next: powershell -ExecutionPolicy Bypass -File scripts\start.ps1"
