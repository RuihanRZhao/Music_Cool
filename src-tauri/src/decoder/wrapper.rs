//! Rust 侧的解码器包装，通过 FFI 调用 C++ NCM 解码器。

use crate::importer::ThreadProgress;
use serde::Serialize;
use std::ffi::CString;
use std::os::raw::c_char;
use std::path::Path;
use std::sync::{Arc, Mutex};

use super::ffi;

#[derive(Debug, Clone, Serialize)]
pub struct DecodeResult {
    pub success: bool,
}

/// 解码单个 NCM 文件到目标目录
///
/// 通过 FFI 调用 C++ 解码器，并将进度回调映射到 ThreadProgress。
/// 注意：由于 C 回调函数的限制，实时进度更新较难实现，目前只在解码完成后更新进度。
pub async fn decode_ncm_to_dir<P: AsRef<Path>>(
    input: P,
    output_dir: P,
    progress: Arc<Mutex<ThreadProgress>>,
) -> DecodeResult {
    let input_path = match input.as_ref().to_str() {
        Some(p) => p,
        None => {
            eprintln!("输入路径包含无效 UTF-8: {:?}", input.as_ref());
            return DecodeResult { success: false };
        }
    };

    let output_dir_str = match output_dir.as_ref().to_str() {
        Some(p) => p,
        None => {
            eprintln!("输出目录路径包含无效 UTF-8: {:?}", output_dir.as_ref());
            return DecodeResult { success: false };
        }
    };

    // 转换为 C 字符串
    let input_cstr = match CString::new(input_path) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("转换输入路径失败: {}", e);
            return DecodeResult { success: false };
        }
    };

    let output_cstr = match CString::new(output_dir_str) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("转换输出目录路径失败: {}", e);
            return DecodeResult { success: false };
        }
    };

    // 使用传入的进度共享状态
    let progress_arc = progress;

    // 定义 C 回调函数（静态函数，目前仅用于日志）
    unsafe extern "C" fn progress_callback(
        file: *const c_char,
        current_bytes: i32,
        total_bytes: i32,
        finished: bool,
    ) {
        // 将 C 字符串转换为 Rust 字符串（仅用于日志）
        if let Ok(file_str) = std::ffi::CStr::from_ptr(file).to_str() {
            if finished {
                eprintln!("解码完成: {} ({}/{})", file_str, current_bytes, total_bytes);
            }
        }
    }

    // 调用 FFI 函数（在 tokio 的 blocking thread 中执行，因为 C++ 解码器可能是同步的）
    let progress_for_update = progress_arc.clone();
    let result = tokio::task::spawn_blocking(move || {
        let raw_result = unsafe {
            ffi::ncm_dump_with_progress_ffi(
                input_cstr.as_ptr(),
                output_cstr.as_ptr(),
                Some(progress_callback),
            )
        };
        
        // 在 blocking 线程中更新进度
        if let Ok(mut prog) = progress_for_update.lock() {
            if raw_result.success {
                prog.progress = 1.0;
                prog.processed_size = prog.current_size;
            } else {
                prog.progress = 0.0;
            }
        }
        
        raw_result
    })
    .await;

    match result {
        Ok(raw_result) => DecodeResult {
            success: raw_result.success,
        },
        Err(e) => {
            eprintln!("解码任务执行失败: {}", e);
            DecodeResult { success: false }
        }
    }
}



