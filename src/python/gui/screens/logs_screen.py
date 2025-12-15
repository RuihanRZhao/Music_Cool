"""
日志页面
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from typing import Dict, Optional
import os

from ..widgets.navigation import NavigationBar
from ..widgets.card import Card


class LogsScreen(Screen):
    """日志页面"""
    
    def __init__(self, app, theme_manager, i18n_manager, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.theme_manager = theme_manager
        self.i18n_manager = i18n_manager
        
        self.log_text = None
        
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
            title=self.i18n_manager.tr('log'),
            theme=self.theme_manager.get_theme(self.theme_manager.load_theme())
        )
        content_layout.add_widget(header)
        
        # 日志显示区域（卡片）
        card = Card(theme=self.theme_manager.get_theme(self.theme_manager.load_theme()), orientation='vertical', spacing=8, padding=[12, 12, 12, 12], elevation=1)
        self.log_text = TextInput(
            text='',
            multiline=True,
            readonly=True,
            font_size=12
        )
        
        scroll_view = ScrollView()
        scroll_view.add_widget(self.log_text)
        card.add_widget(scroll_view)
        content_layout.add_widget(card)
        
        # 清空按钮
        clear_btn = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        clear_btn.add_widget(Label())  # 占位
        from ..widgets.clash_button import ClashButton
        clear_button = ClashButton(
            text='清空日志',
            size_hint_x=None,
            width=100,
            on_press=self.clear_logs,
            theme=self.theme_manager.get_theme(self.theme_manager.load_theme()),
            button_type='secondary'
        )
        clear_btn.add_widget(clear_button)
        content_layout.add_widget(clear_btn)
        
        main_layout.add_widget(content_layout)
        self.add_widget(main_layout)
    
    def add_log(self, message: str):
        """添加日志"""
        if self.log_text:
            self.log_text.text += message + '\n'
            # 自动滚动到底部
            self.log_text.cursor = (len(self.log_text.text), 0)
    
    def clear_logs(self, instance):
        """清空日志"""
        if self.log_text:
            self.log_text.text = ''
    
    def apply_theme(self, theme: Dict):
        """应用主题"""
        if self.navigation:
            self.navigation.apply_theme(theme)
        
        if self.log_text:
            # 设置文本颜色和背景色
            text_color = self._hex_to_rgba(theme.get('text_primary', '#e5e7eb'))
            bg_color = self._hex_to_rgba(theme.get('bg_log', '#0f172a'))
            
            self.log_text.foreground_color = text_color
            self.log_text.background_color = bg_color
    
    def _hex_to_rgba(self, hex_color: str) -> tuple:
        """将十六进制颜色转换为RGBA元组"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b, 1.0)


