use std::env;
use std::path::PathBuf;

fn main() {
    tauri_build::build();

    // 链接 C++ 解码器静态库
    link_ncm_decoder();
}

fn link_ncm_decoder() {
    // 获取项目根目录
    let manifest_dir = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap());
    let project_root = manifest_dir.parent().unwrap();
    
    // 构建目录路径
    let build_dir = project_root.join("build");
    
    // 根据平台确定库路径
    // 注意：本项目仅支持 MSVC 工具链（Windows）或标准 Unix 工具链（Linux/macOS）
    let lib_path = if cfg!(target_os = "windows") {
        // Windows: 仅支持 MSVC，查找 .lib 文件
        let release_path = build_dir.join("Release").join("ncm_decoder_static.lib");
        let debug_path = build_dir.join("Debug").join("ncm_decoder_static.lib");
        let direct_path = build_dir.join("ncm_decoder_static.lib");
        
        if release_path.exists() {
            release_path
        } else if debug_path.exists() {
            debug_path
        } else if direct_path.exists() {
            direct_path
        } else {
            // 找不到 .lib，给出明确错误提示
            direct_path
        }
    } else {
        // Linux/macOS: 使用标准 Unix 工具链
        build_dir.join("libncm_decoder_static.a")
    };

    // 检查库文件是否存在
    if lib_path.exists() {
        // 添加库搜索路径
        if let Some(parent) = lib_path.parent() {
            println!("cargo:rustc-link-search=native={}", parent.display());
        }
        
        // 链接静态库（去掉 lib 前缀和扩展名）
        // 无论是 .a 还是 .lib，链接方式都是 static=ncm_decoder_static
        println!("cargo:rustc-link-lib=static=ncm_decoder_static");
        
        // Windows MSVC 需要链接 OpenSSL 静态库（如果存在）
        // 注意：CMakeLists.txt 使用的文件名是 libcrypto_static.lib 和 libssl_static.lib
        if cfg!(target_os = "windows") {
            let openssl_lib_dir = project_root.join("src").join("shared").join("ext").join("lib");
            let crypto_lib = openssl_lib_dir.join("libcrypto_static.lib");
            let ssl_lib = openssl_lib_dir.join("libssl_static.lib");
            
            // 只有当 OpenSSL 库文件确实存在时才链接
            if crypto_lib.exists() && ssl_lib.exists() {
                println!("cargo:rustc-link-search=native={}", openssl_lib_dir.display());
                // MSVC 链接器在查找库时：
                // - rustc-link-lib=static=xxx 会查找 xxx.lib 或 libxxx.lib
                // - 但优先查找 xxx.lib，如果找不到才会查找 libxxx.lib
                // - 由于我们的文件是 libcrypto_static.lib，需要直接指定完整路径
                // 使用 rustc-link-arg 直接传递库文件路径给链接器
                // 注意：MSVC 链接器需要完整路径，使用反斜杠
                let crypto_path = crypto_lib.to_string_lossy().replace('/', "\\");
                let ssl_path = ssl_lib.to_string_lossy().replace('/', "\\");
                println!("cargo:rustc-link-arg={}", crypto_path);
                println!("cargo:rustc-link-arg={}", ssl_path);
            } else {
                // OpenSSL 库不存在，给出明确的错误信息
                println!("cargo:warning=OpenSSL 静态库未找到: {:?}", openssl_lib_dir);
                println!("cargo:warning=需要文件: libcrypto_static.lib 和 libssl_static.lib");
                println!("cargo:warning=C++ 解码器依赖 OpenSSL，请确保已编译并放置 OpenSSL 静态库到上述目录");
                println!("cargo:warning=这会导致链接错误，因为 C++ 代码使用了 AES 加密函数");
            }
        }
    } else {
        // 如果库不存在，给出警告但继续构建（开发时可能还没编译 C++ 库）
        let expected_format = if cfg!(target_os = "windows") {
            "ncm_decoder_static.lib (MSVC 格式)"
        } else {
            "libncm_decoder_static.a"
        };
        
        println!("cargo:warning=未找到 C++ 解码器静态库: {:?}", lib_path);
        println!("cargo:warning=期望格式: {}", expected_format);
        println!("cargo:warning=请先运行 CMake 构建静态库（使用 Visual Studio MSVC）:");
        println!("cargo:warning=  .\\scripts\\develop\\build_only.ps1");
        println!("cargo:warning=或手动:");
        println!("cargo:warning=  cd src/cpp");
        println!("cargo:warning=  mkdir -p build && cd build");
        if cfg!(target_os = "windows") {
            println!("cargo:warning=  cmake .. -G \"Visual Studio 18 2026\" -A x64 -DBUILD_PYTHON_BINDINGS=OFF");
            println!("cargo:warning=  (或使用其他 VS 版本: \"Visual Studio 17 2022\", \"Visual Studio 16 2019\", \"Visual Studio 15 2017\")");
        } else {
            println!("cargo:warning=  cmake .. -DBUILD_PYTHON_BINDINGS=OFF");
        }
        println!("cargo:warning=  cmake --build . --config Release --target ncm_decoder_static");
    }
    
    // 链接 C++ 标准库
    if cfg!(target_os = "windows") {
        // Windows MSVC: 自动链接 C++ 标准库，无需显式链接
    } else {
        // Unix-like: 需要链接 C++ 标准库
        println!("cargo:rustc-link-lib=stdc++");
    }
}


