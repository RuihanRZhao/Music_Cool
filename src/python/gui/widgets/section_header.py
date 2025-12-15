"""
区域标题组件 - Clash Verge 风格
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from typing import Dict, Optional


class SectionHeader(BoxLayout):
    """区域标题组件"""
    
    def __init__(self, title: str = "", subtitle: str = "", 
                 theme: Optional[Dict] = None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 4
        self.padding = [0, 0, 0, 8]
        self.theme = theme or {}
        
        # 主标题
        self.title_label = Label(
            text=title,
            size_hint_y=None,
            height=24,
            font_size=16,
            bold=True
        )
        
        # 副标题（可选）
        self.subtitle_label = None
        if subtitle:
            self.subtitle_label = Label(
                text=subtitle,
                size_hint_y=None,
                height=18,
                font_size=12
            )
            self.add_widget(self.subtitle_label)
        
        self.add_widget(self.title_label)
        
        if theme:
            self.apply_theme(theme)
    
    def apply_theme(self, theme: Dict):
        """应用主题"""
        self.theme = theme
        primary_color = self._hex_to_rgba(theme.get('text_primary', '#FFFFFF'))
        secondary_color = self._hex_to_rgba(theme.get('text_secondary', '#D9D9D6'))
        
        self.title_label.color = primary_color
        if self.subtitle_label:
            self.subtitle_label.color = secondary_color
    
    def _hex_to_rgba(self, hex_color: str) -> tuple:
        """将十六进制颜色转换为RGBA元组"""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b, 1.0)


