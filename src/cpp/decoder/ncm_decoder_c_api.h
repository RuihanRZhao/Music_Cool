#pragma once

#include "decoder/ncm_decoder.h"

// C 语言 ABI 的 NCM 解码接口，用于 Rust FFI
extern "C" {

// C 风格进度回调：
// file: UTF-8 文件路径
// current_bytes / total_bytes: 进度字节数
// finished: 当前文件是否已完成
using ProgressCallbackRaw = void (*)(const char* file,
                                     int current_bytes,
                                     int total_bytes,
                                     bool finished);

// 精简版解码结果，仅暴露 success，避免字符串所有权问题
struct DecodeResultRaw {
    bool success;
};

// C ABI 包装函数：
// input_path: 输入 NCM 文件路径（UTF-8）
// output_dir: 输出目录路径（UTF-8）
// cb: 进度回调（可为 nullptr）
DecodeResultRaw ncm_dump_with_progress_ffi(const char* input_path,
                                           const char* output_dir,
                                           ProgressCallbackRaw cb);

} // extern "C"

