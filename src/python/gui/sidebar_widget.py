"""
侧边栏导航组件 - 支持主题切换
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, Optional


class SidebarWidget(QWidget):
    """侧边栏导航组件"""
    
    # 信号：页面切换
    page_changed = pyqtSignal(str)  # 页面名称
    
    def __init__(self, parent=None, i18n_manager=None, theme_manager=None):
        super().__init__(parent)
        self.i18n_manager = i18n_manager
        self.theme_manager = theme_manager
        self.current_theme: Optional[Dict[str, str]] = None
        self.current_page = "main"
        self.buttons = {}
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 20, 12, 20)
        
        # 页面按钮
        pages = [
            ("main", "📁", self._tr('main_page')),
            ("files", "📋", self._tr('file_list')),
            ("log", "📝", self._tr('log')),
            ("settings", "⚙", self._tr('settings')),
        ]
        
        for page_id, icon, text in pages:
            btn = QPushButton(f"{icon} {text}")
            btn.setCheckable(True)
            btn.setMinimumHeight(45)
            btn.clicked.connect(lambda checked, pid=page_id: self.on_page_clicked(pid))
            self.buttons[page_id] = btn
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # 默认选中主页面
        if "main" in self.buttons:
            self.buttons["main"].setChecked(True)
    
    def on_page_clicked(self, page_id: str):
        """页面按钮点击"""
        # 取消其他按钮的选中状态
        for pid, btn in self.buttons.items():
            btn.setChecked(pid == page_id)
        
        self.current_page = page_id
        self.page_changed.emit(page_id)
    
    def set_page(self, page_id: str):
        """设置当前页面"""
        if page_id in self.buttons:
            self.on_page_clicked(page_id)
    
    def set_theme(self, theme: Dict[str, str]):
        """设置主题"""
        self.current_theme = theme
        
        # 侧边栏样式
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['bg_card']};
                border-right: 1px solid {theme['border']};
            }}
        """)
        
        # 按钮样式
        button_style = f"""
            QPushButton {{
                text-align: left;
                padding: 12px 16px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                color: {theme['text_secondary']};
                background-color: transparent;
            }}
            QPushButton:hover {{
                background-color: {theme['row_hover']};
                color: {theme['text_primary']};
            }}
            QPushButton:checked {{
                background-color: {theme['primary']};
                color: white;
                font-weight: 600;
            }}
        """
        
        for btn in self.buttons.values():
            btn.setStyleSheet(button_style)
    
    def _tr(self, key: str) -> str:
        """获取翻译文本"""
        if self.i18n_manager:
            return self.i18n_manager.tr(key)
        # 默认返回中文
        defaults = {
            'main_page': '主页面',
            'file_list': '文件列表',
            'log': '日志',
            'settings': '设置',
        }
        return defaults.get(key, key)
    
    def update_texts(self, i18n_manager):
        """更新文本（语言切换时调用）"""
        self.i18n_manager = i18n_manager
        # 更新按钮文本
        pages = [
            ("main", "📁", self._tr('main_page')),
            ("files", "📋", self._tr('file_list')),
            ("log", "📝", self._tr('log')),
            ("settings", "⚙", self._tr('settings')),
        ]
        for page_id, icon, text in pages:
            if page_id in self.buttons:
                self.buttons[page_id].setText(f"{icon} {text}")

