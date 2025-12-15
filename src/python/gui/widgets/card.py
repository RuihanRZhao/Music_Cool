"""
通用卡片容器，提供圆角、背景色和阴影效果（Clash Verge 风格）
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, RoundedRectangle, Rectangle
from typing import Dict, Optional


class Card(BoxLayout):
    """卡片容器 - Clash Verge 风格"""

    def __init__(self, theme: Optional[Dict] = None, radius: Optional[int] = None, 
                 elevation: int = 0, **kwargs):
        super().__init__(**kwargs)
        self.theme = theme or {}
        # 从主题获取圆角，如果没有指定则使用主题默认值
        if radius is None:
            radius_str = self.theme.get('radius_md', '10')
            try:
                self.radius = int(radius_str)
            except (ValueError, TypeError):
                self.radius = 10
        else:
            self.radius = radius
        self.elevation = elevation  # 阴影深度（0-3）
        
        with self.canvas.before:
            # 阴影层（如果有）
            if self.elevation > 0:
                self._shadow_color = Color(0, 0, 0, 0.1 * self.elevation)
                self._shadow_rect = RoundedRectangle(radius=[self.radius] * 4)
            # 背景层
            self._bg_color = Color(1, 1, 1, 1)
            self._bg_rect = RoundedRectangle(radius=[self.radius] * 4)
        
        self.bind(pos=self._update_rect, size=self._update_rect)
        if theme:
            self.set_theme(theme)

    def _update_rect(self, *args):
        """更新矩形位置和大小"""
        if self.elevation > 0:
            # 阴影稍微偏移
            offset = self.elevation * 2
            self._shadow_rect.pos = (self.pos[0] + offset, self.pos[1] - offset)
            self._shadow_rect.size = self.size
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def set_theme(self, theme: Dict):
        """设置卡片主题"""
        self.theme = theme
        bg = theme.get("card_bg", theme.get("bg_card", "#2B303B"))
        rgba = self._hex_to_rgba(bg)
        self._bg_color.rgba = rgba

    def _hex_to_rgba(self, hex_color: str) -> tuple:
        """将十六进制颜色转换为RGBA元组"""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b, 1.0)



