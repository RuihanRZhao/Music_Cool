cmake_minimum_required(VERSION 3.20)
project(ncm_decoder)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Python first - prefer the Python from current environment
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

message(STATUS "Using Python executable: ${Python3_EXECUTABLE}")

# Get pybind11 CMake directory
set(pybind11_CMAKE_DIR "")

# Try method 1: get_cmake_dir()
execute_process(
    COMMAND ${Python3_EXECUTABLE} -c "import pybind11; print(pybind11.get_cmake_dir())"
    OUTPUT_VARIABLE pybind11_CMAKE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
    RESULT_VARIABLE pybind11_result
)

if(pybind11_result EQUAL 0 AND pybind11_CMAKE_DIR)
    string(STRIP "${pybind11_CMAKE_DIR}" pybind11_CMAKE_DIR)
    if(EXISTS "${pybind11_CMAKE_DIR}")
        list(APPEND CMAKE_PREFIX_PATH "${pybind11_CMAKE_DIR}")
        message(STATUS "Found pybind11 CMake dir: ${pybind11_CMAKE_DIR}")
    endif()
endif()

# Try method 2: alternative path (if method 1 failed)
if(NOT pybind11_CMAKE_DIR OR NOT EXISTS "${pybind11_CMAKE_DIR}")
    execute_process(
        COMMAND ${Python3_EXECUTABLE} -c "import pybind11; import os; print(os.path.join(os.path.dirname(pybind11.__file__), 'share', 'cmake', 'pybind11'))"
        OUTPUT_VARIABLE pybind11_CMAKE_DIR2
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
        RESULT_VARIABLE pybind11_result2
    )
    if(pybind11_result2 EQUAL 0 AND pybind11_CMAKE_DIR2)
        string(STRIP "${pybind11_CMAKE_DIR2}" pybind11_CMAKE_DIR2)
        if(EXISTS "${pybind11_CMAKE_DIR2}")
            list(APPEND CMAKE_PREFIX_PATH "${pybind11_CMAKE_DIR2}")
            message(STATUS "Found pybind11 CMake dir (alternative): ${pybind11_CMAKE_DIR2}")
        endif()
    endif()
endif()

# Now try to find pybind11 package
find_package(pybind11 QUIET)

if(NOT pybind11_FOUND)
    # If still not found, provide helpful error
    message(FATAL_ERROR "pybind11 not found. Please ensure:\n"
            "  1. pybind11 is installed: pip install pybind11\n"
            "  2. You are using the correct Python environment\n"
            "  3. Python executable: ${Python3_EXECUTABLE}")
endif()

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
)

set(BINDING_SOURCES
    python_binding.cpp
)

# Add MinGW compatibility source if using MinGW
if(MINGW)
    list(APPEND BINDING_SOURCES mingw_compat.cpp)
endif()

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
        # For MSVC, use static libraries
        set(OPENSSL_LIB_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../shared/ext/lib)
        set(OPENSSL_LIBS 
            ${OPENSSL_LIB_DIR}/libcrypto_static.lib
            ${OPENSSL_LIB_DIR}/libssl_static.lib
        )
    endif()
else()
    # For Linux/macOS, try to find OpenSSL via pkg-config or system paths
    find_package(OpenSSL REQUIRED)
    set(OPENSSL_LIBS OpenSSL::SSL OpenSSL::Crypto)
endif()

# Create Python module
pybind11_add_module(ncm_decoder
    ${BINDING_SOURCES}
    ${DECODER_SOURCES}
    ${SHARED_SOURCES}
)

# Link libraries
target_link_libraries(ncm_decoder PRIVATE
    ${OPENSSL_LIBS}
)

# For MinGW with MSVC-compiled OpenSSL, link additional runtime libraries
if(MINGW AND NOT OpenSSL_FOUND)
    # Link MinGW runtime libraries that provide __chkstk and other symbols
    # These are needed when linking MSVC-compiled static libraries with MinGW
    # __chkstk is provided by libgcc, we need to link it explicitly
    # Also need to ensure proper linking order
    target_link_libraries(ncm_decoder PRIVATE
        gcc
        mingwex
    )
    # Also set linker flags to ensure static linking and proper symbol resolution
    # Suppress .drectve warnings from MSVC-compiled static libraries
    set_target_properties(ncm_decoder PROPERTIES
        LINK_FLAGS "-static-libgcc -static-libstdc++ -Wl,--allow-multiple-definition -Wl,--no-warn-search-mismatch"
    )
    message(STATUS "Linking MinGW runtime libraries (gcc, mingwex) to resolve __chkstk")
endif()

# Set output directory
set_target_properties(ncm_decoder PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/../../build
)

# Windows specific settings
if(WIN32)
    target_compile_definitions(ncm_decoder PRIVATE VERSION_INFO=${EXAMPLE_VERSION_INFO})
endif()

# Compiler-specific options
if(MSVC)
    target_compile_options(ncm_decoder PRIVATE /W4)
else()
    target_compile_options(ncm_decoder PRIVATE -Wall -Wextra -Wpedantic)
endif()
