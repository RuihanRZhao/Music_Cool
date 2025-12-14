# NCM Decoder - Build and Run Script
# Auto: clean, configure, compile, copy, run

param(
    [switch]$SkipBuild = $false,
    [switch]$Clean = $false
)

$ErrorActionPreference = "Stop"

# Get script and project directories
# Script is in scripts/develop/, so we need to go up 2 levels to reach project root
$ScriptPath = $MyInvocation.MyCommand.Path
$ScriptDir = Split-Path -Parent $ScriptPath
$ScriptsDir = Split-Path -Parent $ScriptDir
$ProjectRoot = Split-Path -Parent $ScriptsDir

Write-Host "=== NCM Decoder Build and Run Script ===" -ForegroundColor Cyan
Write-Host "Project Directory: $ProjectRoot" -ForegroundColor Gray

# Check virtual environment
if (-not $env:VIRTUAL_ENV) {
    Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
    $venvPath = Join-Path $ProjectRoot ".venv"
    if (Test-Path $venvPath) {
        & (Join-Path $venvPath "Scripts\Activate.ps1")
    } else {
        Write-Host "Warning: Virtual environment not found, using system Python" -ForegroundColor Yellow
    }
}

# Check Python dependencies
Write-Host "`n[1/5] Checking Python dependencies..." -ForegroundColor Yellow

# Check and install pybind11
$pybind11Check = python -c "import pybind11" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing pybind11..." -ForegroundColor Yellow
    pip install pybind11
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install pybind11" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "pybind11 is installed" -ForegroundColor Green
}

# Check and install PyQt6
$pyqt6Check = python -c "import PyQt6" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing PyQt6..." -ForegroundColor Yellow
    pip install PyQt6
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install PyQt6" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "PyQt6 is installed" -ForegroundColor Green
}

