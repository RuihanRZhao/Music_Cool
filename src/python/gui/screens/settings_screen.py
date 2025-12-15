"""
设置页面
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from typing import Dict, Optional

from ..widgets.navigation import NavigationBar
from ..widgets.card import Card
import os


class SettingsScreen(Screen):
    """设置页面"""
    
    def __init__(self, app, theme_manager, i18n_manager, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.theme_manager = theme_manager
        self.i18n_manager = i18n_manager
        
        self.language_spinner = None
        self.theme_spinner = None
        
        self.init_ui()
        self.apply_theme(self.theme_manager.get_theme(self.theme_manager.load_theme()))
    
    def init_ui(self):
        """初始化UI"""
        main_layout = BoxLayout(orientation='horizontal', spacing=0)
        
        # 左侧导航栏
        self.navigation = NavigationBar(
            screen_manager=self.app.screen_manager,
            theme=self.theme_manager.get_theme(self.theme_manager.load_theme()),
            i18n_manager=self.i18n_manager
        )
        main_layout.add_widget(self.navigation)
        
        # 右侧内容区域
        content_layout = BoxLayout(orientation='vertical', spacing=14, padding=20)
        
        # 标题
        from ..widgets.section_header import SectionHeader
        header = SectionHeader(
            title=self.i18n_manager.tr('settings_title'),
            theme=self.theme_manager.get_theme(self.theme_manager.load_theme())
        )
        content_layout.add_widget(header)
        
        # 设置区域（卡片）
        settings_card = Card(theme=self.theme_manager.get_theme(self.theme_manager.load_theme()), orientation='vertical', spacing=16, padding=[16, 16, 16, 16], elevation=1)
        settings_layout = BoxLayout(orientation='vertical', spacing=14)
        
        # 语言选择
        theme = self.theme_manager.get_theme(self.theme_manager.load_theme())
        language_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=12)
        lang_label = Label(text=self.i18n_manager.tr('select_language') + ':', size_hint_x=None, width=150)
        lang_label.color = self._hex_to_rgba(theme.get('text_primary', '#FFFFFF'))
        language_layout.add_widget(lang_label)
        self.language_spinner = Spinner(
            text=self.i18n_manager.get_language_name(self.i18n_manager.current_language),
            values=[self.i18n_manager.get_language_name('zh_CN'), 
                   self.i18n_manager.get_language_name('en_US')],
            size_hint_x=1
        )
        self.language_spinner.bind(text=self.on_language_changed)
        language_layout.add_widget(self.language_spinner)
        settings_layout.add_widget(language_layout)
        
        # 主题选择
        theme_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=12)
        theme_label = Label(text=self.i18n_manager.tr('select_theme') + ':', size_hint_x=None, width=150)
        theme_label.color = self._hex_to_rgba(theme.get('text_primary', '#FFFFFF'))
        theme_layout.add_widget(theme_label)
        current_theme = self.theme_manager.load_theme()
        theme_names = {
            'dark': self.i18n_manager.tr('dark_theme'),
            'light': self.i18n_manager.tr('light_theme'),
            'clash_dark': self.i18n_manager.tr('dark_theme'),
            'notion_dark': self.i18n_manager.tr('dark_theme')
        }
        self.theme_spinner = Spinner(
            text=theme_names.get(current_theme, self.i18n_manager.tr('dark_theme')),
            values=[self.i18n_manager.tr('dark_theme'), self.i18n_manager.tr('light_theme')],
            size_hint_x=1
        )
        self.theme_spinner.bind(text=self.on_theme_changed)
        theme_layout.add_widget(self.theme_spinner)
        settings_layout.add_widget(theme_layout)
        
        settings_card.add_widget(settings_layout)
        content_layout.add_widget(settings_card)
        content_layout.add_widget(Label())  # 占位
        
        main_layout.add_widget(content_layout)
        self.add_widget(main_layout)
    
    def on_language_changed(self, spinner, text):
        """语言改变"""
        # 根据显示名称找到语言代码
        if text == self.i18n_manager.get_language_name('zh_CN'):
            language = 'zh_CN'
        else:
            language = 'en_US'
        
        if language != self.i18n_manager.current_language:
            self.i18n_manager.save_language(language)
            # 更新应用的语言并重建界面
            self.app.i18n_manager.current_language = language
            if hasattr(self.app, 'rebuild_screens'):
                self.app.rebuild_screens()
    
    def on_theme_changed(self, spinner, text):
        """主题改变"""
        theme_map = {
            self.i18n_manager.tr('dark_theme'): 'dark',
            self.i18n_manager.tr('light_theme'): 'light'
        }
        theme = theme_map.get(text, 'dark')
        
        if theme != self.theme_manager.load_theme():
            self.theme_manager.save_theme(theme)
            self.app.apply_theme(theme)
    
    def apply_theme(self, theme: Dict):
        """应用主题"""
        if self.navigation:
            self.navigation.apply_theme(theme)
    
    def _hex_to_rgba(self, hex_color: str) -> tuple:
        """将十六进制颜色转换为RGBA元组"""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b, 1.0)

