"""
进度显示组件 - 支持主题切换
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt
from typing import Dict


class ProgressWidget(QWidget):
    """进度显示组件"""
    
    def __init__(self, parent=None, i18n_manager=None):
        # #region agent log
        import json, os
        log_path = r'e:\Tools\CloudMusicDecoder\.cursor\debug.log'
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"progress_widget.py:13","message":"ProgressWidget.__init__ entry","data":{"parent_type":type(parent).__name__ if parent else "None","i18n_manager_type":type(i18n_manager).__name__ if i18n_manager else "None"},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        super().__init__(parent)
        self.current_theme = None
        self.i18n_manager = i18n_manager
        # #region agent log
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"progress_widget.py:17","message":"ProgressWidget.__init__ after super()","data":{"i18n_manager_set":self.i18n_manager is not None},"timestamp":int(__import__('time').time()*1000)})+'\n')
        # #endregion
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 总进度
        self.total_label = QLabel(self._tr('total_progress'))
        self.total_progress = QProgressBar()
        self.total_progress.setMinimum(0)
        self.total_progress.setMaximum(100)
        self.total_progress.setValue(0)
        self.total_progress.setTextVisible(True)
        self.total_progress.setFormat(f"%p% (%v/%m {self._tr('files')})")
        
        total_layout = QVBoxLayout()
        total_layout.setSpacing(8)
        total_layout.addWidget(self.total_label)
        total_layout.addWidget(self.total_progress)
        
        # 当前文件进度
        self.current_label = QLabel(self._tr('current_file'))
        self.current_file_label = QLabel(self._tr('waiting'))
        self.current_file_label.setWordWrap(True)
        self.current_file_progress = QProgressBar()
        self.current_file_progress.setMinimum(0)
        self.current_file_progress.setMaximum(100)
        self.current_file_progress.setValue(0)
        self.current_file_progress.setTextVisible(True)
        self.current_file_progress.setFormat("%p%")
        
        # 当前文件字节信息
        self.current_bytes_label = QLabel("")
        
        current_layout = QVBoxLayout()
        current_layout.setSpacing(8)
        current_layout.addWidget(self.current_label)
        current_layout.addWidget(self.current_file_label)
        current_layout.addWidget(self.current_file_progress)
        current_layout.addWidget(self.current_bytes_label)
        
        # 添加到主布局
        layout.addLayout(total_layout)
        layout.addLayout(current_layout)
        layout.addStretch()
    
    def set_theme(self, theme: Dict[str, str]):
        """设置主题"""
        self.current_theme = theme
        
        # 标签样式
        label_style = f"""
            QLabel {{
                font-size: 13px;
                font-weight: bold;
                color: {theme['text_primary']};
                padding: 5px;
            }}
        """
        self.total_label.setStyleSheet(label_style)
        self.current_label.setStyleSheet(label_style)
        
        # 文件名标签
        self.current_file_label.setStyleSheet(f"""
            QLabel {{
                color: {theme['text_secondary']};
                font-size: 11px;
                padding: 5px;
            }}
        """)
        
        # 字节信息标签
        self.current_bytes_label.setStyleSheet(f"""
            QLabel {{
                color: {theme['text_tertiary']};
                font-size: 10px;
                padding: 5px;
            }}
        """)
        
        # 总进度条样式（主强调色渐变）
        total_progress_style = f"""
            QProgressBar {{
                border: 2px solid {theme['border']};
                border-radius: 8px;
                text-align: center;
                font-size: 11px;
                font-weight: bold;
                color: {theme['text_primary']};
                height: 30px;
                background-color: {theme['bg_card']};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme['primary']}, stop:1 {theme['primary_hover']});
                border-radius: 6px;
            }}
        """
        self.total_progress.setStyleSheet(total_progress_style)
        
        # 当前文件进度条样式（成功色渐变）
        current_progress_style = f"""
            QProgressBar {{
                border: 2px solid {theme['border']};
                border-radius: 8px;
                text-align: center;
                font-size: 11px;
                font-weight: bold;
                color: {theme['text_primary']};
                height: 25px;
                background-color: {theme['bg_card']};
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme['success']}, stop:1 {theme['success_hover']});
                border-radius: 6px;
            }}
        """
        self.current_file_progress.setStyleSheet(current_progress_style)
        
    def update_total_progress(self, completed: int, total: int):
        """更新总进度"""
        if total > 0:
            percentage = int((completed / total) * 100)
            self.total_progress.setMaximum(total)
            self.total_progress.setValue(completed)
            self.total_progress.setFormat(f"%p% ({completed}/{total} {self._tr('files')})")
        else:
            self.total_progress.setValue(0)
            self.total_progress.setFormat(f"0% (0/0 {self._tr('files')})")
    
    def update_current_file(self, file_path: str, current_bytes: int = 0, total_bytes: int = 0, finished: bool = False):
        """更新当前文件进度"""
        from pathlib import Path
        
        # 显示文件名（只显示文件名，不显示完整路径）
        file_name = Path(file_path).name if file_path else ""
        if file_name:
            self.current_file_label.setText(f"{self._tr('processing')}: {file_name}")
        else:
            self.current_file_label.setText(self._tr('waiting'))
        
        if total_bytes > 0 and not finished:
            percentage = int((current_bytes / total_bytes) * 100)
            self.current_file_progress.setMaximum(total_bytes)
            self.current_file_progress.setValue(current_bytes)
            self.current_file_progress.setFormat(f"%p%")
            
            # 格式化字节数
            current_mb = current_bytes / (1024 * 1024)
            total_mb = total_bytes / (1024 * 1024)
            self.current_bytes_label.setText(f"{current_mb:.2f} MB / {total_mb:.2f} MB")
        elif finished:
            self.current_file_progress.setValue(self.current_file_progress.maximum())
            self.current_file_progress.setFormat("100%")
            self.current_bytes_label.setText(self._tr('completed'))
        else:
            self.current_file_progress.setValue(0)
            self.current_file_progress.setFormat("0%")
            self.current_bytes_label.setText("")
    
    def reset(self):
        """重置进度显示"""
        self.total_progress.setValue(0)
        self.total_progress.setMaximum(100)
        self.current_file_progress.setValue(0)
        self.current_file_progress.setMaximum(100)
        self.current_file_label.setText(self._tr('waiting'))
        self.current_bytes_label.setText("")
    
    def _tr(self, key: str) -> str:
        """获取翻译文本"""
        if self.i18n_manager:
            return self.i18n_manager.tr(key)
        # 默认返回中文（向后兼容）
        defaults = {
            'total_progress': '总进度',
            'current_file': '当前文件',
            'waiting': '等待开始...',
            'processing': '正在处理',
            'completed': '完成',
            'files': '文件',
        }
        return defaults.get(key, key)
    
    def update_texts(self, i18n_manager):
        """更新文本（语言切换时调用）"""
        self.i18n_manager = i18n_manager
        self.total_label.setText(self._tr('total_progress'))
        self.current_label.setText(self._tr('current_file'))
        if not self.current_file_label.text() or self.current_file_label.text() == '等待开始...':
            self.current_file_label.setText(self._tr('waiting'))