# Check CMake
Write-Host "`n[2/5] Checking build tools..." -ForegroundColor Yellow
$cmake = Get-Command cmake -ErrorAction SilentlyContinue
if (-not $cmake) {
    Write-Host "Error: CMake not found, please install CMake" -ForegroundColor Red
    Write-Host "Install: winget install Kitware.CMake" -ForegroundColor Yellow
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

# Build C++ extension module
if (-not $SkipBuild) {
    Write-Host "`n[3/5] Building C++ extension module..." -ForegroundColor Yellow
    
    $cppDir = Join-Path $ProjectRoot "src\cpp"
    $buildDir = Join-Path $cppDir "build"
    
    # Clean if needed
    if ($Clean) {
        Write-Host "Cleaning build directory..." -ForegroundColor Gray
        if (Test-Path $buildDir) {
            Remove-Item $buildDir -Recurse -Force
        }
    }
    
    # Create build directory
    if (-not (Test-Path $buildDir)) {
        New-Item -ItemType Directory -Path $buildDir | Out-Null
    }
    
    Push-Location $buildDir
    
    # Configure CMake
    Write-Host "Configuring CMake..." -ForegroundColor Gray
    
    # Get Python executable path (should be from venv)
    $pythonExe = (Get-Command python).Source
    Write-Host "Using Python: $pythonExe" -ForegroundColor Gray
    
    # Get pybind11 CMake directory and normalize path
    $pybind11Dir = python -c "import pybind11; print(pybind11.get_cmake_dir())" 2>&1
    if ($LASTEXITCODE -eq 0 -and $pybind11Dir) {
        $pybind11Dir = $pybind11Dir.Trim()
        # Convert to Windows path format
        $pybind11Dir = $pybind11Dir -replace '/', '\'
        Write-Host "pybind11 CMake dir: $pybind11Dir" -ForegroundColor Gray
        
        # Verify the directory exists
        if (-not (Test-Path $pybind11Dir)) {
            Write-Host "Warning: pybind11 CMake dir does not exist: $pybind11Dir" -ForegroundColor Yellow
            $pybind11Dir = $null
        }
    } else {
        Write-Host "Warning: Could not get pybind11 CMake dir" -ForegroundColor Yellow
        $pybind11Dir = $null
    }
    
    # Build CMake command
    $cmakeArgs = @("..", "-G")
    if ($useMingw) {
        $cmakeArgs += "MinGW Makefiles"
    } else {
        $cmakeArgs += "Visual Studio 17 2022", "-A", "x64"
    }
    
    # Add pybind11 directory if found
    if ($pybind11Dir) {
        $cmakeArgs += "-Dpybind11_DIR=$pybind11Dir"
        $cmakeArgs += "-DCMAKE_PREFIX_PATH=$pybind11Dir"
    }
    
    # Also set Python executable explicitly
    $cmakeArgs += "-DPython3_EXECUTABLE=$pythonExe"
    
    Write-Host "CMake command: cmake $($cmakeArgs -join ' ')" -ForegroundColor Gray
    & cmake $cmakeArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "CMake configuration failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    # Compile
    Write-Host "Compiling C++ extension module..." -ForegroundColor Gray
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
    Write-Host "`n[4/5] Copying extension module..." -ForegroundColor Yellow
    $projectBuildDir = Join-Path $ProjectRoot "build"
    if (-not (Test-Path $projectBuildDir)) {
        New-Item -ItemType Directory -Path $projectBuildDir | Out-Null
    }
    
    # pybind11 generates files with version suffix (e.g., ncm_decoder.cp310-win_amd64.pyd)
    # The output directory is set to ../../build in CMakeLists.txt
    # So the file should already be in the project build directory
    $extensionPattern = Join-Path $projectBuildDir "ncm_decoder*.pyd"
    $extensionFiles = Get-ChildItem -Path $extensionPattern -ErrorAction SilentlyContinue
    
    if ($extensionFiles) {
        # Filter out ncm_decoder.pyd (target file) - only keep versioned files
        $versionedFiles = $extensionFiles | Where-Object { $_.Name -ne "ncm_decoder.pyd" }
        
        if ($versionedFiles) {
            # Find the most recent versioned file
            $extensionFile = $versionedFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            $targetPath = Join-Path $projectBuildDir "ncm_decoder.pyd"
            
            # Only copy if source and target are different files
            if ($extensionFile.FullName -ne $targetPath) {
                Copy-Item $extensionFile.FullName $targetPath -Force
                Write-Host "Extension module copied: $targetPath" -ForegroundColor Green
                Write-Host "  (from: $($extensionFile.Name))" -ForegroundColor Gray
            } else {
                Write-Host "Extension module already at target location: $targetPath" -ForegroundColor Green
            }
        } else {
            # No versioned files found, check if ncm_decoder.pyd already exists
            $targetPath = Join-Path $projectBuildDir "ncm_decoder.pyd"
            if (Test-Path $targetPath) {
                Write-Host "Extension module already exists: $targetPath" -ForegroundColor Green
            } else {
                Write-Host "Warning: No versioned extension files found" -ForegroundColor Yellow
            }
        }
        Write-Host "Extension module copied: $targetPath" -ForegroundColor Green
        Write-Host "  (from: $($extensionFile.Name))" -ForegroundColor Gray
    } else {
        # Fallback: check in build directory (for older builds or different configs)
        if ($useMingw) {
            $extensionPattern = Join-Path $buildDir "ncm_decoder*.pyd"
            $extensionFiles = Get-ChildItem -Path $extensionPattern -ErrorAction SilentlyContinue
        } else {
            $extensionPattern = Join-Path $buildDir "Release\ncm_decoder*.pyd"
            $extensionFiles = Get-ChildItem -Path $extensionPattern -ErrorAction SilentlyContinue
        }
        
        if ($extensionFiles) {
            # Filter out ncm_decoder.pyd (target file) - only keep versioned files
            $versionedFiles = $extensionFiles | Where-Object { $_.Name -ne "ncm_decoder.pyd" }
            
            if ($versionedFiles) {
                $extensionFile = $versionedFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
                $targetPath = Join-Path $projectBuildDir "ncm_decoder.pyd"
                
                # Only copy if source and target are different files
                if ($extensionFile.FullName -ne $targetPath) {
                    Copy-Item $extensionFile.FullName $targetPath -Force
                    Write-Host "Extension module copied: $targetPath" -ForegroundColor Green
                    Write-Host "  (from: $($extensionFile.FullName))" -ForegroundColor Gray
                } else {
                    Write-Host "Extension module already at target location: $targetPath" -ForegroundColor Green
                }
            } else {
                # No versioned files found, check if target already exists
                $targetPath = Join-Path $projectBuildDir "ncm_decoder.pyd"
                if (Test-Path $targetPath) {
                    Write-Host "Extension module already exists: $targetPath" -ForegroundColor Green
                } else {
                    Write-Host "Warning: No versioned extension files found in fallback location" -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "Warning: Compiled extension module not found" -ForegroundColor Yellow
            Write-Host "Searched in:" -ForegroundColor Gray
            Write-Host "  - $projectBuildDir" -ForegroundColor Gray
            Write-Host "  - $buildDir" -ForegroundColor Gray
            exit 1
        }
    }
} else {
    Write-Host "`n[3/5] Skipping build (using --SkipBuild parameter)" -ForegroundColor Gray
    Write-Host "`n[4/5] Checking extension module..." -ForegroundColor Yellow
    $extensionFile = Join-Path $ProjectRoot "build\ncm_decoder.pyd"
    if (-not (Test-Path $extensionFile)) {
        Write-Host "Error: Extension module not found, please build first" -ForegroundColor Red
        exit 1
    }
}

# Run program
Write-Host "`n[5/5] Starting program..." -ForegroundColor Yellow
$mainScript = Join-Path $ProjectRoot "src\python\main.py"

if (-not (Test-Path $mainScript)) {
    Write-Host "Error: Main program not found: $mainScript" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Starting NCM Decoder ===" -ForegroundColor Green
Push-Location $ProjectRoot
python $mainScript
Pop-Location
