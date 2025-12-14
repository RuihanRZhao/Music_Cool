#pragma once

#include <string>
#include <functional>
#include <exception>

namespace ncm_decoder {

// 进度回调函数类型
// 参数: 文件名, 当前字节数, 总字节数, 是否完成
using ProgressCallback = std::function<void(const std::string& file, 
                                             int current_bytes, 
                                             int total_bytes, 
                                             bool finished)>;

// 解码结果
struct DecodeResult {
    bool success;
    std::string error_message;
    std::string output_format;  // "mp3", "flac"等
    std::string output_path;     // 输出文件路径
    
    DecodeResult() : success(false) {}
    DecodeResult(bool s, const std::string& err = "", 
                 const std::string& fmt = "", const std::string& path = "")
        : success(s), error_message(err), output_format(fmt), output_path(path) {}
};

// 解码函数（带进度回调）
// input_path: 输入NCM文件路径
// output_path: 输出目录路径（会在此目录下创建文件）
// callback: 进度回调函数（可选，可为nullptr）
DecodeResult ncmDumpWithProgress(const std::string& input_path,
                                  const std::string& output_path,
                                  ProgressCallback callback = nullptr);

} // namespace ncm_decoder
