#!/bin/bash

# Linux AppImage创建脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../../"
DIST_DIR="$1"
APPIMAGE_NAME="${2:-NCMDecoder.AppImage}"

if [ -z "$DIST_DIR" ]; then
    echo "用法: $0 <dist_dir> [appimage_name]"
    echo "  dist_dir: PyInstaller输出的目录"
    echo "  appimage_name: 输出AppImage文件名（默认: NCMDecoder.AppImage）"
    exit 1
fi

if [ ! -d "$DIST_DIR" ]; then
    echo "错误: 目录不存在: $DIST_DIR"
    exit 1
fi

# 检查appimagetool
if ! command -v appimagetool &> /dev/null; then
    echo "错误: 未找到appimagetool"
    echo "请安装AppImageKit: https://github.com/AppImage/AppImageKit"
    echo "或下载: https://github.com/AppImage/AppImageKit/releases"
    exit 1
fi

# 创建AppDir
APPDIR="$PROJECT_ROOT/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR"

# 复制文件
echo "复制文件到AppDir..."
cp -r "$DIST_DIR"/* "$APPDIR/"

# 创建.desktop文件
cat > "$APPDIR/NCMDecoder.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=NCM解码器
Comment=NCM文件解码工具
Exec=NCMDecoder
Icon=NCMDecoder
Categories=AudioVideo;Audio;
Terminal=false
EOF

# 创建AppRun脚本
cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/NCMDecoder" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# 创建图标（如果存在）
if [ -f "$PROJECT_ROOT/packaging/icons/app.png" ]; then
    mkdir -p "$APPDIR/usr/share/pixmaps"
    cp "$PROJECT_ROOT/packaging/icons/app.png" "$APPDIR/NCMDecoder.png"
    cp "$PROJECT_ROOT/packaging/icons/app.png" "$APPDIR/usr/share/pixmaps/NCMDecoder.png"
fi

# 运行appimagetool
echo "创建AppImage..."
appimagetool "$APPDIR" "$PROJECT_ROOT/$APPIMAGE_NAME"

# 清理
rm -rf "$APPDIR"

echo "AppImage已创建: $PROJECT_ROOT/$APPIMAGE_NAME"
