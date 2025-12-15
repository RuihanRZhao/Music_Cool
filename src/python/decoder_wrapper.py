"""
解码器 Python 包装类
处理文件遍历、目录结构维护和 Qt 信号

注意：此文件属于旧版 Python GUI 的一部分，但其中的解码器调用逻辑
仍可作为参考实现。Tauri 版本使用 Rust FFI 直接调用 C++ 解码器。
"""

import os
import shutil
import sys
from pathlib import Path
from typing import List, Dict, Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal, QThread, pyqtSlot
import logging

# Try to add MinGW DLL directory to Python's DLL search path
# This is needed for MinGW-compiled modules on Windows
try:
    mingw_bin_paths = [
        r"D:\msys64\mingw64\bin",
        r"C:\msys64\mingw64\bin",
        r"C:\mingw64\bin",
    ]
    # Also check PATH environment variable
    path_env = os.environ.get("PATH", "")
    for path in path_env.split(os.pathsep):
        if "mingw" in path.lower() and "bin" in path.lower():
            mingw_bin_paths.insert(0, path)
    
    for mingw_path in mingw_bin_paths:
        if os.path.exists(mingw_path):
            os.add_dll_directory(mingw_path)
            break
except Exception:
    pass

try:
    import ncm_decoder
except ImportError:
    # 如果导入失败，尝试从build目录导入
    build_path = Path(__file__).parent.parent.parent / "build"
    if build_path.exists():
        sys.path.insert(0, str(build_path))
    try:
        import ncm_decoder
    except ImportError as e2:
        raise ImportError(
            f"无法导入ncm_decoder模块。请先编译C++扩展模块。\n"
            f"错误详情: {e2}\n"
            f"运行: cd src/cpp && mkdir build && cd build && cmake .. && cmake --build ."
        )


class DecoderWorker(QThread):
    """解码工作线程"""
    
    # 信号定义
    file_progress = pyqtSignal(str, int, int, bool)  # 文件路径, 当前字节, 总字节, 完成
    file_finished = pyqtSignal(str, bool, str, str)  # 文件路径, 成功, 错误信息, 输出格式
    all_finished = pyqtSignal()
    error_occurred = pyqtSignal(str, str)  # 文件路径, 错误信息
    
    def __init__(self, tasks: List[Dict], max_threads: int = 4):
        super().__init__()
        self.tasks = tasks
        self.max_threads = max_threads
        self.decoder_manager = None
        self._stop_requested = False
        
    def run(self):
        """执行解码任务"""
        try:
            self.decoder_manager = ncm_decoder.DecoderManager(self.max_threads)
            
            # 添加所有任务
            for task in self.tasks:
                if self._stop_requested:
                    break
                    
                input_path = task['input_path']
                output_path = task['output_path']
                
                # 创建进度回调
                def make_progress_callback(file_path):
                    def callback(file, current_bytes, total_bytes, finished):
                        if not self._stop_requested:
                            self.file_progress.emit(file_path, current_bytes, total_bytes, finished)
                    return callback
                
                progress_cb = make_progress_callback(input_path)
                
                # 添加解码任务
                self.decoder_manager.add_task(
                    input_path,
                    output_path,
                    progress_cb
                )
            
            # 等待所有任务完成
            if not self._stop_requested:
                # 轮询等待所有任务完成
                while True:
                    if self._stop_requested:
                        break
                    
                    progress = self.decoder_manager.get_progress()
                    completed = progress['completed']
                    total = progress['total']
                    
                    # 检查是否所有任务都完成
                    if completed >= total and total > 0:
                        # 获取最终结果
                        for file_info in progress['files']:
                            file_path = file_info['file']
                            success = file_info['success']
                            error = file_info['error']
                            output_format = ""  # 可以从DecodeResult获取
                            
                            self.file_finished.emit(file_path, success, error, output_format)
                        break
                    
                    # 等待一段时间再检查
                    self.msleep(100)  # 100ms
            
            if not self._stop_requested:
                self.all_finished.emit()
                
        except Exception as e:
            logging.error(f"解码工作线程错误: {e}", exc_info=True)
            self.error_occurred.emit("", str(e))
    
    def stop(self):
        """停止解码"""
        self._stop_requested = True
        if self.decoder_manager:
            self.decoder_manager.stop()


