#!/usr/bin/env bash
# Music_Cool - Build C++ Static Library Only
# 仅构建 C++ 解码核心静态库（供 Tauri 版本使用），不运行程序
# 示例: ./scripts/develop/build_only.sh --clean

set -e  # 遇到错误立即退出

# 获取脚本目录（兼容 zsh 和 bash）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")" && pwd)"
SCRIPTS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$SCRIPTS_DIR/.." && pwd)"

# 解析参数
CLEAN=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --clean)
            CLEAN=true
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Usage: $0 [--clean]" >&2
            exit 1
            ;;
    esac
done

echo "=== Music_Cool - Build C++ Static Library ==="
echo "Project Directory: $PROJECT_ROOT"
echo ""

# 检查 CMake
if ! command -v cmake &> /dev/null; then
    echo "Error: CMake not found" >&2
    echo "Please install CMake:" >&2
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install cmake" >&2
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  sudo apt-get install cmake  # Ubuntu/Debian" >&2
        echo "  sudo yum install cmake       # Fedora/RHEL" >&2
    fi
    exit 1
fi

# 检测 C++ 编译器（优先 GCC，其次 Clang）
CXX=""
COMPILERS=("g++" "clang++")
for compiler in "${COMPILERS[@]}"; do
    if command -v "$compiler" &> /dev/null; then
        CXX="$compiler"
        break
    fi
done

if [[ -z "$CXX" ]]; then
    echo "Error: No C++ compiler found (g++ or clang++)" >&2
    echo "Please install a C++ compiler:" >&2
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  xcode-select --install  # Install Xcode Command Line Tools" >&2
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  sudo apt-get install build-essential  # Ubuntu/Debian" >&2
        echo "  sudo yum groupinstall 'Development Tools'  # Fedora/RHEL" >&2
    fi
    exit 1
fi

echo "Using C++ compiler: $CXX"
CXX_VERSION=$("$CXX" --version | head -n 1)
echo "  $CXX_VERSION"
echo ""

# 检查 OpenSSL 开发库
if ! pkg-config --exists openssl 2>/dev/null; then
    echo "Warning: OpenSSL development libraries not found via pkg-config" >&2
    echo "The build may fail if OpenSSL headers are not available." >&2
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  Install with: brew install openssl" >&2
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  Install with: sudo apt-get install libssl-dev  # Ubuntu/Debian" >&2
        echo "                sudo yum install openssl-devel    # Fedora/RHEL" >&2
    fi
    echo ""
fi

# 构建目录
CPP_DIR="$PROJECT_ROOT/src/cpp"
BUILD_DIR="$CPP_DIR/build"

# 清理
if [[ "$CLEAN" == true ]]; then
    echo "Cleaning C++ build directory..." >&2
    if [[ -d "$BUILD_DIR" ]]; then
        rm -rf "$BUILD_DIR"
    fi
fi

# 创建构建目录
if [[ ! -d "$BUILD_DIR" ]]; then
    mkdir -p "$BUILD_DIR"
fi

cd "$BUILD_DIR"

# 清理 CMake 缓存
if [[ -f "CMakeCache.txt" ]]; then
    echo "Cleaning CMake cache..." >&2
    rm -f CMakeCache.txt
    if [[ -d "CMakeFiles" ]]; then
        rm -rf CMakeFiles
    fi
fi

# 配置 CMake
echo "Configuring CMake for C++ decoder core..."
cmake .. -G "Unix Makefiles"

if [[ $? -ne 0 ]]; then
    echo "Error: CMake configuration failed" >&2
    exit 1
fi

# 编译静态库目标 ncm_decoder_static
echo "Building static library target 'ncm_decoder_static'..."
cmake --build . --target ncm_decoder_static

if [[ $? -ne 0 ]]; then
    echo "Error: Compilation failed" >&2
    exit 1
fi

cd "$PROJECT_ROOT"

# 提示输出位置
PROJECT_BUILD_DIR="$PROJECT_ROOT/build"
echo ""
echo "Build completed successfully."
echo "Expected static library location:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  - $PROJECT_BUILD_DIR/libncm_decoder_static.a"
else
    echo "  - $PROJECT_BUILD_DIR/libncm_decoder_static.a"
fi
echo ""
echo "You can now run the Tauri dev app with:"
echo "  ./scripts/develop/build_and_run.sh"

