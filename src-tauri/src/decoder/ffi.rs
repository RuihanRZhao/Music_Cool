//! C++ NCM 解码器的 FFI 绑定模块。
//!
//! 此模块定义了与 C++ 解码器库的 FFI 接口，通过 C ABI 调用 ncm_dump_with_progress_ffi 函数。

use std::os::raw::{c_char, c_int};

/// 对应 C++ 侧的 DecodeResultRaw 结构
#[repr(C)]
#[derive(Debug, Copy, Clone)]
pub struct DecodeResultRaw {
    pub success: bool,
}

/// 进度回调函数类型（C ABI）
///
/// file: UTF-8 C 字符串
/// current_bytes / total_bytes: 进度字节数
/// finished: 是否完成当前文件
pub type ProgressCallbackRaw =
    Option<unsafe extern "C" fn(file: *const c_char, current_bytes: c_int, total_bytes: c_int, finished: bool)>;

extern "C" {
    /// C ABI 解码函数：
    ///
    /// - input_path: 输入 NCM 文件路径（UTF-8 C 字符串）
    /// - output_dir: 输出目录路径（UTF-8 C 字符串）
    /// - cb: 进度回调（可为 nullptr）
    ///
    /// 返回解码结果（success 字段表示是否成功）
    pub fn ncm_dump_with_progress_ffi(
        input_path: *const c_char,
        output_dir: *const c_char,
        cb: ProgressCallbackRaw,
    ) -> DecodeResultRaw;
}



