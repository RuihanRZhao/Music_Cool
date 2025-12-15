#!/usr/bin/env bash
# Music_Cool - Build C++ Core and Run Tauri Dev
# 构建 C++ 解码核心静态库并启动 Tauri 开发环境
# 示例: ./scripts/develop/build_and_run.sh

set -e  # 遇到错误立即退出

# 获取脚本目录（兼容 zsh 和 bash）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")" && pwd)"
SCRIPTS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$SCRIPTS_DIR/.." && pwd)"

# 解析参数
SKIP_BUILD=false
CLEAN=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Usage: $0 [--skip-build] [--clean]" >&2
            exit 1
            ;;
    esac
done

echo "=== Music_Cool - Build C++ Core & Run Tauri Dev ==="
echo "Project Directory: $PROJECT_ROOT"
echo ""

# -------------------------------------------------------------
# 1. 构建 C++ 静态库（如果未跳过）
# -------------------------------------------------------------
if [[ "$SKIP_BUILD" == false ]]; then
    echo "[1/2] Building C++ static library..."
    if [[ "$CLEAN" == true ]]; then
        "$SCRIPT_DIR/build_only.sh" --clean
    else
        "$SCRIPT_DIR/build_only.sh"
    fi
    
    if [[ $? -ne 0 ]]; then
        echo "Error: C++ build failed" >&2
        exit 1
    fi
    echo ""
else
    echo "[1/2] Skipping C++ build (--skip-build specified)"
    echo ""
fi

# -------------------------------------------------------------
# 2. 启动 Tauri 开发环境
# -------------------------------------------------------------
echo "[2/2] Starting Tauri dev..."
"$SCRIPT_DIR/run_only.sh"

if [[ $? -ne 0 ]]; then
    echo "Error: Tauri dev failed" >&2
    exit 1
fi

