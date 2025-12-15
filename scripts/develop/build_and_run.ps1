# Music_Cool - Build C++ Core and Run Tauri Dev
# 构建 C++ 解码核心静态库并启动 Tauri 开发环境
# 示例: .\scripts\develop\build_and_run.ps1

param(
    [switch]$SkipBuild = $false,
    [switch]$Clean     = $false
)

$ErrorActionPreference = "Stop"

$ScriptPath  = $MyInvocation.MyCommand.Path
$ScriptDir   = Split-Path -Parent $ScriptPath
$ScriptsDir  = Split-Path -Parent $ScriptDir
$ProjectRoot = Split-Path -Parent $ScriptsDir

Write-Host "=== Music_Cool - Build C++ Core & Run Tauri Dev ===" -ForegroundColor Cyan
Write-Host "Project Directory: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

# -------------------------------------------------------------
# 1. 构建 C++ 静态库（如果未跳过）
# -------------------------------------------------------------
if (-not $SkipBuild) {
    Write-Host "[1/2] Building C++ static library..." -ForegroundColor Yellow
    & "$ScriptDir\build_only.ps1" -Clean:$Clean
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: C++ build failed" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
} else {
    Write-Host "[1/2] Skipping C++ build (--SkipBuild specified)" -ForegroundColor Gray
    Write-Host ""
}

# -------------------------------------------------------------
# 2. 启动 Tauri 开发环境
# -------------------------------------------------------------
Write-Host "[2/2] Starting Tauri dev..." -ForegroundColor Yellow
& "$ScriptDir\run_only.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Tauri dev failed" -ForegroundColor Red
    exit 1
}
