"""
左侧导航栏组件 - Clash Verge 风格
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, RoundedRectangle
from typing import Dict, Optional


class NavigationBar(BoxLayout):
    """左侧导航栏 - Clash Verge 风格"""
    
    def __init__(self, screen_manager, theme: Optional[Dict] = None, i18n_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_x = None
        self.width = 220  # 稍微加宽
        self.spacing = 4
        self.padding = [12, 20, 12, 20]
        self.screen_manager = screen_manager
        self.theme = theme or {}
        self.i18n_manager = i18n_manager
        self.current_button = None
        self.buttons = {}
        
        self.init_ui()
        self.apply_theme(self.theme)
    
    def init_ui(self):
        """初始化UI"""
        # 标题区域
        title = Label(
            text=self._tr('app_title'),
            size_hint_y=None,
            height=60,
            font_size=18,
            bold=True
        )
        title.color = self._hex_to_rgba(self.theme.get('text_primary', '#FFFFFF'))
        self.add_widget(title)
        
        # 导航按钮
        nav_items = [
            ('main', '📁', self._tr('main_page')),
            ('files', '📋', self._tr('file_list')),
            ('logs', '📝', self._tr('log')),
            ('settings', '⚙', self._tr('settings')),
        ]
        
        for screen_name, icon, text in nav_items:
            btn = self._create_nav_button(screen_name, f"{icon} {text}")
            self.buttons[screen_name] = btn
            self.add_widget(btn)
        
        # 添加弹性空间
        self.add_widget(Label(size_hint_y=1))
        
        # 设置默认选中主页
        if 'main' in self.buttons:
            self.select_button(self.buttons['main'])
    
    def _create_nav_button(self, screen_name: str, text: str) -> Button:
        """创建导航按钮 - Clash Verge 风格"""
        btn = NavButton(
            text=text,
            size_hint_y=None,
            height=48,
            theme=self.theme,
            on_press=lambda instance: self.switch_screen(screen_name)
        )
        return btn
    
    def switch_screen(self, screen_name: str):
        """切换屏幕"""
        if self.screen_manager:
            self.screen_manager.current = screen_name
        
        # 更新按钮选中状态
        if screen_name in self.buttons:
            self.select_button(self.buttons[screen_name])
    
    def select_button(self, button: Button):
        """选中按钮"""
        # 取消所有按钮的选中状态
        for btn in self.buttons.values():
            if isinstance(btn, NavButton):
                btn.set_selected(False)
        
        # 设置当前按钮为选中
        if isinstance(button, NavButton):
            button.set_selected(True)
            self.current_button = button
    
    def apply_theme(self, theme: Dict):
        """应用主题"""
        self.theme = theme
        
        # 背景色（侧边栏背景）
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._hex_to_rgba(theme.get('bg_sidebar', '#1E222A')))
            Rectangle(pos=self.pos, size=self.size)
        
        # 更新所有按钮的主题
        for btn in self.buttons.values():
            if isinstance(btn, NavButton):
                btn.apply_theme(theme)
        
        # 更新标题颜色
        for child in self.children:
            if isinstance(child, Label) and child.text == self._tr('app_title'):
                child.color = self._hex_to_rgba(theme.get('text_primary', '#FFFFFF'))
    
    def _hex_to_rgba(self, hex_color: str) -> tuple:
        """将十六进制颜色转换为RGBA元组"""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b, 1.0)
    
    def _tr(self, key: str) -> str:
        """获取翻译文本"""
        if self.i18n_manager:
            return self.i18n_manager.tr(key)
        defaults = {
            'app_title': 'NCM文件解码器',
            'main_page': '主页',
            'file_list': '文件列表',
            'log': '日志',
            'settings': '设置',
        }
        return defaults.get(key, key)


class NavButton(Button):
    """导航按钮 - 带选中状态和右侧圆角"""
    
    def __init__(self, theme: Optional[Dict] = None, **kwargs):
        super().__init__(**kwargs)
        self.theme = theme or {}
        self.is_selected = False
        self.background_normal = ''
        self.background_down = ''
        
        # 从主题获取圆角
        radius_str = self.theme.get('radius_md', '10')
        try:
            self.radius = int(radius_str)
        except (ValueError, TypeError):
            self.radius = 10
        
        with self.canvas.before:
            self._bg_color = Color(0, 0, 0, 0)  # 透明
            self._bg_rect = RoundedRectangle(radius=[0, 0, self.radius, self.radius])  # 仅右侧圆角
        
        self.bind(pos=self._update_rect, size=self._update_rect)
        if theme:
            self.apply_theme(theme)
    
    def _update_rect(self, *args):
        """更新矩形位置和大小"""
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
    
    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        self._update_appearance()
    
    def _update_appearance(self):
        """更新外观"""
        if not self.theme:
            return
        
        if self.is_selected:
            # 选中状态：使用 accent 颜色，白色文字
            accent_color = self.theme.get('accent', self.theme.get('primary', '#2962FF'))
            self._bg_color.rgba = self._hex_to_rgba(accent_color)
            self.color = (1, 1, 1, 1)  # 白色
        else:
            # 未选中状态：透明背景，灰色文字
            self._bg_color.rgba = (0, 0, 0, 0)  # 透明
            self.color = self._hex_to_rgba(self.theme.get('text_secondary', '#D9D9D6'))
    
    def apply_theme(self, theme: Dict):
        """应用主题"""
        self.theme = theme
        self._update_appearance()
    
    def on_enter(self):
        """鼠标进入"""
        if not self.is_selected and self.theme:
            # 悬停效果：浅色背景
            hover_color = self.theme.get('row_hover', '#2D3035')
            self._bg_color.rgba = self._hex_to_rgba(hover_color)
    
    def on_leave(self):
        """鼠标离开"""
        self._update_appearance()
    
    def _hex_to_rgba(self, hex_color: str) -> tuple:
        """将十六进制颜色转换为RGBA元组"""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b, 1.0)
