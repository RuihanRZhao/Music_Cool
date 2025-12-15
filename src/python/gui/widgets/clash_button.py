"""
Clash Verge 风格按钮组件
"""

from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle
from typing import Dict, Optional


class ClashButton(Button):
    """Clash Verge 风格按钮"""
    
    def __init__(self, theme: Optional[Dict] = None, button_type: str = 'primary', **kwargs):
        super().__init__(**kwargs)
        self.theme = theme or {}
        self.button_type = button_type  # 'primary', 'secondary', 'success', 'error'
        
        # 从主题获取圆角
        radius_str = self.theme.get('radius_md', '10')
        try:
            self.radius = int(radius_str)
        except (ValueError, TypeError):
            self.radius = 10
        
        with self.canvas.before:
            self._bg_color = Color(1, 1, 1, 1)
            self._bg_rect = RoundedRectangle(radius=[self.radius] * 4)
        
        self.bind(pos=self._update_rect, size=self._update_rect)
        if theme:
            self.apply_theme(theme)
    
    def _update_rect(self, *args):
        """更新矩形位置和大小"""
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
    
    def apply_theme(self, theme: Dict):
        """应用主题"""
        self.theme = theme
        
        # 根据按钮类型选择颜色
        color_map = {
            'primary': theme.get('primary', '#2962FF'),
            'secondary': theme.get('text_secondary', '#D9D9D6'),
            'success': theme.get('success', '#32C07A'),
            'error': theme.get('error', '#F26B60'),
        }
        bg_color = color_map.get(self.button_type, theme.get('primary', '#2962FF'))
        
        rgba = self._hex_to_rgba(bg_color)
        self._bg_color.rgba = rgba
        
        # 设置文字颜色
        if self.button_type == 'secondary':
            self.color = self._hex_to_rgba(theme.get('text_primary', '#FFFFFF'))
        else:
            self.color = (1, 1, 1, 1)  # 白色文字
    
    def _hex_to_rgba(self, hex_color: str) -> tuple:
        """将十六进制颜色转换为RGBA元组"""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b, 1.0)
    
    def on_press(self):
        """按下时的视觉反馈"""
        if self.theme:
            color_map = {
                'primary': self.theme.get('primary_pressed', '#1565C0'),
                'secondary': self.theme.get('text_tertiary', '#8E8E92'),
                'success': self.theme.get('success_pressed', '#218351'),
                'error': self.theme.get('error_pressed', '#B4463F'),
            }
            pressed_color = color_map.get(self.button_type, self.theme.get('primary_pressed', '#1565C0'))
            self._bg_color.rgba = self._hex_to_rgba(pressed_color)
    
    def on_release(self):
        """释放时恢复颜色"""
        if self.theme:
            self.apply_theme(self.theme)


