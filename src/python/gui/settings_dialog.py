"""
设置对话框 - 支持语言和主题切换
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QComboBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from .theme_manager import ThemeManager
from .i18n_manager import I18nManager


class SettingsDialog(QDialog):
    """设置对话框类"""
    
    # 信号：设置已更改
    settings_changed = pyqtSignal(str, str)  # language, theme
    
    def __init__(self, parent=None, theme_manager: ThemeManager = None, i18n_manager: I18nManager = None):
        """
        初始化设置对话框
        
        Args:
            parent: 父窗口
            theme_manager: 主题管理器实例
            i18n_manager: 国际化管理器实例
        """
        super().__init__(parent)
        self.theme_manager = theme_manager or ThemeManager()
        self.i18n_manager = i18n_manager or I18nManager()
        
        # 保存初始值
        self.initial_language = self.i18n_manager.current_language
        self.initial_theme = self.theme_manager.load_theme()
        
        self.init_ui()
        self.apply_theme(self.initial_theme)
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(self.i18n_manager.tr('settings_title'))
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(24, 24, 24, 24)
        
        # 设置组
        self.settings_group = QGroupBox(self.i18n_manager.tr('settings_title'))
        settings_layout = QFormLayout()
        settings_layout.setSpacing(16)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        
        # 语言选择
        self.language_combo = QComboBox()
        self.language_combo.addItem(self.i18n_manager.tr('chinese'), 'zh_CN')
        self.language_combo.addItem(self.i18n_manager.tr('english'), 'en_US')
        
        # 设置当前语言
        current_index = self.language_combo.findData(self.initial_language)
        if current_index >= 0:
            self.language_combo.setCurrentIndex(current_index)
        
        self.language_label = QLabel(self.i18n_manager.tr('select_language') + ':')
        settings_layout.addRow(self.language_label, self.language_combo)
        
        # 主题选择
        self.theme_combo = QComboBox()
        self.theme_combo.addItem(self.i18n_manager.tr('dark_theme'), 'dark')
        self.theme_combo.addItem(self.i18n_manager.tr('light_theme'), 'light')
        
        # 设置当前主题
        current_theme_index = self.theme_combo.findData(self.initial_theme)
        if current_theme_index >= 0:
            self.theme_combo.setCurrentIndex(current_theme_index)
        
        # 主题切换时实时预览
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        
        self.theme_label = QLabel(self.i18n_manager.tr('select_theme') + ':')
        settings_layout.addRow(self.theme_label, self.theme_combo)
        
        self.settings_group.setLayout(settings_layout)
        main_layout.addWidget(self.settings_group)
        
        main_layout.addStretch()
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.ok_btn = QPushButton(self.i18n_manager.tr('ok'))
        self.ok_btn.setMinimumHeight(40)
        self.ok_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton(self.i18n_manager.tr('cancel'))
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
    
    def on_theme_changed(self, index: int):
        """主题切换时的预览"""
        theme_code = self.theme_combo.itemData(index)
        if theme_code:
            self.apply_theme(theme_code)
    
    def apply_theme(self, theme_name: str):
        """应用主题"""
        theme = self.theme_manager.get_theme(theme_name)
        
        # 对话框背景
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme['bg_main']};
            }}
            QLabel {{
                color: {theme['text_primary']};
                font-size: 13px;
            }}
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
            QComboBox {{
                padding: 8px 12px;
                border: 1px solid {theme['border']};
                border-radius: 8px;
                font-size: 13px;
                background-color: {theme['bg_input']};
                color: {theme['text_primary']};
                min-width: 150px;
            }}
            QComboBox:hover {{
                border: 1px solid {theme['border_hover']};
            }}
            QComboBox:focus {{
                border: 1px solid {theme['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {theme['text_secondary']};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme['bg_card']};
                border: 1px solid {theme['border']};
                border-radius: 8px;
                selection-background-color: {theme['primary']};
                color: {theme['text_primary']};
                padding: 4px;
            }}
        """)
        
        # 按钮样式
        self.ok_btn.setStyleSheet(ThemeManager.get_qss_for_widget('button_primary', theme))
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 10px 24px;
                background-color: {theme['bg_card']};
                color: {theme['text_primary']};
                border: 1px solid {theme['border']};
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {theme['border']};
                border: 1px solid {theme['border_hover']};
            }}
            QPushButton:pressed {{
                background-color: {theme['border_hover']};
            }}
        """)
    
    def accept(self):
        """确定按钮点击"""
        # 获取选中的语言和主题
        language = self.language_combo.currentData()
        theme = self.theme_combo.currentData()
        
        # 保存设置
        language_changed = False
        theme_changed = False
        if language and language != self.initial_language:
            self.i18n_manager.save_language(language)
            language_changed = True
        
        if theme and theme != self.initial_theme:
            self.theme_manager.save_theme(theme)
            theme_changed = True
        
        # 发送信号通知主窗口
        # 只发送实际更改的设置，发送新值以便主窗口更新
        if language_changed or theme_changed:
            # 发送更改后的值（如果语言更改了发送新语言，否则发送None让主窗口知道没有语言更改）
            emit_language = language if language_changed else None
            emit_theme = theme if theme_changed else None
            self.settings_changed.emit(emit_language, emit_theme)
        
        super().accept()
