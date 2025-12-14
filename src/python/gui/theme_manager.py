"""
主题管理器 - 管理亮色和暗色主题
"""

import json
from pathlib import Path
from typing import Dict, Optional


class ThemeManager:
    """主题管理器类"""
    
    # 暗色主题配色方案
    DARK_THEME = {
        'bg_main': '#111827',           # 主背景色
        'bg_card': '#1f2937',           # 卡片背景色
        'bg_input': '#111827',          # 输入框背景
        'bg_log': '#0f172a',            # 日志背景
        'border': '#374151',            # 边框色
        'border_hover': '#4b5563',      # 悬停边框色
        'primary': '#3b82f6',           # 主强调色
        'primary_hover': '#2563eb',     # 主强调色悬停
        'primary_pressed': '#1d4ed8',   # 主强调色按下
        'success': '#10b981',           # 成功色
        'success_hover': '#059669',     # 成功色悬停
        'success_pressed': '#047857',   # 成功色按下
        'error': '#ef4444',             # 错误色
        'error_hover': '#dc2626',       # 错误色悬停
        'error_pressed': '#b91c1c',     # 错误色按下
        'warning': '#f59e0b',           # 警告色（处理中）
        'text_primary': '#e5e7eb',     # 主要文字
        'text_secondary': '#d1d5db',    # 次要文字
        'text_tertiary': '#9ca3af',     # 三级文字
        'text_disabled': '#6b7280',     # 禁用文字
        'header_bg': '#374151',         # 表头背景
        'header_text': '#ffffff',       # 表头文字
        'row_hover': '#1f2937',         # 行悬停背景
        'row_alt': '#1a1f2e',           # 交替行背景
    }
    
    # 亮色主题配色方案
    LIGHT_THEME = {
        'bg_main': '#f9fafb',           # 主背景色
        'bg_card': '#ffffff',           # 卡片背景色
        'bg_input': '#ffffff',          # 输入框背景
        'bg_log': '#f3f4f6',            # 日志背景
        'border': '#e5e7eb',            # 边框色
        'border_hover': '#d1d5db',      # 悬停边框色
        'primary': '#2563eb',           # 主强调色
        'primary_hover': '#1d4ed8',     # 主强调色悬停
        'primary_pressed': '#1e40af',   # 主强调色按下
        'success': '#059669',           # 成功色
        'success_hover': '#047857',     # 成功色悬停
        'success_pressed': '#065f46',    # 成功色按下
        'error': '#dc2626',             # 错误色
        'error_hover': '#b91c1c',       # 错误色悬停
        'error_pressed': '#991b1b',     # 错误色按下
        'warning': '#f59e0b',           # 警告色（处理中）
        'text_primary': '#111827',     # 主要文字
        'text_secondary': '#374151',    # 次要文字
        'text_tertiary': '#6b7280',     # 三级文字
        'text_disabled': '#9ca3af',     # 禁用文字
        'header_bg': '#f3f4f6',         # 表头背景
        'header_text': '#111827',       # 表头文字
        'row_hover': '#f9fafb',         # 行悬停背景
        'row_alt': '#ffffff',           # 交替行背景
    }
    
    THEMES = {
        'dark': DARK_THEME,
        'light': LIGHT_THEME,
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化主题管理器
        
        Args:
            config_path: 配置文件路径，默认为项目根目录下的 config.json
        """
        if config_path is None:
            # 默认配置文件路径：项目根目录/config.json
            project_root = Path(__file__).parent.parent.parent.parent
            config_path = project_root / 'config.json'
        self.config_path = config_path
    
    def get_theme(self, theme_name: str = 'dark') -> Dict[str, str]:
        """
        获取主题配色方案
        
        Args:
            theme_name: 主题名称 ('dark' 或 'light')
            
        Returns:
            主题配色字典
        """
        return self.THEMES.get(theme_name, self.DARK_THEME)
    
    def load_theme(self) -> str:
        """
        从配置文件加载主题
        
        Returns:
            主题名称 ('dark' 或 'light')
        """
        if not self.config_path.exists():
            return 'dark'  # 默认暗色主题
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                theme = config.get('theme', 'dark')
                if theme not in self.THEMES:
                    theme = 'dark'
                return theme
        except (json.JSONDecodeError, IOError, KeyError):
            return 'dark'  # 默认暗色主题
    
    def save_theme(self, theme_name: str) -> bool:
        """
        保存主题到配置文件
        
        Args:
            theme_name: 主题名称 ('dark' 或 'light')
            
        Returns:
            是否保存成功
        """
        if theme_name not in self.THEMES:
            return False
        
        try:
            config = {}
            if self.config_path.exists():
                try:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except (json.JSONDecodeError, IOError):
                    config = {}
            
            config['theme'] = theme_name
            
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            return True
        except IOError:
            return False
    
    @staticmethod
    def get_qss_for_widget(widget_type: str, theme: Dict[str, str]) -> str:
        """
        获取特定控件的QSS样式字符串
        
        Args:
            widget_type: 控件类型 ('lineedit', 'button', 'progressbar', 'tree', 'groupbox', 'textedit')
            theme: 主题配色字典
            
        Returns:
            QSS样式字符串
        """
        if widget_type == 'lineedit':
            return f"""
                QLineEdit {{
                    padding: 10px 14px;
                    border: 1px solid {theme['border']};
                    border-radius: 8px;
                    font-size: 13px;
                    background-color: {theme['bg_input']};
                    color: {theme['text_primary']};
                }}
                QLineEdit:focus {{
                    border: 1px solid {theme['primary']};
                    background-color: {theme['bg_input']};
                }}
                QLineEdit:disabled {{
                    background-color: {theme['bg_card']};
                    color: {theme['text_disabled']};
                }}
            """
        elif widget_type == 'button_primary':
            return f"""
                QPushButton {{
                    padding: 10px 24px;
                    background-color: {theme['primary']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 13px;
                    font-weight: 500;
                    min-width: 80px;
                }}
                QPushButton:hover {{
                    background-color: {theme['primary_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {theme['primary_pressed']};
                }}
            """
        elif widget_type == 'button_success':
            return f"""
                QPushButton {{
                    background-color: {theme['success']};
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-size: 15px;
                    font-weight: 600;
                    padding: 12px 32px;
                }}
                QPushButton:hover {{
                    background-color: {theme['success_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {theme['success_pressed']};
                }}
                QPushButton:disabled {{
                    background-color: {theme['border']};
                    color: {theme['text_disabled']};
                }}
            """
        elif widget_type == 'button_error':
            return f"""
                QPushButton {{
                    background-color: {theme['error']};
                    color: white;
                    border: none;
                    border-radius: 10px;
                    font-size: 15px;
                    font-weight: 600;
                    padding: 12px 32px;
                }}
                QPushButton:hover {{
                    background-color: {theme['error_hover']};
                }}
                QPushButton:pressed {{
                    background-color: {theme['error_pressed']};
                }}
                QPushButton:disabled {{
                    background-color: {theme['border']};
                    color: {theme['text_disabled']};
                }}
            """
        elif widget_type == 'groupbox':
            return f"""
                QGroupBox {{
                    font-size: 14px;
                    font-weight: 500;
                    color: {theme['text_tertiary']};
                    border: 1px solid {theme['border']};
                    border-radius: 12px;
                    margin-top: 12px;
                    padding-top: 20px;
                    background-color: {theme['bg_card']};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 16px;
                    padding: 0 8px;
                    color: {theme['text_secondary']};
                }}
            """
        elif widget_type == 'textedit_log':
            return f"""
                QTextEdit {{
                    background-color: {theme['bg_log']};
                    color: {theme['text_primary']};
                    border: 1px solid {theme['border']};
                    border-radius: 8px;
                    padding: 12px;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 12px;
                }}
            """
        elif widget_type == 'splitter':
            return f"""
                QSplitter::handle {{
                    background-color: {theme['border']};
                    width: 2px;
                }}
                QSplitter::handle:hover {{
                    background-color: {theme['border_hover']};
                }}
            """
        else:
            return ""
