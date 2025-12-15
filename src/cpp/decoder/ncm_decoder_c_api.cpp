#include "decoder/ncm_decoder_c_api.h"
#include <string>

using namespace ncm_decoder;

extern "C" DecodeResultRaw ncm_dump_with_progress_ffi(const char* input_path,
                                                       const char* output_dir,
                                                       ProgressCallbackRaw cb) {
    if (!input_path || !output_dir) {
        return {false};
    }

    std::string in_path(input_path);
    std::string out_dir(output_dir);

    ProgressCallback cpp_callback = nullptr;
    if (cb) {
        // 将 C 回调包装为 C++ std::function
        cpp_callback = [cb](const std::string& file,
                            int current_bytes,
                            int total_bytes,
                            bool finished) {
            cb(file.c_str(), current_bytes, total_bytes, finished);
        };
    }

    try {
        DecodeResult result = ncmDumpWithProgress(in_path, out_dir, cpp_callback);
        return {result.success};
    } catch (...) {
        // 为了稳健性，捕获所有异常并返回失败
        return {false};
    }
}

