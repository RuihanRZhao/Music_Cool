#include <pybind11/pybind11.h>
#include <pybind11/functional.h>
#include <pybind11/stl.h>
#include <string>
#include <vector>
#include <map>
#include <mutex>
#include <thread>
#include <atomic>
#include <stdexcept>
#include <chrono>
#include <memory>
#include "decoder/ncm_decoder.h"
#include "decoder/thread_pool.h"

namespace py = pybind11;
using namespace ncm_decoder;

// 解码任务结构
struct DecodeTask {
    std::string input_path;
    std::string output_path;
    py::function progress_callback;
    
    DecodeTask(const std::string& in, const std::string& out, py::function cb)
        : input_path(in), output_path(out), progress_callback(cb) {}
};

// 解码管理器类
class DecoderManager {
private:
    thread_pool pool;
    std::mutex progress_mutex;
    std::atomic<int> completed_files{0};
    std::atomic<int> total_files{0};
    std::atomic<bool> stopped{false};
    
    // 文件进度信息
    struct FileProgress {
        std::string file;
        int current_bytes;
        int total_bytes;
        bool finished;
        bool success;
        std::string error;
    };
    std::map<std::string, FileProgress> file_progress;
    
public:
    DecoderManager(int num_threads) : pool(num_threads > 0 ? num_threads : std::thread::hardware_concurrency()) {
        if (num_threads <= 0) {
            throw std::invalid_argument("Number of threads must be greater than 0");
        }
    }
    
    // 添加解码任务
    void add_task(const std::string& input_path, const std::string& output_path, py::function progress_callback) {
        if (stopped.load()) {
            throw std::runtime_error("Decoder manager has been stopped");
        }
        
        total_files++;
        
        // 创建C++进度回调，包装Python回调
        ProgressCallback cpp_callback = nullptr;
        if (!progress_callback.is_none()) {
            // 确保在持有 GIL 的情况下进行操作
            py::gil_scoped_acquire gil;
            
            // 获取 PyObject* 并增加引用计数
            // 这样可以在没有 GIL 的情况下安全地存储和传递
            PyObject* callback_ptr = progress_callback.ptr();
            Py_INCREF(callback_ptr);  // 增加引用计数，确保对象不会被释放
            
            // 使用 shared_ptr 管理 PyObject* 的生命周期
            auto callback_shared = std::shared_ptr<PyObject>(callback_ptr, [](PyObject* obj) {
                // 自定义删除器：在持有 GIL 的情况下减少引用计数
                if (obj) {
                    py::gil_scoped_acquire acquire;
                    Py_DECREF(obj);
                }
            });
            
            cpp_callback = [this, callback_shared, input_path](const std::string& file, 
                                                                int current_bytes, 
                                                                int total_bytes, 
                                                                bool finished) {
                try {
                    // 更新内部进度信息（不需要 GIL）
                    {
                        std::lock_guard<std::mutex> lock(progress_mutex);
                        file_progress[file] = {file, current_bytes, total_bytes, finished, false, ""};
                    }
                    
                    // 调用Python回调（需要 GIL）
                    {
                        py::gil_scoped_acquire acquire;
                        if (callback_shared.get()) {
                            // 直接使用 py::function，因为我们拥有引用
                            // reinterpret_borrow 创建一个临时借用，不会增加引用计数
                            py::function callback = py::reinterpret_borrow<py::function>(callback_shared.get());
                            callback(file, current_bytes, total_bytes, finished);
                        }
                    }
                } catch (const std::exception& e) {
                    // 忽略回调异常，继续处理
                } catch (...) {
                    // 捕获所有异常，避免崩溃
                }
            };
        }
        
        // 提交任务到线程池
        pool.enqueue([this, input_path, output_path, cpp_callback]() {
            if (stopped.load()) {
                return;
            }
            
            DecodeResult result = ncmDumpWithProgress(input_path, output_path, cpp_callback);
            
            // 更新完成状态
            {
                std::lock_guard<std::mutex> lock(progress_mutex);
                if (file_progress.find(input_path) != file_progress.end()) {
                    file_progress[input_path].finished = true;
                    file_progress[input_path].success = result.success;
                    file_progress[input_path].error = result.error_message;
                } else {
                    file_progress[input_path] = {
                        input_path, 0, 0, true, result.success, result.error_message
                    };
                }
            }
            
            completed_files++;
        });
    }
    
