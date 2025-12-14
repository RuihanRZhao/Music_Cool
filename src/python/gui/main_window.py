"""
主窗口 - Clash Verge 风格，支持主题切换
"""

import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QLineEdit, QSpinBox, QFileDialog,
    QTextEdit, QSplitter, QGroupBox, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont

from .progress_widget import ProgressWidget
from .file_tree_widget import FileTreeWidget, FileStatus
from .theme_manager import ThemeManager
from .i18n_manager import I18nManager
from .settings_dialog import SettingsDialog
from decoder_wrapper import DecoderWrapper


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.decoder_wrapper = DecoderWrapper()
        self.completed_files = 0
        self.total_files = 0
        self.current_file_path = ""
        
        # 初始化国际化管理器
        self.i18n_manager = I18nManager()
        
        # 初始化主题管理器
        self.theme_manager = ThemeManager()
        self.current_theme = self.theme_manager.load_theme()
        
        self.init_ui()
        self.apply_theme(self.current_theme)
        self.connect_signals()
        self.setup_logging()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(self.i18n_manager.tr('app_title'))
        self.setMinimumSize(1200, 800)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题区域
        title_layout = QHBoxLayout()
        self.title_label = QLabel(self.i18n_manager.tr('app_title'))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(self.title_label, stretch=1)
        
        # 设置按钮
        self.settings_btn = QPushButton(f"⚙ {self.i18n_manager.tr('settings')}")
        self.settings_btn.setFixedWidth(100)
        self.settings_btn.clicked.connect(self.show_settings_dialog)
        title_layout.addWidget(self.settings_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        main_layout.addLayout(title_layout)
        
        # 配置区域
        self.config_group = QGroupBox(self.i18n_manager.tr('config'))
        config_layout = QFormLayout()
        config_layout.setSpacing(16)
        config_layout.setContentsMargins(20, 20, 20, 20)
        
        # 输入文件夹
        input_layout = QHBoxLayout()
        input_layout.setSpacing(12)
        self.input_path_edit = QLineEdit()
        self.input_path_edit.setPlaceholderText(self.i18n_manager.tr('select_ncm_folder'))
        self.input_browse_btn = QPushButton(self.i18n_manager.tr('browse'))
        self.input_browse_btn.clicked.connect(self.browse_input_folder)
        input_layout.addWidget(self.input_path_edit)
        input_layout.addWidget(self.input_browse_btn)
        self.input_folder_label = QLabel(self.i18n_manager.tr('input_folder') + ':')
        config_layout.addRow(self.input_folder_label, input_layout)
        
        # 输出文件夹
        output_layout = QHBoxLayout()
        output_layout.setSpacing(12)
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText(self.i18n_manager.tr('select_output_folder'))
        self.output_browse_btn = QPushButton(self.i18n_manager.tr('browse'))
        self.output_browse_btn.clicked.connect(self.browse_output_folder)
        output_layout.addWidget(self.output_path_edit)
        output_layout.addWidget(self.output_browse_btn)
        self.output_folder_label = QLabel(self.i18n_manager.tr('output_folder') + ':')
        config_layout.addRow(self.output_folder_label, output_layout)
        
        # 最大线程数
        thread_layout = QHBoxLayout()
        thread_layout.setSpacing(12)
        self.thread_spinbox = QSpinBox()
        self.thread_spinbox.setMinimum(1)
        self.thread_spinbox.setMaximum(32)
        self.thread_spinbox.setValue(8)
        self.thread_label = QLabel(self.i18n_manager.tr('recommended_threads'))
        thread_layout.addWidget(self.thread_spinbox)
        thread_layout.addWidget(self.thread_label)
        thread_layout.addStretch()
        self.max_threads_label = QLabel(self.i18n_manager.tr('max_threads') + ':')
        config_layout.addRow(self.max_threads_label, thread_layout)
        
        self.config_group.setLayout(config_layout)
        main_layout.addWidget(self.config_group)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.start_btn = QPushButton(self.i18n_manager.tr('start_decode'))
        self.start_btn.setMinimumHeight(48)
        self.start_btn.clicked.connect(self.start_decode)
        
        self.stop_btn = QPushButton(self.i18n_manager.tr('stop'))
        self.stop_btn.setMinimumHeight(48)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_decode)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        # 进度显示
        # #region agent log
        import json, os
        log_path = r'e:\Tools\CloudMusicDecoder\.cursor\debug.log'
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"main_window.py:139","message":"Creating ProgressWidget","data":{"i18n_manager_type":type(self.i18n_manager).__name__},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        self.progress_widget = ProgressWidget(i18n_manager=self.i18n_manager)
        main_layout.addWidget(self.progress_widget)
        
        # 分割器：文件树和日志
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 文件树
        self.file_tree_group = QGroupBox(self.i18n_manager.tr('file_list'))
        file_tree_layout = QVBoxLayout()
        file_tree_layout.setContentsMargins(12, 12, 12, 12)
        # #region agent log
        log_path = r'e:\Tools\CloudMusicDecoder\.cursor\debug.log'
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"main_window.py:149","message":"Creating FileTreeWidget","data":{"i18n_manager_type":type(self.i18n_manager).__name__},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        self.file_tree = FileTreeWidget(i18n_manager=self.i18n_manager)
        file_tree_layout.addWidget(self.file_tree)
        self.file_tree_group.setLayout(file_tree_layout)
        self.splitter.addWidget(self.file_tree_group)
        
        # 日志区域
        self.log_group = QGroupBox(self.i18n_manager.tr('log'))
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(12, 12, 12, 12)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        log_layout.addWidget(self.log_text)
        self.log_group.setLayout(log_layout)
        self.splitter.addWidget(self.log_group)
        
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 1)
        main_layout.addWidget(self.splitter)
    
    def show_settings_dialog(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self, self.theme_manager, self.i18n_manager)
        dialog.settings_changed.connect(self.on_settings_changed)
        dialog.exec()
    
    def on_settings_changed(self, language: str, theme: str):
        """设置更改回调"""
        # #region agent log
        import json, os
        log_path = r'e:\Tools\CloudMusicDecoder\.cursor\debug.log'
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"main_window.py:188","message":"on_settings_changed entry","data":{"language":language,"theme":theme,"current_language":self.i18n_manager.current_language,"current_theme":self.current_theme},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        
        # 更新语言
        # 如果 language 不是 None，说明语言被更改了（设置对话框只在 language_changed 时发送 language）
        if language:
            old_language = self.i18n_manager.current_language
            # 确保 current_language 与信号中的 language 一致（可能已经在 save_language 中更新了）
            self.i18n_manager.current_language = language
            # #region agent log
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"main_window.py:194","message":"Language change detected, updating","data":{"old_language":old_language,"new_language":language},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
            self.update_ui_texts()
            # #region agent log
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"main_window.py:199","message":"update_ui_texts completed","data":{},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
        else:
            # #region agent log
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"main_window.py:202","message":"No language change, skipping language update","data":{},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
        
        # 更新主题
        # 如果 theme 不是 None，说明主题被更改了（设置对话框只在 theme_changed 时发送 theme）
        if theme:
            # #region agent log
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"main_window.py:217","message":"Theme change detected, updating","data":{"old_theme":self.current_theme,"new_theme":theme},"timestamp":int(__import__('time').time()*1000)})+'\n')
            # #endregion
            self.current_theme = theme
            self.apply_theme(theme)
    
    def update_ui_texts(self):
        """更新所有UI文本"""
        # #region agent log
        import json, os
        log_path = r'e:\Tools\CloudMusicDecoder\.cursor\debug.log'
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"main_window.py:200","message":"update_ui_texts entry","data":{"current_language":self.i18n_manager.current_language},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        
        # 窗口标题
        new_title = self.i18n_manager.tr('app_title')
        self.setWindowTitle(new_title)
        # #region agent log
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"main_window.py:207","message":"Window title updated","data":{"title":new_title},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        
        # 标题标签
        self.title_label.setText(new_title)
        
        # 设置按钮
        settings_text = f"⚙ {self.i18n_manager.tr('settings')}"
        self.settings_btn.setText(settings_text)
        # #region agent log
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"main_window.py:215","message":"Settings button updated","data":{"text":settings_text},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        
        # 组框标题
        self.config_group.setTitle(self.i18n_manager.tr('config'))
        self.file_tree_group.setTitle(self.i18n_manager.tr('file_list'))
        self.log_group.setTitle(self.i18n_manager.tr('log'))
        
        # 标签
        self.input_folder_label.setText(self.i18n_manager.tr('input_folder') + ':')
        self.output_folder_label.setText(self.i18n_manager.tr('output_folder') + ':')
        self.max_threads_label.setText(self.i18n_manager.tr('max_threads') + ':')
        self.thread_label.setText(self.i18n_manager.tr('recommended_threads'))
        
        # 占位符
        self.input_path_edit.setPlaceholderText(self.i18n_manager.tr('select_ncm_folder'))
        self.output_path_edit.setPlaceholderText(self.i18n_manager.tr('select_output_folder'))
        
        # 按钮
        self.input_browse_btn.setText(self.i18n_manager.tr('browse'))
        self.output_browse_btn.setText(self.i18n_manager.tr('browse'))
        self.start_btn.setText(self.i18n_manager.tr('start_decode'))
        self.stop_btn.setText(self.i18n_manager.tr('stop'))
        
        # 更新子组件
        # #region agent log
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"main_window.py:235","message":"Updating child widgets","data":{},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        self.progress_widget.update_texts(self.i18n_manager)
        self.file_tree.update_texts(self.i18n_manager)
        # #region agent log
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"main_window.py:238","message":"update_ui_texts completed","data":{},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
    
    def switch_theme(self, theme_name: str):
        """切换主题"""
        if theme_name != self.current_theme:
            self.current_theme = theme_name
            self.theme_manager.save_theme(theme_name)
            self.apply_theme(theme_name)
    
    def apply_theme(self, theme_name: str):
        """应用主题到所有组件"""
        theme = self.theme_manager.get_theme(theme_name)
        
        # 主窗口背景
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme['bg_main']};
            }}
            QLabel {{
                color: {theme['text_primary']};
                font-size: 13px;
            }}
            QFormLayout QLabel {{
                font-weight: 500;
                color: {theme['text_secondary']};
            }}
        """)
        
        # 标题
        self.title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 32px;
                font-weight: 600;
                color: {theme['text_primary']};
                padding: 20px;
                background-color: {theme['bg_card']};
                border-radius: 12px;
            }}
        """)
        
        # 设置按钮
        self.settings_btn.setStyleSheet(ThemeManager.get_qss_for_widget('button_primary', theme))
        
        # GroupBox
        groupbox_style = ThemeManager.get_qss_for_widget('groupbox', theme)
        self.config_group.setStyleSheet(groupbox_style)
        self.file_tree_group.setStyleSheet(groupbox_style)
        self.log_group.setStyleSheet(groupbox_style)
        
        # 输入框
        lineedit_style = ThemeManager.get_qss_for_widget('lineedit', theme)
        self.input_path_edit.setStyleSheet(lineedit_style)
        self.output_path_edit.setStyleSheet(lineedit_style)
        
        # SpinBox
        spinbox_style = f"""
            QSpinBox {{
                padding: 10px 14px;
                border: 1px solid {theme['border']};
                border-radius: 8px;
                font-size: 13px;
                background-color: {theme['bg_input']};
                color: {theme['text_primary']};
                min-width: 80px;
            }}
            QSpinBox:focus {{
                border: 1px solid {theme['primary']};
                background-color: {theme['bg_input']};
            }}
            QSpinBox:disabled {{
                background-color: {theme['bg_card']};
                color: {theme['text_disabled']};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {theme['border']};
                border: none;
                border-radius: 4px;
                width: 20px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {theme['border_hover']};
            }}
        """
        self.thread_spinbox.setStyleSheet(spinbox_style)
        
        # 浏览按钮
        browse_btn_style = ThemeManager.get_qss_for_widget('button_primary', theme)
        self.input_browse_btn.setStyleSheet(browse_btn_style)
        self.output_browse_btn.setStyleSheet(browse_btn_style)
        
        # 开始/停止按钮
        self.start_btn.setStyleSheet(ThemeManager.get_qss_for_widget('button_success', theme))
        self.stop_btn.setStyleSheet(ThemeManager.get_qss_for_widget('button_error', theme))
        
        # 日志区域
        self.log_text.setStyleSheet(ThemeManager.get_qss_for_widget('textedit_log', theme))
        
        # 分割器
        self.splitter.setStyleSheet(ThemeManager.get_qss_for_widget('splitter', theme))
        
        # 进度组件
        self.progress_widget.set_theme(theme)
        
        # 文件树组件
        self.file_tree.set_theme(theme)
        
    def connect_signals(self):
        """连接信号和槽"""
        # 解码器信号
        self.decoder_wrapper.progress_updated.connect(self.on_file_progress)
        self.decoder_wrapper.file_finished.connect(self.on_file_finished)
        self.decoder_wrapper.all_finished.connect(self.on_all_finished)
        self.decoder_wrapper.error_occurred.connect(self.on_error)
        self.decoder_wrapper.log_message.connect(self.on_log_message)
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def browse_input_folder(self):
        """浏览输入文件夹"""
        folder = QFileDialog.getExistingDirectory(self, self.i18n_manager.tr('input_folder'))
        if folder:
            self.input_path_edit.setText(folder)
            # 自动扫描文件
            self.scan_files()
    
    def browse_output_folder(self):
        """浏览输出文件夹"""
        folder = QFileDialog.getExistingDirectory(self, self.i18n_manager.tr('output_folder'))
        if folder:
            self.output_path_edit.setText(folder)
    
    def scan_files(self):
        """扫描文件"""
        input_path = self.input_path_edit.text()
        if not input_path:
            return
        
        try:
            scan_result = self.decoder_wrapper.scan_folder(input_path)
            self.total_files = scan_result['total_files']
            ncm_count = len(scan_result['ncm_files'])
            other_count = len(scan_result['other_files'])
            
            self.log(f"{self.i18n_manager.tr('scan_complete')}: {self.total_files} files "
                    f"({ncm_count} NCM files, {other_count} other files)")
            
            # 更新文件树
            file_list = self.decoder_wrapper.get_file_list()
            self.file_tree.add_files(file_list, input_path)
            
            # 保存总文件数，用于进度计算
            self.total_files = scan_result['total_files']
            self.completed_files = 0
            
        except Exception as e:
            QMessageBox.critical(self, self.i18n_manager.tr('error'), 
                               f"{self.i18n_manager.tr('scan_failed')}: {e}")
            logging.error(f"扫描文件失败: {e}", exc_info=True)
    
    def start_decode(self):
        """开始解码"""
        input_path = self.input_path_edit.text()
        output_path = self.output_path_edit.text()
        max_threads = self.thread_spinbox.value()
        
        if not input_path:
            QMessageBox.warning(self, self.i18n_manager.tr('warning'), 
                              self.i18n_manager.tr('please_select_input'))
            return
        
        if not output_path:
            QMessageBox.warning(self, self.i18n_manager.tr('warning'), 
                              self.i18n_manager.tr('please_select_output'))
            return
        
        # 检查是否正在运行
        if self.decoder_wrapper.is_running():
            QMessageBox.warning(self, self.i18n_manager.tr('warning'), 
                              self.i18n_manager.tr('decoding_in_progress'))
            return
        
        # 重置状态
        self.completed_files = 0
        # 确保总文件数已设置（从扫描结果或文件列表）
        if not hasattr(self, 'total_files') or self.total_files == 0:
            file_list = self.decoder_wrapper.get_file_list()
            self.total_files = len(file_list) if file_list else 1
        self.progress_widget.reset()
        self.log_text.clear()
        
        # 更新UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.input_path_edit.setEnabled(False)
        self.output_path_edit.setEnabled(False)
        self.thread_spinbox.setEnabled(False)
        
        # 开始解码
        try:
            self.decoder_wrapper.decode_folder(input_path, output_path, max_threads)
            self.log(self.i18n_manager.tr('start_decoding').format(threads=max_threads))
        except Exception as e:
            QMessageBox.critical(self, self.i18n_manager.tr('error'), 
                               f"{self.i18n_manager.tr('start_decode_failed')}: {e}")
            logging.error(f"启动解码失败: {e}", exc_info=True)
            self.reset_ui_state()
    
    def stop_decode(self):
        """停止解码"""
        if self.decoder_wrapper.is_running():
            self.decoder_wrapper.stop()
            self.log(self.i18n_manager.tr('stopping'))
    
    def on_file_progress(self, file_path: str, current_bytes: int, total_bytes: int, finished: bool):
        """文件进度更新"""
        self.current_file_path = file_path
        self.progress_widget.update_current_file(file_path, current_bytes, total_bytes, finished)
        
        # 更新文件树
        if total_bytes > 0:
            progress_percent = int((current_bytes / total_bytes) * 100)
            self.file_tree.update_file_status(file_path, FileStatus.PROCESSING, progress_percent)
    
    def on_file_finished(self, file_path: str, success: bool, error: str, output_format: str):
        """文件完成"""
        self.completed_files += 1
        
        # 更新总进度（使用扫描时的总文件数，而不是动态增加）
        if not hasattr(self, 'total_files') or self.total_files == 0:
            # 如果没有设置总文件数，从文件树获取
            file_list = self.decoder_wrapper.get_file_list()
            self.total_files = len(file_list) if file_list else 1
        
        self.progress_widget.update_total_progress(self.completed_files, self.total_files)
        
        # 更新文件树
        if success:
            # 如果是已复制的文件（无需解码），使用 SKIPPED 状态
            # 检查中英文两种可能的返回值（向后兼容）
            if output_format == "已复制" or output_format == "Copied" or output_format == self.i18n_manager.tr('copied'):
                self.file_tree.update_file_status(file_path, FileStatus.SKIPPED)
                self.log(f"✓ {self.i18n_manager.tr('copied')}: {Path(file_path).name}")
            else:
                self.file_tree.update_file_status(file_path, FileStatus.COMPLETED)
                self.log(f"✓ {self.i18n_manager.tr('file_complete')}: {Path(file_path).name}")
        else:
            self.file_tree.update_file_status(file_path, FileStatus.FAILED, error=error)
            self.log(f"✗ {self.i18n_manager.tr('file_failed')}: {Path(file_path).name} - {error}")
    
    def on_all_finished(self):
        """所有文件完成"""
        self.log(self.i18n_manager.tr('all_files_complete'))
        self.reset_ui_state()
        QMessageBox.information(self, self.i18n_manager.tr('success'), 
                               self.i18n_manager.tr('all_files_complete'))
    
    def on_error(self, file_path: str, error: str):
        """错误处理"""
        self.log(f"{self.i18n_manager.tr('error')}: {error}")
        if file_path:
            self.file_tree.update_file_status(file_path, FileStatus.FAILED, error=error)
    
    def on_log_message(self, message: str):
        """日志消息"""
        self.log(message)
    
    def log(self, message: str):
        """添加日志"""
        self.log_text.append(message)
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        logging.info(message)
    
    def reset_ui_state(self):
        """重置UI状态"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.input_path_edit.setEnabled(True)
        self.output_path_edit.setEnabled(True)
        self.thread_spinbox.setEnabled(True)
        self.progress_widget.update_current_file("", 0, 0, True)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.decoder_wrapper.is_running():
            reply = QMessageBox.question(
                self, 
                self.i18n_manager.tr('confirm'), 
                self.i18n_manager.tr('confirm_exit'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.decoder_wrapper.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
