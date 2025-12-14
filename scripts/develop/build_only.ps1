# NCM Decoder - Build Only Script
# Only build C++ extension module, do not run

param(
    [switch]$Clean = $false
)

$ErrorActionPreference = "Stop"

# Get script and project directories
# Script is in scripts/develop/, so we need to go up 2 levels to reach project root
$ScriptPath = $MyInvocation.MyCommand.Path
$ScriptDir = Split-Path -Parent $ScriptPath
$ScriptsDir = Split-Path -Parent $ScriptDir
$ProjectRoot = Split-Path -Parent $ScriptsDir

Write-Host "=== NCM Decoder Build Script ===" -ForegroundColor Cyan

# Check CMake
$cmake = Get-Command cmake -ErrorAction SilentlyContinue
if (-not $cmake) {
    Write-Host "Error: CMake not found" -ForegroundColor Red
    exit 1
}

# Check compiler
$gcc = Get-Command gcc -ErrorAction SilentlyContinue
$mingw32_make = Get-Command mingw32-make -ErrorAction SilentlyContinue

if (-not $gcc -or -not $mingw32_make) {
    Write-Host "Warning: MinGW-w64 not found, trying Visual Studio" -ForegroundColor Yellow
    $useMingw = $false
} else {
    $useMingw = $true
    Write-Host "Using MinGW-w64 compiler" -ForegroundColor Green
}

# Build
$cppDir = Join-Path $ProjectRoot "src\cpp"
$buildDir = Join-Path $cppDir "build"

# Clean
if ($Clean) {
    Write-Host "Cleaning build directory..." -ForegroundColor Yellow
    if (Test-Path $buildDir) {
        Remove-Item $buildDir -Recurse -Force
    }
}

# Create build directory
if (-not (Test-Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir | Out-Null
}

Push-Location $buildDir

# Clean CMake cache if exists
if (Test-Path "CMakeCache.txt") {
    Write-Host "Cleaning CMake cache..." -ForegroundColor Gray
    Remove-Item CMakeCache.txt -Force
    if (Test-Path "CMakeFiles") {
        Remove-Item CMakeFiles -Recurse -Force
    }
}

# Configure CMake
Write-Host "Configuring CMake..." -ForegroundColor Yellow
if ($useMingw) {
    cmake .. -G "MinGW Makefiles"
} else {
    cmake .. -G "Visual Studio 17 2022" -A x64
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "CMake configuration failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Compile
Write-Host "Compiling C++ extension module..." -ForegroundColor Yellow
if ($useMingw) {
    mingw32-make -j4
} else {
    cmake --build . --config Release
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Compilation failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location

# Copy extension module
Write-Host "Copying extension module..." -ForegroundColor Yellow
$projectBuildDir = Join-Path $ProjectRoot "build"
if (-not (Test-Path $projectBuildDir)) {
    New-Item -ItemType Directory -Path $projectBuildDir | Out-Null
}

if ($useMingw) {
    $extensionFile = Join-Path $buildDir "ncm_decoder.pyd"
} else {
    $extensionFile = Join-Path $buildDir "Release\ncm_decoder.pyd"
}

if (Test-Path $extensionFile) {
    Copy-Item $extensionFile $projectBuildDir -Force
    Write-Host "`nBuild complete! Extension module: $projectBuildDir\ncm_decoder.pyd" -ForegroundColor Green
} else {
    Write-Host "Error: Compiled extension module not found" -ForegroundColor Red
    Write-Host "Expected location: $extensionFile" -ForegroundColor Gray
    exit 1
}
