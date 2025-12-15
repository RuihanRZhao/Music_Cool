use super::ImportParams;
use serde::Serialize;
use std::fs;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

/// 单个文件同步任务
#[derive(Debug, Clone, Serialize)]
pub struct FileTask {
    pub input: PathBuf,
    pub output: PathBuf,
    pub is_ncm: bool,
}

fn is_excluded(rel: &Path, exclude_dirs: &[String]) -> bool {
    let rel_str = rel.to_string_lossy();
    exclude_dirs.iter().any(|pat| !pat.is_empty() && rel_str.starts_with(pat))
}

/// 计算需要同步的任务列表（只新增/更新，不删除多余文件）
pub fn plan_sync(params: &ImportParams) -> Result<Vec<FileTask>, String> {
    let input_root = Path::new(&params.input_path);
    let output_root = Path::new(&params.output_path);

    if !input_root.is_dir() {
        return Err(format!("输入路径不是有效目录: {}", params.input_path));
    }
    if !output_root.exists() {
        fs::create_dir_all(output_root).map_err(|e| format!("创建输出目录失败: {e}"))?;
    }

    let mut tasks = Vec::new();

    for entry in WalkDir::new(input_root).into_iter().filter_map(|e| e.ok()) {
        if !entry.file_type().is_file() {
            continue;
        }
        let path = entry.path();
        let rel = match path.strip_prefix(input_root) {
            Ok(r) => r,
            Err(_) => continue,
        };

        if is_excluded(rel, &params.exclude_dirs) {
            continue;
        }

        let is_ncm = path.extension().map(|e| e.to_ascii_lowercase())
            .and_then(|e| e.to_str().map(|s| s == "ncm")).unwrap_or(false);

        // 对于 NCM 文件，输出路径是解码后的音频文件（文件名由解码器从元数据确定）
        // 对于普通文件，输出路径保持相同的相对路径结构
        let out_path = if is_ncm {
            // NCM 文件：输出目录保持相对路径结构，但文件名会在解码时确定
            // 这里先使用原路径作为占位，实际解码后的文件路径由解码器决定
            output_root.join(rel)
        } else {
            // 普通文件：直接映射到输出目录
            output_root.join(rel)
        };

        // rsync 风格比对：只新增/更新，不删除
        if !is_ncm {
            // 对于普通文件：如果目标存在且大小 & mtime 相同，则跳过
            if out_path.exists() {
                if let (Ok(src_meta), Ok(dst_meta)) = (fs::metadata(path), fs::metadata(&out_path)) {
                    let same_size = src_meta.len() == dst_meta.len();
                    let same_mtime = src_meta.modified().ok().and_then(|t1| dst_meta.modified().ok().map(|t2| t1 == t2)).unwrap_or(false);
                    if same_size && same_mtime {
                        continue; // 文件未变化，跳过
                    }
                }
            }
        } else {
            // 对于 NCM 文件：
            // 策略：总是加入任务列表，因为：
            // 1. 解码后的文件名由解码器从 NCM 元数据确定，无法在扫描阶段预知
            // 2. NCM 文件本身的变化（mtime）可能意味着需要重新解码
            // 3. 解码器内部可能会检查目标文件是否存在并决定是否覆盖
            // 
            // 未来优化：可以解析 NCM 文件元数据来预测输出文件名，
            // 然后检查目标文件是否存在且未变化，但这需要额外的解析逻辑
        }

        tasks.push(FileTask {
            input: path.to_path_buf(),
            output: out_path,
            is_ncm,
        });
    }

    Ok(tasks)
}