class DecoderWrapper(QObject):
    """解码器包装类，处理文件遍历和Qt信号"""
    
    # 信号定义
    progress_updated = pyqtSignal(str, int, int, bool)  # 文件, 当前字节, 总字节, 完成
    file_finished = pyqtSignal(str, bool, str, str)  # 文件, 成功, 错误信息, 输出格式
    all_finished = pyqtSignal()
    error_occurred = pyqtSignal(str, str)  # 文件路径, 错误信息
    log_message = pyqtSignal(str)  # 日志消息
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.input_dir = None
        self.output_dir = None
        self.file_list = []  # 存储所有文件信息
        
    def scan_folder(self, input_dir: str) -> Dict:
        """
        扫描文件夹，返回文件列表和统计信息
        
        Returns:
            dict: 包含 'ncm_files', 'other_files', 'total_files' 的字典
        """
        input_path = Path(input_dir)
        if not input_path.exists() or not input_path.is_dir():
            raise ValueError(f"输入目录不存在或不是目录: {input_dir}")
        
        ncm_files = []
        other_files = []
        
        # 递归遍历所有文件
        for file_path in input_path.rglob('*'):
            if file_path.is_file():
                rel_path = file_path.relative_to(input_path)
                
                file_info = {
                    'input_path': str(file_path),
                    'relative_path': rel_path,
                    'is_ncm': file_path.suffix.lower() == '.ncm'
                }
                
                if file_info['is_ncm']:
                    ncm_files.append(file_info)
                else:
                    other_files.append(file_info)
        
        self.file_list = ncm_files + other_files
        
        return {
            'ncm_files': ncm_files,
            'other_files': other_files,
            'total_files': len(self.file_list)
        }
    
    def decode_folder(self, input_dir: str, output_dir: str, max_threads: int = 4):
        """
        解码文件夹中的所有NCM文件，保留目录结构
        
        Args:
            input_dir: 输入文件夹路径
            output_dir: 输出文件夹路径
            max_threads: 最大线程数
        """
        if self.worker and self.worker.isRunning():
            raise RuntimeError("解码任务正在运行中，请先停止")
        
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # 扫描文件夹
        scan_result = self.scan_folder(input_dir)
        self.log_message.emit(f"扫描完成: 找到 {scan_result['total_files']} 个文件 "
                             f"({len(scan_result['ncm_files'])} 个NCM文件, "
                             f"{len(scan_result['other_files'])} 个其他文件)")
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 准备解码任务
        tasks = []
        
        # NCM文件解码任务
        for file_info in scan_result['ncm_files']:
            rel_path = file_info['relative_path']
            # 输出路径：输出目录 + 相对路径的父目录
            output_file_dir = self.output_dir / rel_path.parent
            output_file_dir.mkdir(parents=True, exist_ok=True)
            
            tasks.append({
                'input_path': file_info['input_path'],
                'output_path': str(output_file_dir),
                'relative_path': rel_path
            })
        
        # 复制非NCM文件
        for file_info in scan_result['other_files']:
            rel_path = file_info['relative_path']
            output_file_path = self.output_dir / rel_path
            output_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                shutil.copy2(file_info['input_path'], output_file_path)
                self.log_message.emit(f"已复制: {rel_path}")
                # 发送文件完成信号，标记为已跳过（无需解码）
                self.file_finished.emit(file_info['input_path'], True, "", "已复制")
            except Exception as e:
                error_msg = f"复制文件失败 {rel_path}: {e}"
                self.log_message.emit(error_msg)
                self.error_occurred.emit(file_info['input_path'], error_msg)
                # 发送文件完成信号，标记为失败
                self.file_finished.emit(file_info['input_path'], False, error_msg, "")
        
        if not tasks:
            self.log_message.emit("没有找到NCM文件需要解码")
            self.all_finished.emit()
            return
        
        # 创建并启动工作线程
        self.worker = DecoderWorker(tasks, max_threads)
        self.worker.file_progress.connect(self.progress_updated)
        self.worker.file_finished.connect(self.file_finished)
        self.worker.all_finished.connect(self.all_finished)
        self.worker.error_occurred.connect(self.error_occurred)
        
        self.log_message.emit(f"开始解码 {len(tasks)} 个NCM文件，使用 {max_threads} 个线程")
        self.worker.start()
    
    def stop(self):
        """停止解码"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            self.log_message.emit("解码已停止")
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.worker is not None and self.worker.isRunning()
    
    def get_file_list(self) -> List[Dict]:
        """获取文件列表"""
        return self.file_list.copy()
