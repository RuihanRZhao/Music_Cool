# Music_Cool - Build C++ Static Library Only
# 仅构建 C++ 解码核心静态库（供 Tauri 版本使用），不运行程序
# 示例: .\scripts\develop\build_only.ps1 -Clean

param(
    [switch]$Clean = $false
)

$ErrorActionPreference = "Stop"

# 计算项目根目录（scripts/develop/*.ps1 -> scripts -> project root）
$ScriptPath  = $MyInvocation.MyCommand.Path
$ScriptDir   = Split-Path -Parent $ScriptPath
$ScriptsDir  = Split-Path -Parent $ScriptDir
$ProjectRoot = Split-Path -Parent $ScriptsDir

Write-Host "=== Music_Cool - Build C++ Static Library ===" -ForegroundColor Cyan
Write-Host "Project Directory: $ProjectRoot" -ForegroundColor Gray

# 检查 CMake
$cmake = Get-Command cmake -ErrorAction SilentlyContinue
if (-not $cmake) {
    Write-Host "Error: CMake not found" -ForegroundColor Red
    Write-Host "Please install CMake (e.g. winget install Kitware.CMake)" -ForegroundColor Yellow
    exit 1
}

# 检测 Visual Studio (MSVC) 并确定 CMake 生成器
$vsGenerator = $null
$vsVersion = $null

# 方法1: 使用 vswhere 查找 Visual Studio（最可靠）
$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path $vswhere) {
    $vsPath = & $vswhere -latest -property installationPath -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 2>$null
    if ($vsPath -and (Test-Path $vsPath)) {
            # 从安装路径提取版本信息
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
            # 尝试从 catalog.json 读取版本
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
                    # 忽略解析错误
                }
            }
        }
    }
}

# 方法2: 检查常见的 Visual Studio 安装路径（如果 vswhere 未找到）
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

# 方法3: 检查 cl.exe 是否在 PATH 中（如果前两种方法都失败，至少确认有 MSVC）
if (-not $vsGenerator) {
    $cl = Get-Command cl -ErrorAction SilentlyContinue
    if ($cl) {
        # 有 cl.exe 但没有找到安装路径，尝试默认生成器
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

# 构建目录
$cppDir   = Join-Path $ProjectRoot "src\cpp"
$buildDir = Join-Path $cppDir "build"

# 清理
if ($Clean) {
    Write-Host "Cleaning C++ build directory..." -ForegroundColor Yellow
    if (Test-Path $buildDir) {
        Remove-Item $buildDir -Recurse -Force
    }
}

# 创建构建目录
if (-not (Test-Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir | Out-Null
}

Push-Location $buildDir

# 清理 CMake 缓存
if (Test-Path "CMakeCache.txt") {
    Write-Host "Cleaning CMake cache..." -ForegroundColor Gray
    Remove-Item CMakeCache.txt -Force
    if (Test-Path "CMakeFiles") {
        Remove-Item CMakeFiles -Recurse -Force
    }
}

# 配置 CMake（只构建静态库，使用检测到的 Visual Studio 生成器）
Write-Host "Configuring CMake for C++ decoder core..." -ForegroundColor Yellow
cmake .. -G $vsGenerator -A x64

if ($LASTEXITCODE -ne 0) {
    Write-Host "CMake configuration failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

# 编译静态库目标 ncm_decoder_static
Write-Host "Building static library target 'ncm_decoder_static'..." -ForegroundColor Yellow
cmake --build . --config Release --target ncm_decoder_static

if ($LASTEXITCODE -ne 0) {
    Write-Host "Compilation failed" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location

# 提示输出位置（CMake 将 ARCHIVE_OUTPUT_DIRECTORY 设置到 project_root/build）
$projectBuildDir = Join-Path $ProjectRoot "build"
Write-Host "" 
Write-Host "Build completed successfully." -ForegroundColor Green
Write-Host "Expected static library location:" -ForegroundColor Gray
Write-Host "  - $projectBuildDir\Release\ncm_decoder_static.lib" -ForegroundColor Gray
Write-Host "  - $projectBuildDir\Debug\ncm_decoder_static.lib (if built in Debug)" -ForegroundColor Gray
Write-Host "" 
Write-Host "You can now run the Tauri dev app with:" -ForegroundColor Cyan
Write-Host "  .\\scripts\\develop\\build_and_run.ps1" -ForegroundColor White
