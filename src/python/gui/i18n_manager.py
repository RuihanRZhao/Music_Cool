"""
国际化管理器 - 支持中英文切换
"""

import json
import locale
from pathlib import Path
from typing import Dict, Optional


class I18nManager:
    """国际化管理器类"""
    
    # 翻译字典
    TRANSLATIONS = {
        'zh_CN': {
            'app_title': 'NCM文件解码器',
            'settings': '设置',
            'theme': '主题',
            'language': '语言',
            'dark_theme': '暗色主题',
            'light_theme': '亮色主题',
            'chinese': '中文',
            'english': 'English',
            'input_folder': '输入文件夹',
            'output_folder': '输出文件夹',
            'max_threads': '最大线程数',
            'recommended_threads': '推荐: 4-8 线程',
            'browse': '浏览',
            'start_decode': '开始解码',
            'stop': '停止',
            'config': '配置',
            'file_list': '文件列表',
            'log': '日志',
            'select_ncm_folder': '选择包含NCM文件的文件夹...',
            'select_output_folder': '选择解码后文件的输出位置...',
            'file_name': '文件名',
            'status': '状态',
            'progress': '进度',
            'total_progress': '总进度',
            'current_file': '当前文件',
            'completed': '已完成',
            'processing': '处理中',
            'waiting': '等待中',
            'error': '错误',
            'success': '成功',
            'ok': '确定',
            'cancel': '取消',
            'settings_title': '设置',
            'select_language': '选择语言',
            'select_theme': '选择主题',
            'no_files_found': '未找到NCM文件',
            'decoding_complete': '解码完成',
            'decoding_stopped': '解码已停止',
            'please_select_folders': '请选择输入和输出文件夹',
            'scan_complete': '扫描完成',
            'scan_failed': '扫描文件失败',
            'please_select_input': '请选择输入文件夹',
            'please_select_output': '请选择输出文件夹',
            'decoding_in_progress': '解码任务正在运行中',
            'start_decode_failed': '启动解码失败',
            'stopping': '正在停止解码...',
            'all_files_complete': '所有文件处理完成！',
            'confirm': '确认',
            'confirm_exit': '解码任务正在运行中，确定要退出吗？',
            'yes': '是',
            'no': '否',
            'copied': '已复制',
            'file_complete': '完成',
            'file_failed': '失败',
            'start_decoding': '开始解码，使用 {threads} 个线程',
            'warning': '警告',
            'files': '文件',
            'waiting': '等待开始...',
            'partially_complete': '部分完成',
        },
        'en_US': {
            'app_title': 'NCM File Decoder',
            'settings': 'Settings',
            'theme': 'Theme',
            'language': 'Language',
            'dark_theme': 'Dark Theme',
            'light_theme': 'Light Theme',
            'chinese': '中文',
            'english': 'English',
            'input_folder': 'Input Folder',
            'output_folder': 'Output Folder',
            'max_threads': 'Max Threads',
            'recommended_threads': 'Recommended: 4-8 threads',
            'browse': 'Browse',
            'start_decode': 'Start Decode',
            'stop': 'Stop',
            'config': 'Configuration',
            'file_list': 'File List',
            'log': 'Log',
            'select_ncm_folder': 'Select folder containing NCM files...',
            'select_output_folder': 'Select output location for decoded files...',
            'file_name': 'File Name',
            'status': 'Status',
            'progress': 'Progress',
            'total_progress': 'Total Progress',
            'current_file': 'Current File',
            'completed': 'Completed',
            'processing': 'Processing',
            'waiting': 'Waiting',
            'error': 'Error',
            'success': 'Success',
            'ok': 'OK',
            'cancel': 'Cancel',
            'settings_title': 'Settings',
            'select_language': 'Select Language',
            'select_theme': 'Select Theme',
            'no_files_found': 'No NCM files found',
            'decoding_complete': 'Decoding complete',
            'decoding_stopped': 'Decoding stopped',
            'please_select_folders': 'Please select input and output folders',
            'scan_complete': 'Scan complete',
            'scan_failed': 'Scan failed',
            'please_select_input': 'Please select input folder',
            'please_select_output': 'Please select output folder',
            'decoding_in_progress': 'Decoding task is in progress',
            'start_decode_failed': 'Failed to start decoding',
            'stopping': 'Stopping decoding...',
            'all_files_complete': 'All files processed!',
            'confirm': 'Confirm',
            'confirm_exit': 'Decoding task is in progress. Are you sure you want to exit?',
            'yes': 'Yes',
            'no': 'No',
            'copied': 'Copied',
            'file_complete': 'Complete',
            'file_failed': 'Failed',
            'start_decoding': 'Starting decode with {threads} threads',
            'warning': 'Warning',
            'files': 'files',
            'waiting': 'Waiting...',
            'partially_complete': 'Partially Complete',
        }
    }
    
    SUPPORTED_LANGUAGES = {
        'zh_CN': '中文',
        'en_US': 'English',
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化国际化管理器
        
        Args:
            config_path: 配置文件路径，默认为项目根目录下的 config.json
        """
        if config_path is None:
            # 默认配置文件路径：项目根目录/config.json
            project_root = Path(__file__).parent.parent.parent.parent
            config_path = project_root / 'config.json'
        self.config_path = config_path
        
        # 加载语言设置
        self.current_language = self.load_language()
    
    def detect_system_language(self) -> str:
        """
        检测系统语言
        
        Returns:
            语言代码 ('zh_CN' 或 'en_US')
        """
        try:
            system_lang, _ = locale.getdefaultlocale()
            if system_lang:
                if 'zh' in system_lang.lower() or 'chinese' in system_lang.lower():
                    return 'zh_CN'
        except (ValueError, AttributeError):
            pass
        return 'en_US'  # 默认英文
    
    def load_language(self) -> str:
        """
        从配置文件加载语言设置
        
        Returns:
            语言代码 ('zh_CN' 或 'en_US')
        """
        if not self.config_path.exists():
            return self.detect_system_language()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                language = config.get('language', None)
                if language and language in self.SUPPORTED_LANGUAGES:
                    return language
        except (json.JSONDecodeError, IOError, KeyError):
            pass
        
        return self.detect_system_language()
    
    def save_language(self, language: str) -> bool:
        """
        保存语言设置到配置文件
        
        Args:
            language: 语言代码 ('zh_CN' 或 'en_US')
            
        Returns:
            是否保存成功
        """
        if language not in self.SUPPORTED_LANGUAGES:
            return False
        
        try:
            config = {}
            if self.config_path.exists():
                try:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except (json.JSONDecodeError, IOError):
                    config = {}
            
            config['language'] = language
            
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.current_language = language
            return True
        except IOError:
            return False
    
    def tr(self, key: str) -> str:
        """
        获取翻译文本
        
        Args:
            key: 翻译键
            
        Returns:
            翻译后的文本，如果找不到则返回键本身
        """
        translations = self.TRANSLATIONS.get(self.current_language, self.TRANSLATIONS['en_US'])
        return translations.get(key, key)
    
    def get_language_name(self, language_code: str) -> str:
        """
        获取语言显示名称
        
        Args:
            language_code: 语言代码
            
        Returns:
            语言显示名称
        """
        return self.SUPPORTED_LANGUAGES.get(language_code, language_code)
