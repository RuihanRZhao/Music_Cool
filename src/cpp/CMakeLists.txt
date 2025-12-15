cmake_minimum_required(VERSION 3.20)
project(ncm_decoder)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/decoder
    ${CMAKE_CURRENT_SOURCE_DIR}/../shared
    ${CMAKE_CURRENT_SOURCE_DIR}/../shared/ext/include
)

# Source files
set(SHARED_SOURCES
    ../shared/base64.cpp
    ../shared/pkcs7.cpp
)

set(DECODER_SOURCES
    decoder/ncm_decoder.cpp
    decoder/ncm_decoder_c_api.cpp
)

# OpenSSL library paths
if(WIN32)
    # Check if using MinGW
    if(MINGW)
        # For MinGW, try to use system OpenSSL first (if available via pkg-config)
        # Otherwise fall back to static libraries
        find_package(OpenSSL QUIET)
        if(OpenSSL_FOUND)
            set(OPENSSL_LIBS OpenSSL::SSL OpenSSL::Crypto)
            message(STATUS "Using system OpenSSL for MinGW")
        else()
            # Use static libraries (may have compatibility issues)
            set(OPENSSL_LIB_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../shared/ext/lib)
            set(OPENSSL_LIBS 
                ${OPENSSL_LIB_DIR}/libcrypto_static.lib
                ${OPENSSL_LIB_DIR}/libssl_static.lib
            )
            message(STATUS "Using static OpenSSL libraries (MSVC-compiled, may need MinGW runtime)")
        endif()
    else()
        # For MSVC, try to find system OpenSSL first
        find_package(OpenSSL QUIET)
        if(OpenSSL_FOUND)
            set(OPENSSL_LIBS OpenSSL::SSL OpenSSL::Crypto)
            message(STATUS "Using system OpenSSL for MSVC")
        else()
            # Fall back to static libraries
            set(OPENSSL_LIB_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../shared/ext/lib)
            set(OPENSSL_LIBS 
                ${OPENSSL_LIB_DIR}/libcrypto_static.lib
                ${OPENSSL_LIB_DIR}/libssl_static.lib
            )
            message(STATUS "Using static OpenSSL libraries from: ${OPENSSL_LIB_DIR}")
            message(STATUS "Note: If libraries are missing, you may need to build OpenSSL or install vcpkg")
        endif()
    endif()
else()
    # For Linux/macOS, try to find OpenSSL via pkg-config or system paths
    find_package(OpenSSL REQUIRED)
    set(OPENSSL_LIBS OpenSSL::SSL OpenSSL::Crypto)
endif()

# Create static library for Rust FFI
add_library(ncm_decoder_static STATIC
    ${DECODER_SOURCES}
    ${SHARED_SOURCES}
)

# Link OpenSSL to static library
target_link_libraries(ncm_decoder_static PRIVATE
    ${OPENSSL_LIBS}
)

# Set output directory for static library
set_target_properties(ncm_decoder_static PROPERTIES
    ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/../../build
)

# For MinGW with MSVC-compiled OpenSSL, link additional runtime libraries to static lib
if(MINGW AND NOT OpenSSL_FOUND)
    target_link_libraries(ncm_decoder_static PRIVATE
        gcc
        mingwex
    )
    set_target_properties(ncm_decoder_static PROPERTIES
        LINK_FLAGS "-static-libgcc -static-libstdc++ -Wl,--allow-multiple-definition -Wl,--no-warn-search-mismatch"
    )
endif()

# Compiler-specific options for static library
if(MSVC)
    # /utf-8: 将源文件和执行字符集视为 UTF-8，避免 C4819 警告
    target_compile_options(ncm_decoder_static PRIVATE /W4 /utf-8)
else()
    target_compile_options(ncm_decoder_static PRIVATE -Wall -Wextra -Wpedantic)
endif()
