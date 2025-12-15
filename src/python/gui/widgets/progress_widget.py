"""
进度显示组件 - Kivy版本，支持多线程进度显示
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from typing import Dict, Optional, List
from pathlib import Path
from .card import Card


class MultiThreadProgressWidget(BoxLayout):
    """多线程进度显示组件"""
    
    def __init__(self, max_threads: int = 8, theme: Optional[Dict] = None, i18n_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 15
        self.padding = [10, 10]
        self.max_threads = max_threads
        self.theme = theme or {}
        self.i18n_manager = i18n_manager
        
        # 总进度
        self.total_progress = ProgressBar(max=100, value=0, height=10, size_hint_y=None)
        self.total_label = Label(text=self._tr('total_progress'))
        self.total_count_label = Label(text="0/0")
        
        # 多线程进度列表
        self.thread_progress_items = {}  # {thread_id: {widgets}}
        self.thread_container = GridLayout(cols=2, spacing=10, size_hint_y=None, padding=[0, 0, 0, 0])
        self.thread_container.bind(minimum_height=self.thread_container.setter('height'))
        
        self.scroll_view = ScrollView(size_hint_y=1)
        self.scroll_view.add_widget(self.thread_container)
        
        self.init_ui()
        self.apply_theme(self.theme)
    
    def init_ui(self):
        """初始化UI"""
        # 总进度区域
        total_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=80)
        total_header = BoxLayout(orientation='horizontal', size_hint_y=None, height=30)
        total_header.add_widget(self.total_label)
        total_header.add_widget(self.total_count_label)
        total_layout.add_widget(total_header)
        total_layout.add_widget(self.total_progress)
        self.add_widget(total_layout)
        
        # 多线程进度列表
        thread_label = Label(
            text=self._tr('thread_progress'),
            size_hint_y=None,
            height=30
        )
        self.add_widget(thread_label)
        self.add_widget(self.scroll_view)
    
    def update_total_progress(self, completed: int, total: int):
        """更新总进度"""
        if total > 0:
            percentage = int((completed / total) * 100)
            self.total_progress.value = percentage
            self.total_count_label.text = f"{completed}/{total} {self._tr('files')}"
        else:
            self.total_progress.value = 0
            self.total_count_label.text = "0/0"
    
    def update_thread_progress(self, thread_progress: Dict[int, Dict]):
        """更新线程进度
        
        Args:
            thread_progress: {thread_id: {file_path, current_bytes, total_bytes}}
        """
        # 移除不存在的线程项
        existing_ids = set(thread_progress.keys())
        to_remove = set(self.thread_progress_items.keys()) - existing_ids
        for thread_id in to_remove:
            if thread_id in self.thread_progress_items:
                for widget in self.thread_progress_items[thread_id].values():
                    self.thread_container.remove_widget(widget)
                del self.thread_progress_items[thread_id]
        
        # 更新或创建线程进度项
        for thread_id, info in thread_progress.items():
            if thread_id not in self.thread_progress_items:
                # 创建新的线程进度项
                self._create_thread_item(thread_id, info)
            else:
                # 更新现有项
                self._update_thread_item(thread_id, info)
    
    def _create_thread_item(self, thread_id: int, info: Dict):
        """创建线程进度项"""
        file_path = info.get('file_path', '')
        current_bytes = info.get('current_bytes', 0)
        total_bytes = info.get('total_bytes', 0)
        
        # 容器
        item_container = Card(
            theme=self.theme or {},
            orientation='vertical',
            size_hint_y=None,
            height=90,
            spacing=6,
            padding=[10, 10, 10, 10],
            radius=10
        )
        
        # 文件名标签
        file_name = Path(file_path).name if file_path else self._tr('waiting')
        file_label = Label(
            text=f"线程 {thread_id + 1}: {file_name}",
            size_hint_y=None,
            height=25,
            text_size=(None, None),
            halign='left',
            font_size=13
        )
        
        # 进度条
        progress_bar = ProgressBar(max=total_bytes if total_bytes > 0 else 100, value=current_bytes, height=10, size_hint_y=None)
        
        # 字节信息标签
        if total_bytes > 0:
            current_mb = current_bytes / (1024 * 1024)
            total_mb = total_bytes / (1024 * 1024)
            bytes_label = Label(
                text=f"{current_mb:.2f} MB / {total_mb:.2f} MB",
                size_hint_y=None,
                height=20
            )
        else:
            bytes_label = Label(text="", size_hint_y=None, height=20)
        
        item_container.add_widget(file_label)
        item_container.add_widget(progress_bar)
        item_container.add_widget(bytes_label)
        
        self.thread_container.add_widget(item_container)
        self.thread_progress_items[thread_id] = {
            'container': item_container,
            'file_label': file_label,
            'progress_bar': progress_bar,
            'bytes_label': bytes_label
        }
    
    def _update_thread_item(self, thread_id: int, info: Dict):
        """更新线程进度项"""
        if thread_id not in self.thread_progress_items:
            return
        
        widgets = self.thread_progress_items[thread_id]
        file_path = info.get('file_path', '')
        current_bytes = info.get('current_bytes', 0)
        total_bytes = info.get('total_bytes', 0)
        
        # 更新文件名
        file_name = Path(file_path).name if file_path else self._tr('waiting')
        widgets['file_label'].text = f"线程 {thread_id + 1}: {file_name}"
        
        # 更新进度条
        if total_bytes > 0:
            widgets['progress_bar'].max = total_bytes
            widgets['progress_bar'].value = current_bytes
            
            # 更新字节信息
            current_mb = current_bytes / (1024 * 1024)
            total_mb = total_bytes / (1024 * 1024)
            widgets['bytes_label'].text = f"{current_mb:.2f} MB / {total_mb:.2f} MB"
        else:
            widgets['progress_bar'].value = 0
            widgets['bytes_label'].text = ""
    
    def reset(self):
        """重置进度显示"""
        self.total_progress.value = 0
        self.total_count_label.text = "0/0"
        
        # 清除所有线程进度项
        for thread_id in list(self.thread_progress_items.keys()):
            widgets = self.thread_progress_items[thread_id]
            for widget in widgets.values():
                self.thread_container.remove_widget(widget)
        self.thread_progress_items.clear()
    
    def apply_theme(self, theme: Dict):
        """应用主题"""
        self.theme = theme
        
        # 标签颜色
        label_color = self._hex_to_rgba(theme.get('text_primary', '#e5e7eb'))
        self.total_label.color = label_color
        self.total_count_label.color = label_color
        
        # 进度条颜色
        progress_color = self._hex_to_rgba(theme.get('primary', '#3b82f6'))
        # Kivy ProgressBar的颜色通过canvas设置比较复杂，这里使用背景色
        self.total_progress.background_color = self._hex_to_rgba(theme.get('bg_card', '#1f2937'))
    
    def _hex_to_rgba(self, hex_color: str) -> tuple:
        """将十六进制颜色转换为RGBA元组"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b, 1.0)

    
    def _tr(self, key: str) -> str:
        """获取翻译文本"""
        if self.i18n_manager:
            return self.i18n_manager.tr(key)
        defaults = {
            'total_progress': '总进度',
            'thread_progress': '线程进度',
            'files': '文件',
            'waiting': '等待中...',
        }
        return defaults.get(key, key)

