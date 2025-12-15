"""
Legacy PyQt6 GUI - 主程序入口

⚠️ 注意：此文件属于旧版 GUI 实现，不再积极维护。
推荐使用 Tauri 版本（位于 src-tauri/）作为主要桌面应用。

此文件保留仅作为参考实现。
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# 添加项目路径到sys.path
project_root = Path(__file__).parent.parent.parent
python_src_dir = Path(__file__).parent.parent  # src/python

# Add src/python to sys.path so packages can be imported correctly
# This ensures that 'from gui.main_window' resolves to 'src.python.gui.main_window'
sys.path.insert(0, str(python_src_dir))

# Add build directory for ncm_decoder extension module
sys.path.insert(0, str(project_root / "build"))

from gui.main_window import MainWindow


def main():
    """主函数"""
    # 设置高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("NCM文件解码器")
    app.setOrganizationName("CloudMusicDecoder")
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
