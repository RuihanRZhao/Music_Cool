"""
Legacy PyQt6 GUI 主应用类

⚠️ 注意：此文件属于旧版 GUI 实现，不再积极维护。
推荐使用 Tauri 版本（位于 src-tauri/）作为主要桌面应用。

此文件保留仅作为参考实现。
"""

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from pathlib import Path

from .screens.main_screen import MainScreen
from .screens.files_screen import FilesScreen
from .screens.logs_screen import LogsScreen
from .screens.settings_screen import SettingsScreen
from .theme_manager import ThemeManager
from .i18n_manager import I18nManager
from decoder_wrapper import DecoderWrapper


class NCMDecoderApp(App):
    """NCM解码器主应用"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_manager = ThemeManager()
        self.i18n_manager = I18nManager()
        self.decoder_wrapper = DecoderWrapper()
        self.screen_manager = None
        
    def build(self):
        """构建应用界面"""
        # 设置窗口大小
        Window.size = (1200, 800)
        Window.minimum_width = 1000
        Window.minimum_height = 600
        
        # 创建屏幕管理器
        self.screen_manager = ScreenManager()
        
        self._build_screens()
        
        # 设置当前主题
        current_theme = self.theme_manager.load_theme()
        self.apply_theme(current_theme)
        
        return self.screen_manager
    
    def apply_theme(self, theme_name: str):
        """应用主题"""
        theme = self.theme_manager.get_theme(theme_name)
        
        # 设置窗口背景色
        from kivy.core.window import Window
        Window.clearcolor = self._hex_to_rgba(theme.get('bg_main', '#22262E'))
        
        # 通知所有屏幕更新主题
        for screen in self.screen_manager.screens:
            if hasattr(screen, 'apply_theme'):
                screen.apply_theme(theme)
    
    def rebuild_screens(self):
        """语言变更后重建所有屏幕"""
        current = self.screen_manager.current if self.screen_manager else 'main'
        if self.screen_manager:
            self.screen_manager.clear_widgets()
            self._build_screens()
            # 保持在主屏
            if self.screen_manager.has_screen(current):
                self.screen_manager.current = current
            else:
                self.screen_manager.current = 'main'
    
    def _build_screens(self):
        """创建并添加所有屏幕"""
        main_screen = MainScreen(
            name='main',
            app=self,
            decoder_wrapper=self.decoder_wrapper,
            theme_manager=self.theme_manager,
            i18n_manager=self.i18n_manager
        )
        
        files_screen = FilesScreen(
            name='files',
            app=self,
            decoder_wrapper=self.decoder_wrapper,
            theme_manager=self.theme_manager,
            i18n_manager=self.i18n_manager
        )
        
        logs_screen = LogsScreen(
            name='logs',
            app=self,
            theme_manager=self.theme_manager,
            i18n_manager=self.i18n_manager
        )
        
        settings_screen = SettingsScreen(
            name='settings',
            app=self,
            theme_manager=self.theme_manager,
            i18n_manager=self.i18n_manager
        )
        
        self.screen_manager.add_widget(main_screen)
        self.screen_manager.add_widget(files_screen)
        self.screen_manager.add_widget(logs_screen)
        self.screen_manager.add_widget(settings_screen)
    
    def _hex_to_rgba(self, hex_color: str) -> tuple:
        """将十六进制颜色转换为RGBA元组"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b, 1.0)
    
    def on_stop(self):
        """应用关闭时"""
        if self.decoder_wrapper.is_running():
            self.decoder_wrapper.stop()

