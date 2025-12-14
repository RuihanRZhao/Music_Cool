# NCM Decoder - Run Only Script
# Only run program, do not build

$ErrorActionPreference = "Stop"

# Get script and project directories
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "=== NCM Decoder Run Script ===" -ForegroundColor Cyan

# Check virtual environment
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    $venvPath = Join-Path $ProjectRoot ".venv"
    if (Test-Path $venvPath) {
        & (Join-Path $venvPath "Scripts\Activate.ps1")
    }
}

# Check extension module
$extensionFile = Join-Path $ProjectRoot "build\ncm_decoder.pyd"
if (-not (Test-Path $extensionFile)) {
    Write-Host "Error: Extension module not found" -ForegroundColor Red
    Write-Host "Please run build script first: .\scripts\build_only.ps1" -ForegroundColor Yellow
    exit 1
}

# Check main program
$mainScript = Join-Path $ProjectRoot "src\python\main.py"
if (-not (Test-Path $mainScript)) {
    Write-Host "Error: Main program not found" -ForegroundColor Red
    exit 1
}

# Run program
Write-Host "Starting program..." -ForegroundColor Green
Push-Location $ProjectRoot
python $mainScript
Pop-Location
