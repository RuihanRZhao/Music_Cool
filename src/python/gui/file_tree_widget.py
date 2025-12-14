"""
文件树显示组件 - 支持主题切换
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from pathlib import Path
from enum import Enum
from typing import Dict, Optional


class FileStatus(Enum):
    """文件状态枚举"""
    WAITING = "等待"
    PROCESSING = "处理中"
    COMPLETED = "完成"
    FAILED = "失败"
    SKIPPED = "已跳过"


class FileTreeWidget(QWidget):
    """文件树显示组件"""
    
    def __init__(self, parent=None, i18n_manager=None):
        super().__init__(parent)
        self.current_theme: Optional[Dict[str, str]] = None
        self.i18n_manager = i18n_manager
        self.init_ui()
        self.file_items = {}  # 文件路径 -> QTreeWidgetItem
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            self._tr('file_name'),
            self._tr('status'),
            self._tr('progress')
        ])
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        
        # 设置列宽
        header = self.tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.tree)
    
    def set_theme(self, theme: Dict[str, str]):
        """设置主题"""
        self.current_theme = theme
        
        # 文件树样式
        tree_style = f"""
            QTreeWidget {{
                background-color: {theme['bg_card']};
                border: 2px solid {theme['border']};
                border-radius: 8px;
                font-size: 11px;
                selection-background-color: {theme['primary']};
                selection-color: white;
                alternate-background-color: {theme['row_alt']};
            }}
            QTreeWidget::item {{
                padding: 5px;
                border-bottom: 1px solid {theme['border']};
            }}
            QTreeWidget::item:hover {{
                background-color: {theme['row_hover']};
            }}
            QTreeWidget::item:selected {{
                background-color: {theme['primary']};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {theme['header_bg']};
                color: {theme['header_text']};
                padding: 8px;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }}
        """
        self.tree.setStyleSheet(tree_style)
    
    def add_files(self, file_list: list, base_path: str = ""):
        """
        添加文件到树中
        
        Args:
            file_list: 文件信息列表，每个元素包含 'input_path' 和 'relative_path'
            base_path: 基础路径，用于计算相对路径
        """
        self.tree.clear()
        self.file_items.clear()
        
        base_path_obj = Path(base_path) if base_path else None
        
        # 按路径组织文件
        root_items = {}  # 路径 -> QTreeWidgetItem
        
        for file_info in file_list:
            file_path = Path(file_info['input_path'])
            rel_path = file_info.get('relative_path', file_path)
            
            # 计算显示路径
            if base_path_obj and file_path.is_relative_to(base_path_obj):
                display_path = file_path.relative_to(base_path_obj)
            else:
                display_path = rel_path
            
            # 创建路径项
            parts = display_path.parts
            current_path = Path()
            parent_item = None
            
            for i, part in enumerate(parts):
                current_path = current_path / part
                path_str = str(current_path)
                
                if path_str not in root_items:
                    if i == len(parts) - 1:
                        # 这是文件
                        item = QTreeWidgetItem([part, self._get_status_text(FileStatus.WAITING), "0%"])
                        item.setData(0, Qt.ItemDataRole.UserRole, str(file_path))
                        self.file_items[str(file_path)] = item
                    else:
                        # 这是目录
                        item = QTreeWidgetItem([part, "", ""])
                        item.setExpanded(True)
                        root_items[path_str] = item
                    
                    if parent_item:
                        parent_item.addChild(item)
                    else:
                        self.tree.addTopLevelItem(item)
                    
                    parent_item = item
                else:
                    parent_item = root_items[path_str]
        
        # 展开所有项
        self.tree.expandAll()
        
        # 初始化所有父文件夹的进度（从叶子节点向上更新）
        for file_path, item in self.file_items.items():
            self._update_parent_progress(item)
    
    def _get_status_color(self, status: FileStatus) -> Optional[QColor]:
        """根据状态获取颜色"""
        if not self.current_theme:
            return None
        
        if status == FileStatus.COMPLETED or status == FileStatus.SKIPPED:
            return QColor(self.current_theme['success'])
        elif status == FileStatus.PROCESSING:
            return QColor(self.current_theme['warning'])
        elif status == FileStatus.FAILED:
            return QColor(self.current_theme['error'])
        elif status == FileStatus.WAITING:
            return QColor(self.current_theme['text_tertiary'])
        return None
    
    def update_file_status(self, file_path: str, status: FileStatus, progress: int = 0, error: str = ""):
        """
        更新文件状态
        
        Args:
            file_path: 文件路径
            status: 文件状态
            progress: 进度百分比 (0-100)
            error: 错误信息（如果有）
        """
        if file_path not in self.file_items:
            return
        
        item = self.file_items[file_path]
        
        # 更新状态
        item.setText(1, self._get_status_text(status))
        
        # 更新进度和颜色
        status_color = self._get_status_color(status)
        
        if status == FileStatus.PROCESSING:
            item.setText(2, f"{progress}%")
            if status_color:
                item.setForeground(1, status_color)
                item.setForeground(2, status_color)
        elif status == FileStatus.COMPLETED:
            item.setText(2, "100%")
            if status_color:
                item.setForeground(1, status_color)
                item.setForeground(2, status_color)
        elif status == FileStatus.FAILED:
            item.setText(2, self._tr('file_failed'))
            if status_color:
                item.setForeground(1, status_color)
                item.setForeground(2, status_color)
            if error:
                item.setToolTip(1, error)
        elif status == FileStatus.SKIPPED:
            item.setText(2, self._tr('copied'))
            if status_color:
                item.setForeground(1, status_color)
                item.setForeground(2, status_color)
        else:
            item.setText(2, "")
            if status_color:
                item.setForeground(1, status_color)
                item.setForeground(2, status_color)
        
        # 更新父文件夹的进度
        self._update_parent_progress(item)
    
    def _update_parent_progress(self, item: QTreeWidgetItem):
        """更新父文件夹的进度显示"""
        parent = item.parent()
        if not parent:
            return
        
        # 统计子项的状态（只统计文件，不统计子文件夹）
        completed = 0
        total = 0
        processing = 0
        failed = 0
        waiting = 0
        
        for i in range(parent.childCount()):
            child = parent.child(i)
            # 检查是否是文件：有 UserRole 数据说明是文件
            file_path = child.data(0, Qt.ItemDataRole.UserRole)
            if file_path:  # 这是文件
                total += 1
                status_text = child.text(1)
                # 使用翻译后的文本进行比较
                if status_text == self._get_status_text(FileStatus.COMPLETED) or status_text == self._get_status_text(FileStatus.SKIPPED):
                    completed += 1
                elif status_text == self._get_status_text(FileStatus.PROCESSING):
                    processing += 1
                elif status_text == self._get_status_text(FileStatus.FAILED):
                    failed += 1
                elif status_text == self._get_status_text(FileStatus.WAITING) or not status_text:
                    waiting += 1
        
        # 更新父文件夹的显示
        if not self.current_theme:
            return
        
        if total > 0:
            if completed == total:
                # 全部完成
                parent.setText(1, self._tr('completed'))
                parent.setText(2, "100%")
                parent.setForeground(1, QColor(self.current_theme['success']))
                parent.setForeground(2, QColor(self.current_theme['success']))
            elif processing > 0:
                # 有进行中的
                progress_percent = int((completed / total) * 100)
                parent.setText(1, self._tr('processing'))
                parent.setText(2, f"{progress_percent}%")
                parent.setForeground(1, QColor(self.current_theme['warning']))
                parent.setForeground(2, QColor(self.current_theme['warning']))
            elif waiting > 0:
                # 有待处理的
                progress_percent = int((completed / total) * 100)
                if completed > 0:
                    parent.setText(1, self._tr('partially_complete'))
                    parent.setText(2, f"{progress_percent}%")
                    parent.setForeground(1, QColor(self.current_theme['primary']))
                    parent.setForeground(2, QColor(self.current_theme['primary']))
                else:
                    parent.setText(1, self._tr('waiting'))
                    parent.setText(2, "0%")
                    parent.setForeground(1, QColor(self.current_theme['text_tertiary']))
                    parent.setForeground(2, QColor(self.current_theme['text_tertiary']))
            elif failed == total:
                # 全部失败
                parent.setText(1, self._tr('file_failed'))
                parent.setText(2, self._tr('file_failed'))
                parent.setForeground(1, QColor(self.current_theme['error']))
                parent.setForeground(2, QColor(self.current_theme['error']))
            else:
                # 混合状态
                progress_percent = int((completed / total) * 100)
                parent.setText(1, self._tr('processing'))
                parent.setText(2, f"{progress_percent}%")
                parent.setForeground(1, QColor(self.current_theme['warning']))
                parent.setForeground(2, QColor(self.current_theme['warning']))
        else:
            # 没有文件，可能是空文件夹或只有子文件夹
            parent.setText(1, "")
            parent.setText(2, "")
            parent.setForeground(1, QColor(self.current_theme['text_tertiary']))
            parent.setForeground(2, QColor(self.current_theme['text_tertiary']))
        
        # 递归更新更上层的父文件夹
        if parent.parent():
            self._update_parent_progress(parent)
    
    def clear(self):
        """清空树"""
        self.tree.clear()
        self.file_items.clear()
    
    def get_selected_files(self) -> list:
        """获取选中的文件"""
        selected_items = self.tree.selectedItems()
        files = []
        for item in selected_items:
            file_path = item.data(0, Qt.ItemDataRole.UserRole)
            if file_path:
                files.append(file_path)
        return files
    
    def _tr(self, key: str) -> str:
        """获取翻译文本"""
        if self.i18n_manager:
            return self.i18n_manager.tr(key)
        # 默认返回中文（向后兼容）
        defaults = {
            'file_name': '文件',
            'status': '状态',
            'progress': '进度',
            'waiting': '等待',
            'processing': '处理中',
            'completed': '完成',
            'file_failed': '失败',
            'copied': '已复制',
            'partially_complete': '部分完成',
        }
        return defaults.get(key, key)
    
    def _get_status_text(self, status: FileStatus) -> str:
        """获取状态的翻译文本"""
        status_map = {
            FileStatus.WAITING: self._tr('waiting'),
            FileStatus.PROCESSING: self._tr('processing'),
            FileStatus.COMPLETED: self._tr('completed'),
            FileStatus.FAILED: self._tr('file_failed'),
            FileStatus.SKIPPED: self._tr('copied'),
        }
        return status_map.get(status, status.value)
    
    def update_texts(self, i18n_manager):
        """更新文本（语言切换时调用）"""
        self.i18n_manager = i18n_manager
        # 更新列标题
        self.tree.setHeaderLabels([
            self._tr('file_name'),
            self._tr('status'),
            self._tr('progress')
        ])
        # 更新所有文件项的状态文本
        for file_path, item in self.file_items.items():
            status_text = item.text(1)
            # 根据当前文本推断状态并更新
            if status_text == '等待' or status_text == 'Waiting':
                item.setText(1, self._get_status_text(FileStatus.WAITING))
            elif status_text == '处理中' or status_text == 'Processing':
                item.setText(1, self._get_status_text(FileStatus.PROCESSING))
            elif status_text == '完成' or status_text == 'Completed':
                item.setText(1, self._get_status_text(FileStatus.COMPLETED))
            elif status_text == '失败' or status_text == 'Failed':
                item.setText(1, self._get_status_text(FileStatus.FAILED))
            elif status_text == '已复制' or status_text == 'Copied':
                item.setText(1, self._get_status_text(FileStatus.SKIPPED))
        
        # 更新所有父文件夹的状态文本
        def update_parent_texts(parent_item):
            if not parent_item:
                return
            status_text = parent_item.text(1)
            if status_text:
                # 根据文本推断并更新
                if '完成' in status_text or 'Complete' in status_text:
                    if status_text == '完成' or status_text == 'Completed':
                        parent_item.setText(1, self._tr('completed'))
                elif '处理中' in status_text or 'Processing' in status_text:
                    parent_item.setText(1, self._tr('processing'))
                elif '等待' in status_text or 'Waiting' in status_text:
                    parent_item.setText(1, self._tr('waiting'))
                elif '失败' in status_text or 'Failed' in status_text:
                    parent_item.setText(1, self._tr('file_failed'))
            
            if parent_item.parent():
                update_parent_texts(parent_item.parent())
        
        # 更新所有父项
        for file_path, item in self.file_items.items():
            if item.parent():
                update_parent_texts(item.parent())
