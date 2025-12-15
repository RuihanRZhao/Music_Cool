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

# -------------------------------------------------------------
# 1. 构建 C++ 静态库（如果未跳过）
# -------------------------------------------------------------
if (-not $SkipBuild) {

    $cmake = Get-Command cmake -ErrorAction SilentlyContinue
    if (-not $cmake) {
        Write-Host "Error: CMake not found" -ForegroundColor Red
        exit 1
    }

    $vsGenerator = $null
    $vsVersion = $null

    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vswhere) {
        $vsPath = & $vswhere -latest -property installationPath -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 2>$null
        if ($vsPath -and (Test-Path $vsPath)) {

            if ($vsPath -match "\\18\\" -or $vsPath -match "\\2026\\") {
                $vsVersion = "2026"
                $vsGenerator = "Visual Studio 18 2026"
            } elseif ($vsPath -match "\\2022\\") {
                $vsVersion = "2022"
                $vsGenerator = "Visual Studio 17 2022"
            } elseif ($vsPath -match "\\2019\\") {
                $vsVersion = "2019"
                $vsGenerator = "Visual Studio 16 2019"
            } elseif ($vsPath -match "\\2017\\") {
                $vsVersion = "2017"
                $vsGenerator = "Visual Studio 15 2017"
            } else {

                $catalogPath = Join-Path $vsPath "catalog.json"
                if (Test-Path $catalogPath) {
                    try {
                        $catalog = Get-Content $catalogPath -Raw | ConvertFrom-Json
                        if ($catalog.productLineVersion) {
                            $majorVersion = [int]($catalog.productLineVersion -split '\.')[0]
                            if ($majorVersion -ge 18) {
                                $vsGenerator = "Visual Studio 18 2026"
                            } elseif ($majorVersion -ge 17) {
                                $vsGenerator = "Visual Studio 17 2022"
                            } elseif ($majorVersion -eq 16) {
                                $vsGenerator = "Visual Studio 16 2019"
                            } elseif ($majorVersion -eq 15) {
                                $vsGenerator = "Visual Studio 15 2017"
                            }
                        }
                    } catch {

                    }
                }
            }
        }
    }

    if (-not $vsGenerator) {
        $vsPaths = @(
            @{ Path = "${env:ProgramFiles}\Microsoft Visual Studio\18"; Version = "2026"; Generator = "Visual Studio 18 2026" },
            @{ Path = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\18"; Version = "2026"; Generator = "Visual Studio 18 2026" },
            @{ Path = "${env:ProgramFiles}\Microsoft Visual Studio\2022"; Version = "2022"; Generator = "Visual Studio 17 2022" },
            @{ Path = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022"; Version = "2022"; Generator = "Visual Studio 17 2022" },
            @{ Path = "${env:ProgramFiles}\Microsoft Visual Studio\2019"; Version = "2019"; Generator = "Visual Studio 16 2019" },
            @{ Path = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2019"; Version = "2019"; Generator = "Visual Studio 16 2019" },
            @{ Path = "${env:ProgramFiles}\Microsoft Visual Studio\2017"; Version = "2017"; Generator = "Visual Studio 15 2017" },
            @{ Path = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2017"; Version = "2017"; Generator = "Visual Studio 15 2017" }
        )

        foreach ($vsInfo in $vsPaths) {
            $editions = @("Community", "Professional", "Enterprise", "BuildTools")
            foreach ($edition in $editions) {
                $testPath = Join-Path $vsInfo.Path $edition
                if (Test-Path $testPath) {
                    $vsGenerator = $vsInfo.Generator
                    $vsVersion = $vsInfo.Version
                    break
                }
            }
            if ($vsGenerator) { break }
        }
    }

    if (-not $vsGenerator) {
        $cl = Get-Command cl -ErrorAction SilentlyContinue
        if ($cl) {

            Write-Host "Warning: Found cl.exe but could not determine Visual Studio version." -ForegroundColor Yellow
            Write-Host "Attempting to use 'Visual Studio 18 2026' generator..." -ForegroundColor Yellow
            $vsGenerator = "Visual Studio 18 2026"
        }
    }

    if (-not $vsGenerator) {
        Write-Host "Error: Visual Studio (MSVC) not found!" -ForegroundColor Red
        Write-Host "This project requires Visual Studio with C++ development tools." -ForegroundColor Yellow
        Write-Host "Please install Visual Studio (2017/2019/2022/2026) with:" -ForegroundColor Yellow
        Write-Host "  - Desktop development with C++ workload" -ForegroundColor Yellow
        Write-Host "  - MSVC C++ build tools" -ForegroundColor Yellow
        exit 1
    }

    Write-Host "Using Visual Studio (MSVC) toolchain" -ForegroundColor Green
    if ($vsVersion) {
        Write-Host "Detected Visual Studio $vsVersion, using generator: $vsGenerator" -ForegroundColor Cyan
    } else {
        Write-Host "Using generator: $vsGenerator" -ForegroundColor Cyan
    }

    $cppDir   = Join-Path $ProjectRoot "src\cpp"
    $buildDir = Join-Path $cppDir "build"

    if ($Clean) {
        Write-Host "Cleaning C++ build directory..." -ForegroundColor Yellow
        if (Test-Path $buildDir) {
            Remove-Item $buildDir -Recurse -Force
        }
    }

    if (-not (Test-Path $buildDir)) {
        New-Item -ItemType Directory -Path $buildDir | Out-Null
    }

    Push-Location $buildDir

    if (Test-Path "CMakeCache.txt") {
        Remove-Item CMakeCache.txt -Force
        if (Test-Path "CMakeFiles") {
            Remove-Item CMakeFiles -Recurse -Force
        }
    }

    Write-Host "[1/3] Configuring CMake for C++ decoder core..." -ForegroundColor Yellow
    cmake .. -G $vsGenerator -A x64 -DBUILD_PYTHON_BINDINGS=OFF

    if ($LASTEXITCODE -ne 0) {
        Write-Host "CMake configuration failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }

    Write-Host "[2/3] Building static library target 'ncm_decoder_static'..." -ForegroundColor Yellow
    cmake --build . --config Release --target ncm_decoder_static

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Compilation failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }

    Pop-Location

    $projectBuildDir = Join-Path $ProjectRoot "build"
    Write-Host "C++ static library build completed." -ForegroundColor Green
}
# -------------------------------------------------------------
# 2. 检查开发工具 & 自动安装前端依赖
# -------------------------------------------------------------
Write-Host "[2/3] Checking development tools..." -ForegroundColor Yellow

$cargo = Get-Command cargo -ErrorAction SilentlyContinue
if (-not $cargo) {
    Write-Host "Error: cargo (Rust) not found" -ForegroundColor Red
    exit 1
}

$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Host "Warning: Node.js not found. Frontend build may fail." -ForegroundColor Yellow
} else {
    $frontendDir = Join-Path $ProjectRoot "src-tauri\frontend"
    $frontendPkg = Join-Path $frontendDir "package.json"
    $frontendNodeModules = Join-Path $frontendDir "node_modules"

    if (Test-Path $frontendPkg) {


        Write-Host "Ensuring frontend dependencies are installed..." -ForegroundColor Yellow
        Push-Location $frontendDir
        try {
            npm install
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Error: npm install failed" -ForegroundColor Red
                exit 1
            }
        } finally {
            Pop-Location
        }
    }
}

# -------------------------------------------------------------
# 3. 启动 Tauri 开发环境
# -------------------------------------------------------------
Write-Host "[3/3] Starting Tauri dev..." -ForegroundColor Yellow

$tauriDir = Join-Path $ProjectRoot "src-tauri"
if (-not (Test-Path $tauriDir)) {
    Write-Host "Error: Tauri directory not found: $tauriDir" -ForegroundColor Red
    exit 1
}

Push-Location $tauriDir

$localTauriCli = Join-Path "frontend" "node_modules" | Join-Path -ChildPath ".bin" | Join-Path -ChildPath "tauri.cmd"

if (Test-Path $localTauriCli) {
    Write-Host "Using local Tauri CLI: $localTauriCli" -ForegroundColor Cyan
    & $localTauriCli dev
} else {
    Write-Host "Warning: Local Tauri CLI not found at $localTauriCli" -ForegroundColor Yellow
    Write-Host "Falling back to npm run tauri (may fail if CWD issue)" -ForegroundColor Yellow

    npm run --prefix frontend tauri -- dev
}

Pop-Location