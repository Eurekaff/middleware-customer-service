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

function Set-EnvValue($Path, $Key, $Value) {
    $escapedValue = $Value -replace '\$', '`$'
    $lines = Get-Content $Path
    $found = $false
    $updated = foreach ($line in $lines) {
        if ($line -match "^$Key=") {
            $found = $true
            "$Key=$escapedValue"
        } else {
            $line
        }
    }

    if (!$found) {
        $updated += "$Key=$escapedValue"
    }

    Set-Content -Path $Path -Value $updated -Encoding UTF8
}

function Configure-Llm($EnvPath) {
    Write-Host ""
    Write-Host "LLM is optional. Press Enter to keep local rule/template mode." -ForegroundColor Yellow
    $enable = Read-Host "Enable Alibaba DashScope LLM? (y/N)"
    if ($enable -notin @("y", "Y", "yes", "YES")) {
        Set-EnvValue $EnvPath "LLM_ENABLE" "false"
        Set-EnvValue $EnvPath "LLM_API_KEY" ""
        Write-Host "LLM disabled. The project will run with local rules and templates."
        return
    }

    $apiKey = Read-Host "Input DashScope API Key"
    if ([string]::IsNullOrWhiteSpace($apiKey)) {
        Set-EnvValue $EnvPath "LLM_ENABLE" "false"
        Set-EnvValue $EnvPath "LLM_API_KEY" ""
        Write-Host "No API Key provided. LLM disabled."
        return
    }

    Set-EnvValue $EnvPath "LLM_ENABLE" "true"
    Set-EnvValue $EnvPath "LLM_API_KEY" $apiKey.Trim()
    Set-EnvValue $EnvPath "LLM_BASE_URL" "https://dashscope.aliyuncs.com/compatible-mode/v1"
    Set-EnvValue $EnvPath "LLM_MODEL" "qwen-plus"
    Set-EnvValue $EnvPath "LLM_TIMEOUT_SECONDS" "20"
    Write-Host "LLM enabled with Alibaba DashScope compatible API."
}

Step "Prepare .env"
if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example."
    Configure-Llm (Join-Path $Root ".env")
} else {
    Write-Host ".env already exists, skipped. Edit .env manually if you need to change LLM settings."
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