    // 获取进度信息
    py::dict get_progress() {
        std::lock_guard<std::mutex> lock(progress_mutex);
        
        py::dict progress_dict;
        progress_dict["completed"] = completed_files.load();
        progress_dict["total"] = total_files.load();
        
        py::list files_list;
        for (const auto& [file, prog] : file_progress) {
            py::dict file_dict;
            file_dict["file"] = prog.file;
            file_dict["current_bytes"] = prog.current_bytes;
            file_dict["total_bytes"] = prog.total_bytes;
            file_dict["finished"] = prog.finished;
            file_dict["success"] = prog.success;
            file_dict["error"] = prog.error;
            files_list.append(file_dict);
        }
        progress_dict["files"] = files_list;
        
        return progress_dict;
    }
    
    // 停止解码
    void stop() {
        stopped.store(true);
    }
    
    // 等待所有任务完成
    void wait() {
        // 轮询等待所有任务完成
        while (true) {
            {
                std::lock_guard<std::mutex> lock(progress_mutex);
                if (completed_files.load() >= total_files.load() && total_files.load() > 0) {
                    break;
                }
            }
            // 释放锁，等待一段时间（避免在持有锁时等待）
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }
    
    // 重置状态
    void reset() {
        std::lock_guard<std::mutex> lock(progress_mutex);
        completed_files = 0;
        total_files = 0;
        file_progress.clear();
        stopped.store(false);
    }
};

// 单个文件解码函数（Python绑定）
DecodeResult decode_file(const std::string& input_path, 
                         const std::string& output_path,
                         py::function progress_callback = py::none()) {
    ProgressCallback cpp_callback = nullptr;
    
    if (!progress_callback.is_none()) {
        // 确保在持有 GIL 的情况下进行操作
        py::gil_scoped_acquire gil;
        
        // 获取 PyObject* 并增加引用计数
        PyObject* callback_ptr = progress_callback.ptr();
        Py_INCREF(callback_ptr);
        
        // 使用 shared_ptr 管理 PyObject* 的生命周期
        auto callback_shared = std::shared_ptr<PyObject>(callback_ptr, [](PyObject* obj) {
            if (obj) {
                py::gil_scoped_acquire acquire;
                Py_DECREF(obj);
            }
        });
        
        cpp_callback = [callback_shared](const std::string& file, 
                                        int current_bytes, 
                                        int total_bytes, 
                                        bool finished) {
            try {
                py::gil_scoped_acquire acquire;
                if (callback_shared.get()) {
                    // 直接使用 py::function，因为我们拥有引用
                    // reinterpret_borrow 创建一个临时借用，不会增加引用计数
                    py::function callback = py::reinterpret_borrow<py::function>(callback_shared.get());
                    callback(file, current_bytes, total_bytes, finished);
                }
            } catch (const std::exception& e) {
                // 忽略回调异常
            } catch (...) {
                // 捕获所有异常
            }
        };
    }
    
    return ncmDumpWithProgress(input_path, output_path, cpp_callback);
}

PYBIND11_MODULE(ncm_decoder, m) {
    m.doc() = "NCM file decoder with progress callback support";
    
    // 导出DecodeResult结构
    py::class_<DecodeResult>(m, "DecodeResult")
        .def(py::init<>())
        .def_readwrite("success", &DecodeResult::success)
        .def_readwrite("error_message", &DecodeResult::error_message)
        .def_readwrite("output_format", &DecodeResult::output_format)
        .def_readwrite("output_path", &DecodeResult::output_path);
    
    // 导出单个文件解码函数
    m.def("decode_file", &decode_file,
          "Decode a single NCM file",
          py::arg("input_path"),
          py::arg("output_path"),
          py::arg("progress_callback") = py::none());
    
    // 导出DecoderManager类
    py::class_<DecoderManager>(m, "DecoderManager")
        .def(py::init<int>(), "Initialize decoder manager with specified number of threads",
             py::arg("num_threads"))
        .def("add_task", &DecoderManager::add_task,
             "Add a decode task to the queue",
             py::arg("input_path"),
             py::arg("output_path"),
             py::arg("progress_callback") = py::none())
        .def("get_progress", &DecoderManager::get_progress,
             "Get current progress information")
        .def("stop", &DecoderManager::stop,
             "Stop processing new tasks")
        .def("wait", &DecoderManager::wait,
             "Wait for all tasks to complete")
        .def("reset", &DecoderManager::reset,
             "Reset the decoder manager state");
}
