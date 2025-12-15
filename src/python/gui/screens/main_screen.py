"""
主页面 - 配置和进度显示
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from plyer import filechooser
from pathlib import Path
from typing import Dict, Optional
import threading
import os
import tkinter as tk
from tkinter import filedialog

from ..widgets.navigation import NavigationBar
from ..widgets.progress_widget import MultiThreadProgressWidget
from ..widgets.card import Card
from decoder_wrapper import DecoderWrapper


class MainScreen(Screen):
    """主页面"""
    
    def __init__(self, app, decoder_wrapper: DecoderWrapper, 
                 theme_manager, i18n_manager, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.decoder_wrapper = decoder_wrapper
        self.theme_manager = theme_manager
        self.i18n_manager = i18n_manager
        
        # 状态
        self.completed_files = 0
        self.total_files = 0
        self.max_threads = 8
        
        # UI组件
        self.navigation = None
        self.input_path_input = None
        self.output_path_input = None
        self.thread_spinner = None
        self.start_btn = None
        self.stop_btn = None
        self.progress_widget = None
        
        # 设置解码器回调
        self.decoder_wrapper.set_callbacks(
            progress_callback=self.on_file_progress,
            file_finished_callback=self.on_file_finished,
            all_finished_callback=self.on_all_finished,
            error_callback=self.on_error,
            log_callback=self.on_log_message
        )
        
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
        
        # 顶部标题（使用 SectionHeader）
        from ..widgets.section_header import SectionHeader
        header = SectionHeader(
            title=self.i18n_manager.tr('app_title'),
            theme=self.theme_manager.get_theme(self.theme_manager.load_theme())
        )
        content_layout.add_widget(header)
        
        # 配置区域（卡片）
        config_card = Card(theme=self.theme_manager.get_theme(self.theme_manager.load_theme()), orientation='vertical', spacing=14, size_hint_y=None, height=240, padding=[16, 16, 16, 16], elevation=1)
        config_layout = config_card
        
        # 输入文件夹
        input_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=12)
        input_label = Label(text=self.i18n_manager.tr('input_folder') + ':', size_hint_x=None, width=120)
        input_label.color = self._theme_color('text_primary')
        input_layout.add_widget(input_label)
        self.input_path_input = TextInput(
            text='',
            hint_text=self.i18n_manager.tr('select_ncm_folder'),
            multiline=False,
            padding=[12, 10]
        )
        input_browse_btn = Button(
            text=self.i18n_manager.tr('browse'),
            size_hint_x=None,
            width=100,
            on_press=self.browse_input_folder,
            background_normal='',
            background_down='',
            background_color=self._theme_color('primary'),
            color=(1,1,1,1)
        )
        input_layout.add_widget(self.input_path_input)
        input_layout.add_widget(input_browse_btn)
        config_layout.add_widget(input_layout)
        
        # 输出文件夹
        output_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=12)
        output_label = Label(text=self.i18n_manager.tr('output_folder') + ':', size_hint_x=None, width=120)
        output_label.color = self._theme_color('text_primary')
        output_layout.add_widget(output_label)
        self.output_path_input = TextInput(
            text='',
            hint_text=self.i18n_manager.tr('select_output_folder'),
            multiline=False,
            padding=[12, 10]
        )
        output_browse_btn = Button(
            text=self.i18n_manager.tr('browse'),
            size_hint_x=None,
            width=100,
            on_press=self.browse_output_folder,
            background_normal='',
            background_down='',
            background_color=self._theme_color('primary'),
            color=(1,1,1,1)
        )
        output_layout.add_widget(self.output_path_input)
        output_layout.add_widget(output_browse_btn)
        config_layout.add_widget(output_layout)
        
        # 线程数
        thread_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=44, spacing=12)
        thread_label_title = Label(text=self.i18n_manager.tr('max_threads') + ':', size_hint_x=None, width=120)
        thread_label_title.color = self._theme_color('text_primary')
        thread_layout.add_widget(thread_label_title)
        self.thread_spinner = Spinner(
            text=str(self.max_threads),
            values=[str(i) for i in range(1, 33)],
            size_hint_x=None,
            width=100
        )
        self.thread_spinner.bind(text=self.on_threads_changed)
        thread_label = Label(
            text=self.i18n_manager.tr('recommended_threads'),
            size_hint_x=1
        )
        thread_label.color = self._theme_color('text_secondary')
        thread_layout.add_widget(self.thread_spinner)
        thread_layout.add_widget(thread_label)
        config_layout.add_widget(thread_layout)
        
        content_layout.add_widget(config_card)
        
        # 控制按钮
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=12)
        from ..widgets.clash_button import ClashButton
        theme = self.theme_manager.get_theme(self.theme_manager.load_theme())
        self.start_btn = ClashButton(
            text=self.i18n_manager.tr('start_decode'),
            on_press=self.start_decode,
            theme=theme,
            button_type='primary',
            size_hint_x=None,
            width=120
        )
        self.stop_btn = ClashButton(
            text=self.i18n_manager.tr('stop'),
            on_press=self.stop_decode,
            theme=theme,
            button_type='error',
            disabled=True,
            size_hint_x=None,
            width=120
        )
        button_layout.add_widget(self.start_btn)
        button_layout.add_widget(self.stop_btn)
        content_layout.add_widget(button_layout)
        
        # 进度显示卡片
        progress_card = Card(theme=self.theme_manager.get_theme(self.theme_manager.load_theme()), orientation='vertical', spacing=12, padding=[16, 16, 16, 16], elevation=1)
        self.progress_widget = MultiThreadProgressWidget(
            max_threads=self.max_threads,
            theme=self.theme_manager.get_theme(self.theme_manager.load_theme()),
            i18n_manager=self.i18n_manager
        )
        progress_card.add_widget(self.progress_widget)
        content_layout.add_widget(progress_card)
        
        main_layout.add_widget(content_layout)
        self.add_widget(main_layout)
    
    def on_threads_changed(self, spinner, text):
        """线程数改变"""
        try:
            self.max_threads = int(text)
            if self.progress_widget:
                self.progress_widget.max_threads = self.max_threads
        except ValueError:
            pass
    
    def browse_input_folder(self, instance):
        """浏览输入文件夹"""
        selected = self._select_directory()
        if selected:
            self.input_path_input.text = selected
            self.scan_files_async(selected)
    
    def browse_output_folder(self, instance):
        """浏览输出文件夹"""
        selected = self._select_directory()
        if selected:
            self.output_path_input.text = selected
    
    def scan_files_async(self, input_path: str):
        """异步扫描文件"""
        def on_scan_complete(result, error):
            if error:
                Clock.schedule_once(lambda dt: self.on_scan_error(error), 0)
            else:
                Clock.schedule_once(lambda dt: self.on_scan_complete(result), 0)
        
        self.decoder_wrapper.scan_folder_async(input_path, on_scan_complete)
    
    def on_scan_complete(self, result: Dict):
        """扫描完成"""
        self.total_files = result['total_files']
        ncm_count = len(result['ncm_files'])
        other_count = len(result['other_files'])
        
        log_msg = (f"{self.i18n_manager.tr('scan_complete')}: {self.total_files} {self.i18n_manager.tr('files')} "
                  f"({ncm_count} NCM {self.i18n_manager.tr('files')}, "
                  f"{other_count} {self.i18n_manager.tr('other_files')})")
        self.on_log_message(log_msg)
        
        # 通知文件列表页面更新
        files_screen = self.app.screen_manager.get_screen('files')
        if hasattr(files_screen, 'update_file_list'):
            file_list = self.decoder_wrapper.get_file_list()
            files_screen.update_file_list(file_list, self.input_path_input.text)
    
    def on_scan_error(self, error: Exception):
        """扫描错误"""
        error_msg = f"{self.i18n_manager.tr('scan_failed')}: {error}"
        self.on_log_message(error_msg)
    
    def start_decode(self, instance):
        """开始解码"""
        input_path = self.input_path_input.text
        output_path = self.output_path_input.text
        
        if not input_path:
            self.on_log_message(self.i18n_manager.tr('please_select_input'))
            return
        
        if not output_path:
            self.on_log_message(self.i18n_manager.tr('please_select_output'))
            return
        
        if self.decoder_wrapper.is_running():
            self.on_log_message(self.i18n_manager.tr('decoding_in_progress'))
            return
        
        # 重置状态
        self.completed_files = 0
        if not hasattr(self, 'total_files') or self.total_files == 0:
            file_list = self.decoder_wrapper.get_file_list()
            self.total_files = len(file_list) if file_list else 1
        
        self.progress_widget.reset()
        
        # 更新UI
        self.start_btn.disabled = True
        self.stop_btn.disabled = False
        self.input_path_input.disabled = True
        self.output_path_input.disabled = True
        self.thread_spinner.disabled = True
        
        # 在后台线程中开始解码
        def decode_thread():
            try:
                self.decoder_wrapper.decode_folder(input_path, output_path, self.max_threads)
            except Exception as e:
                Clock.schedule_once(lambda dt: self.on_error("", str(e)), 0)
        
        thread = threading.Thread(target=decode_thread, daemon=True)
        thread.start()
    
    def stop_decode(self, instance):
        """停止解码"""
        if self.decoder_wrapper.is_running():
            self.decoder_wrapper.stop()
            self.on_log_message(self.i18n_manager.tr('stopping'))
    
    def on_file_progress(self, file_path: str, current_bytes: int, total_bytes: int, finished: bool):
        """文件进度更新"""
        # 更新多线程进度
        thread_progress = self.decoder_wrapper.get_thread_progress()
        Clock.schedule_once(lambda dt: self.progress_widget.update_thread_progress(thread_progress), 0)
    
    def on_file_finished(self, file_path: str, success: bool, error: str, output_format: str):
        """文件完成"""
        self.completed_files += 1
        
        # 更新总进度
        if not hasattr(self, 'total_files') or self.total_files == 0:
            file_list = self.decoder_wrapper.get_file_list()
            self.total_files = len(file_list) if file_list else 1
        
        Clock.schedule_once(
            lambda dt: self.progress_widget.update_total_progress(self.completed_files, self.total_files),
            0
        )
        
        # 通知文件列表页面更新
        files_screen = self.app.screen_manager.get_screen('files')
        if hasattr(files_screen, 'update_file_status'):
            if success:
                if output_format == "已复制" or output_format == "Copied":
                    files_screen.update_file_status(file_path, 'skipped')
                else:
                    files_screen.update_file_status(file_path, 'completed')
            else:
                files_screen.update_file_status(file_path, 'failed', error)
    
    def on_all_finished(self):
        """所有文件完成"""
        Clock.schedule_once(lambda dt: self.on_log_message(self.i18n_manager.tr('all_files_complete')), 0)
        Clock.schedule_once(lambda dt: self.reset_ui_state(), 0)
    
    def on_error(self, file_path: str, error: str):
        """错误处理"""
        error_msg = f"{self.i18n_manager.tr('error')}: {error}"
        Clock.schedule_once(lambda dt: self.on_log_message(error_msg), 0)
    
    def on_log_message(self, message: str):
        """日志消息"""
        # 通知日志页面
        logs_screen = self.app.screen_manager.get_screen('logs')
        if hasattr(logs_screen, 'add_log'):
            Clock.schedule_once(lambda dt: logs_screen.add_log(message), 0)
    
    def reset_ui_state(self):
        """重置UI状态"""
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
        self.input_path_input.disabled = False
        self.output_path_input.disabled = False
        self.thread_spinner.disabled = False
    
    def apply_theme(self, theme: Dict):
        """应用主题"""
        if self.progress_widget:
            self.progress_widget.apply_theme(theme)
        if self.navigation:
            self.navigation.apply_theme(theme)
        # 更新按钮主题
        from ..widgets.clash_button import ClashButton
        if isinstance(self.start_btn, ClashButton):
            self.start_btn.apply_theme(theme)
        if isinstance(self.stop_btn, ClashButton):
            self.stop_btn.apply_theme(theme)
        # 更新输入框和标签颜色
        if self.input_path_input:
            self.input_path_input.background_color = self._theme_color('bg_input', 1.0)
            self.input_path_input.foreground_color = self._theme_color('text_primary', 1.0)
        if self.output_path_input:
            self.output_path_input.background_color = self._theme_color('bg_input', 1.0)
            self.output_path_input.foreground_color = self._theme_color('text_primary', 1.0)

    def _select_directory(self) -> Optional[str]:
        """选择文件夹，优先 plyer，失败回退 tkinter"""
        chosen = None
        error_msg = None
        # 尝试 plyer
        try:
            if hasattr(filechooser, "choose_dir"):
                result = filechooser.choose_dir()
                if result:
                    chosen = result[0] if isinstance(result, list) else result
        except Exception as e:
            error_msg = f"plyer_choose_dir_error: {e}"
        # 回退 tkinter
        if not chosen:
            try:
                root = tk.Tk()
                root.withdraw()
                chosen = filedialog.askdirectory()
                root.destroy()
            except Exception as e:
                error_msg = f"tk_filedialog_error: {e}"
        return chosen

    def _theme_color(self, key: str, alpha: float = 1.0):
        """获取主题颜色 (rgba tuple)"""
        theme = self.theme_manager.get_theme(self.theme_manager.load_theme())
        hex_color = theme.get(key, "#0A84FF")
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b, alpha)


