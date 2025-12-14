#include "ncm_decoder.h"
#include <filesystem>
#include <sstream>
#include <fstream>
#include <memory>
#include <cstring>
#include <stdexcept>
#include "../../shared/base64.h"
#include "../../shared/pkcs7.h"
#include "../../shared/rapidjson/document.h"

#ifdef _WIN32
#include "../../shared/ext/include/openssl/aes.h"
#else
#include <openssl/aes.h>
#endif

using namespace std;
namespace fs = std::filesystem;

static char core_hex[] = "687A4852416D736F356B496E62617857";
static char mata_hex[] = "2331346C6A6B5F215C5D2630553C2728";

void hex2str(const char* src_, unsigned char* tgt_);
unsigned int little_int(const unsigned char* src_);

namespace ncm_decoder {

DecodeResult ncmDumpWithProgress(const std::string& input_path,
                                  const std::string& output_path,
                                  ProgressCallback callback) {
    try {
        unsigned char* core_key = new unsigned char[16];
        unsigned char* mata_key = new unsigned char[16];
        memset(core_key, 0, 16);
        memset(mata_key, 0, 16);
        hex2str(core_hex, core_key);
        hex2str(mata_hex, mata_key);

        fs::path raw_path = fs::u8path(input_path);
        
        // 检查输入文件是否存在
        if (!fs::exists(raw_path)) {
            delete[] core_key;
            delete[] mata_key;
            return DecodeResult(false, "Input file does not exist: " + input_path);
        }

        ifstream fp;
        fp.open(raw_path, ios::in | ios::binary);
        if (!fp.is_open()) {
            delete[] core_key;
            delete[] mata_key;
            return DecodeResult(false, "Failed to open input file: " + input_path);
        }

        // 获取文件大小用于进度计算
        fp.seekg(0, ios::end);
        size_t total_file_size = fp.tellg();
        fp.seekg(0, ios::beg);
        
        if (callback) {
            callback(input_path, 0, total_file_size, false);
        }

        fp.seekg(10, ios::cur);     // 8 + 2

        unsigned char* key_len_bin = new unsigned char[4];
        fp.read((char*)key_len_bin, 4);
        if (fp.gcount() != 4) {
            delete[] key_len_bin;
            delete[] core_key;
            delete[] mata_key;
            fp.close();
            return DecodeResult(false, "Failed to read key length");
        }
        unsigned int key_len = little_int(key_len_bin);
        delete[] key_len_bin;

        unsigned char* key_data_bin = new unsigned char[key_len];
        fp.read((char*)key_data_bin, key_len);
        if (fp.gcount() != key_len) {
            delete[] key_data_bin;
            delete[] core_key;
            delete[] mata_key;
            fp.close();
            return DecodeResult(false, "Failed to read key data");
        }
        for (unsigned int i = 0; i < key_len; i++) {
            key_data_bin[i] ^= 0x64;
        }

        int success;
        AES_KEY* key = new AES_KEY;
        success = AES_set_decrypt_key(core_key, 16 * 8, key);
        if (success != 0) {
            delete[] key_data_bin;
            delete key;
            delete[] core_key;
            delete[] mata_key;
            fp.close();
            return DecodeResult(false, "Failed to set AES decrypt key");
        }
        
        unsigned char* key_data_bin_de = new unsigned char[key_len];
        for (unsigned int i = 0; i < key_len; i += 16) {
            AES_ecb_encrypt(key_data_bin + i, key_data_bin_de + i, key, AES_DECRYPT);
        }
        delete[] key_data_bin;
        delete key;

        unsigned int key_len_unpad = pkcs7::pad_size(key_data_bin_de, key_len);
        unsigned char* key_data = new unsigned char[key_len_unpad];
        pkcs7::unpad(key_data_bin_de, key_len, key_data);
        delete[] key_data_bin_de;
        unsigned char* key_data_use = key_data + 17;

        unsigned char* key_box = new unsigned char[256];
        for (unsigned int i = 0; i < 256; i++) {
            key_box[i] = i;
        }

        {
            unsigned char c = 0;
            unsigned char last_byte = 0;
            unsigned int key_offset = 0;
            unsigned char swap = 0;
            for (unsigned int i = 0; i < 256; i++) {
                swap = key_box[i];
                c = (swap + last_byte + key_data_use[key_offset]) & 0xff;
                key_offset++;
                if (key_offset >= key_len_unpad - 17) {
                    key_offset = 0;
                }
                key_box[i] = key_box[c];
                key_box[c] = swap;
                last_byte = c;
            }
        }

        delete[] key_data;

        unsigned char* mata_len_bin = new unsigned char[4];
        fp.read((char*)mata_len_bin, 4);
        if (fp.gcount() != 4) {
            delete[] mata_len_bin;
            delete[] key_box;
            delete[] core_key;
            delete[] mata_key;
            fp.close();
            return DecodeResult(false, "Failed to read metadata length");
        }
        unsigned int mata_len = little_int(mata_len_bin);
        delete[] mata_len_bin;
        
        unsigned char* mata_data_bin = new unsigned char[mata_len];
        memset(mata_data_bin, 0, mata_len);
        fp.read((char*)mata_data_bin, mata_len);
        if (fp.gcount() != mata_len) {
            delete[] mata_data_bin;
            delete[] key_box;
            delete[] core_key;
            delete[] mata_key;
            fp.close();
            return DecodeResult(false, "Failed to read metadata");
        }

        for (unsigned int i = 0; i < mata_len; i++) {
            mata_data_bin[i] ^= 0x63;
        }
        
        string mata_data_base64 = string((char*)mata_data_bin + 22, mata_len - 22);
        string mata_data_str = base64_decode(mata_data_base64);
        delete[] mata_data_bin;
        mata_data_bin = (unsigned char*)mata_data_str.c_str();
        mata_len = (unsigned int)mata_data_str.length();

        key = new AES_KEY;
        AES_set_decrypt_key(mata_key, 16 * 8, key);
        unsigned char* mata_data_de = new unsigned char[mata_len];

        for (unsigned int i = 0; i < mata_len; i += 16) {
            AES_ecb_encrypt(mata_data_bin + i, mata_data_de + i, key, AES_DECRYPT);
        }
        delete key;

        unsigned int mata_len_unpad = pkcs7::pad_size(mata_data_de, mata_len);
        unsigned char* mata_data = new unsigned char[mata_len_unpad];
        pkcs7::unpad(mata_data_de, mata_len, mata_data);
        delete[] mata_data_de;

        string mata_str = string((char*)mata_data + 6, mata_len_unpad - 6);
        delete[] mata_data;

        rapidjson::Document dom;
        dom.Parse(mata_str.c_str(), mata_str.length());
        
        if (dom.HasParseError() || !dom.HasMember("format")) {
            delete[] key_box;
            delete[] core_key;
            delete[] mata_key;
            fp.close();
            return DecodeResult(false, "Failed to parse metadata JSON or missing format field");
        }

        fp.seekg(9, ios::cur);      // 4 + 5

        mata_len_bin = new unsigned char[4];
        fp.read((char*)mata_len_bin, 4);
        if (fp.gcount() != 4) {
            delete[] mata_len_bin;
            delete[] key_box;
            delete[] core_key;
            delete[] mata_key;
            fp.close();
            return DecodeResult(false, "Failed to read image data length");
        }
        mata_len = little_int(mata_len_bin);
        delete[] mata_len_bin;

        fp.seekg(mata_len, ios::cur);

        string extname = '.' + string(dom["format"].GetString());
        string output_format = dom["format"].GetString();

        // 创建输出目录（如果不存在）
        fs::path output_dir = fs::u8path(output_path);
        if (!fs::exists(output_dir)) {
            fs::create_directories(output_dir);
        }

        // 计算相对路径以保持目录结构
        fs::path tgt = output_dir / fs::u8path(raw_path.stem().u8string() + extname);

        ofstream of;
        of.open(tgt, ios::out | ios::binary);
        if (!of.is_open()) {
            delete[] key_box;
            delete[] core_key;
            delete[] mata_key;
            fp.close();
            return DecodeResult(false, "Failed to open output file: " + tgt.u8string());
        }

        // 计算音频数据的大小（从当前位置到文件末尾）
        size_t audio_start_pos = fp.tellg();
        size_t bytes_written = 0;

        unsigned char* buff = new unsigned char[0x8000];
        fp.read((char*)buff, 0x8000);
        unsigned int buff_len = (unsigned int)fp.gcount();
        while (buff_len) {
            for (unsigned int i = 1; i <= buff_len; i++) {
                unsigned int j = i & 0xff;
                buff[i - 1] ^= key_box[(key_box[j] + key_box[(key_box[j] + j) & 0xff]) & 0xff];
            }
            of.write((char*)buff, buff_len);
            bytes_written += buff_len;
            
            // 更新进度
            if (callback) {
                int current_bytes = audio_start_pos + bytes_written;
                callback(input_path, current_bytes, total_file_size, false);
            }
            
            fp.read((char*)buff, 0x8000);
            buff_len = (unsigned int)fp.gcount();
        }
        of.close();
        fp.close();

        delete[] buff;
        delete[] key_box;
        delete[] core_key;
        delete[] mata_key;

        // 完成回调
        if (callback) {
            callback(input_path, total_file_size, total_file_size, true);
        }

        return DecodeResult(true, "", output_format, tgt.u8string());
    }
    catch (const std::exception& e) {
        return DecodeResult(false, "Exception: " + string(e.what()));
    }
    catch (...) {
        return DecodeResult(false, "Unknown exception occurred");
    }
}

} // namespace ncm_decoder

// 辅助函数实现
void hex2str(const char* src_, unsigned char* tgt_) {
    string hs(src_, 32);
    string bs;
    stringstream ss;
    unsigned int is;
    for (int i = 0; i < 16; i++) {
        ss.clear();
        bs = hs.substr(i * 2, 2);
        ss << hex << bs;
        ss >> is;
        tgt_[i] = is;
    }
    return;
}

unsigned int little_int(const unsigned char* src_) {
    unsigned int ret = 0;
    for (int i = 3; i >= 0; i--) {
        ret <<= 8;
        ret += src_[i];
    }
    return ret;
}
