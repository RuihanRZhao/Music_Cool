"""
文件列表页面
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from pathlib import Path
from typing import Dict, Optional, List

from ..widgets.navigation import NavigationBar
from ..widgets.card import Card
from decoder_wrapper import DecoderWrapper
import os


class FilesScreen(Screen):
    """文件列表页面"""
    
    def __init__(self, app, decoder_wrapper: DecoderWrapper,
                 theme_manager, i18n_manager, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.decoder_wrapper = decoder_wrapper
        self.theme_manager = theme_manager
        self.i18n_manager = i18n_manager
        
        self.file_items = {}  # {file_path: {widget, status}}
        self.base_path = ""
        
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
            title=self.i18n_manager.tr('file_list'),
            theme=self.theme_manager.get_theme(self.theme_manager.load_theme())
        )
        content_layout.add_widget(header)
        
        # 文件列表卡片
        card = Card(theme=self.theme_manager.get_theme(self.theme_manager.load_theme()), orientation='vertical', spacing=8, padding=[12, 12, 12, 12], elevation=1)
        self.file_grid = GridLayout(
            cols=3,
            spacing=8,
            size_hint_y=None
        )
        self.file_grid.bind(minimum_height=self.file_grid.setter('height'))
        
        # 表头
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=34, spacing=6)
        theme = self.theme_manager.get_theme(self.theme_manager.load_theme())
        file_label = Label(text=self.i18n_manager.tr('file_name'), size_hint_x=2)
        file_label.color = self._hex_to_rgba(theme.get('text_secondary', '#D9D9D6'))
        status_label = Label(text=self.i18n_manager.tr('status'), size_hint_x=1)
        status_label.color = self._hex_to_rgba(theme.get('text_secondary', '#D9D9D6'))
        progress_label = Label(text=self.i18n_manager.tr('progress'), size_hint_x=1)
        progress_label.color = self._hex_to_rgba(theme.get('text_secondary', '#D9D9D6'))
        header.add_widget(file_label)
        header.add_widget(status_label)
        header.add_widget(progress_label)
        self.file_grid.add_widget(header)
        
        scroll_view = ScrollView()
        scroll_view.add_widget(self.file_grid)
        card.add_widget(scroll_view)
        content_layout.add_widget(card)
        
        main_layout.add_widget(content_layout)
        self.add_widget(main_layout)
    
    def update_file_list(self, file_list: List[Dict], base_path: str = ""):
        """更新文件列表"""
        self.base_path = base_path
        self.file_items.clear()
        self.file_grid.clear_widgets()
        
        # 表头
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        header.add_widget(Label(text=self.i18n_manager.tr('file_name'), size_hint_x=2))
        header.add_widget(Label(text=self.i18n_manager.tr('status'), size_hint_x=1))
        header.add_widget(Label(text=self.i18n_manager.tr('progress'), size_hint_x=1))
        self.file_grid.add_widget(header)
        
        # 添加文件项
        for file_info in file_list:
            file_path = file_info['input_path']
            rel_path = file_info.get('relative_path', Path(file_path).name)
            
            # 创建文件项
            item = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
            
            # 文件名
            theme = self.theme_manager.get_theme(self.theme_manager.load_theme())
            file_label = Label(
                text=str(rel_path),
                text_size=(None, None),
                halign='left'
            )
            file_label.bind(texture_size=file_label.setter('size'))
            file_label.color = self._hex_to_rgba(theme.get('text_primary', '#FFFFFF'))
            
            # 状态
            status_label = Label(text=self.i18n_manager.tr('waiting'))
            status_label.color = self._hex_to_rgba(theme.get('text_secondary', '#D9D9D6'))
            
            # 进度
            progress_label = Label(text="0%")
            progress_label.color = self._hex_to_rgba(theme.get('text_secondary', '#D9D9D6'))
            
            item.add_widget(file_label)
            item.add_widget(status_label)
            item.add_widget(progress_label)
            
            self.file_grid.add_widget(item)
            self.file_items[file_path] = {
                'widget': item,
                'file_label': file_label,
                'status_label': status_label,
                'progress_label': progress_label,
                'status': 'waiting'
            }
    
    def update_file_status(self, file_path: str, status: str, error: str = ""):
        """更新文件状态"""
        if file_path not in self.file_items:
            return
        
        item = self.file_items[file_path]
        status_map = {
            'waiting': self.i18n_manager.tr('waiting'),
            'processing': self.i18n_manager.tr('processing'),
            'completed': self.i18n_manager.tr('completed'),
            'failed': self.i18n_manager.tr('file_failed'),
            'skipped': self.i18n_manager.tr('copied')
        }
        
        item['status_label'].text = status_map.get(status, status)
        item['status'] = status
        
        if status == 'processing':
            item['progress_label'].text = "..."
        elif status == 'completed' or status == 'skipped':
            item['progress_label'].text = "100%"
        elif status == 'failed':
            item['progress_label'].text = self.i18n_manager.tr('file_failed')
            if error:
                item['status_label'].text = f"{status_map.get(status, status)}: {error}"
        else:
            item['progress_label'].text = "0%"
    
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

