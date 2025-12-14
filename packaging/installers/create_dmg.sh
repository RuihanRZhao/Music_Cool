#!/bin/bash

# macOS DMG创建脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../../"
APP_BUNDLE="$1"
DMG_NAME="${2:-NCMDecoder.dmg}"

if [ -z "$APP_BUNDLE" ]; then
    echo "用法: $0 <app_bundle> [dmg_name]"
    echo "  app_bundle: .app bundle路径"
    echo "  dmg_name: 输出DMG文件名（默认: NCMDecoder.dmg）"
    exit 1
fi

if [ ! -d "$APP_BUNDLE" ]; then
    echo "错误: App bundle不存在: $APP_BUNDLE"
    exit 1
fi

# 检查create-dmg
if ! command -v create-dmg &> /dev/null; then
    echo "错误: 未找到create-dmg"
    echo "请安装: brew install create-dmg"
    exit 1
fi

# 创建临时目录
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# 复制app bundle
cp -R "$APP_BUNDLE" "$TEMP_DIR/"

# 创建DMG
echo "创建DMG..."
create-dmg \
    --volname "NCM解码器" \
    --volicon "$PROJECT_ROOT/packaging/icons/app.icns" \
    --window-pos 200 120 \
    --window-size 800 400 \
    --icon-size 100 \
    --icon "NCMDecoder.app" 200 190 \
    --hide-extension "NCMDecoder.app" \
    --app-drop-link 600 185 \
    "$PROJECT_ROOT/$DMG_NAME" \
    "$TEMP_DIR"

echo "DMG已创建: $PROJECT_ROOT/$DMG_NAME"
