"""
Windows安装程序创建脚本
使用NSIS或Inno Setup创建Windows安装程序
"""

import os
import sys
import subprocess
from pathlib import Path


def create_nsis_installer(dist_dir: str, output_file: str):
    """使用NSIS创建安装程序"""
    nsis_script = """
; NCM解码器安装脚本
!define APP_NAME "NCM解码器"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "CloudMusicDecoder"
!define APP_EXE "NCMDecoder.exe"
!define APP_DIR "NCMDecoder"

Name "${APP_NAME}"
OutFile "{output_file}"
InstallDir "$PROGRAMFILES\\${APP_DIR}"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Install"
    SetOutPath "$INSTDIR"
    File /r "{dist_dir}\\*"
    
    ; 创建开始菜单快捷方式
    CreateDirectory "$SMPROGRAMS\\${APP_DIR}"
    CreateShortCut "$SMPROGRAMS\\${APP_DIR}\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}"
    CreateShortCut "$SMPROGRAMS\\${APP_DIR}\\卸载.lnk" "$INSTDIR\\uninstall.exe"
    
    ; 创建桌面快捷方式
    CreateShortCut "$DESKTOP\\${APP_NAME}.lnk" "$INSTDIR\\${APP_EXE}"
    
    ; 写入卸载信息
    WriteUninstaller "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}" "UninstallString" "$INSTDIR\\uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\uninstall.exe"
    RMDir /r "$INSTDIR"
    RMDir /r "$SMPROGRAMS\\${APP_DIR}"
    Delete "$DESKTOP\\${APP_NAME}.lnk"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APP_NAME}"
SectionEnd
""".format(output_file=output_file, dist_dir=dist_dir)
    
    script_path = Path("installer.nsi")
    script_path.write_text(nsis_script, encoding='utf-8')
    
    # 运行NSIS编译器
    makensis = "makensis"
    if sys.platform == "win32":
        # 尝试常见的NSIS安装路径
        possible_paths = [
            r"C:\\Program Files (x86)\\NSIS\\makensis.exe",
            r"C:\\Program Files\\NSIS\\makensis.exe",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                makensis = path
                break
    
    try:
        subprocess.run([makensis, str(script_path)], check=True)
        print(f"安装程序已创建: {output_file}")
        script_path.unlink()  # 删除临时脚本
    except subprocess.CalledProcessError as e:
        print(f"NSIS编译失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("错误: 未找到NSIS编译器 (makensis)")
        print("请安装NSIS: https://nsis.sourceforge.io/Download")
        sys.exit(1)


def create_inno_setup_installer(dist_dir: str, output_file: str):
    """使用Inno Setup创建安装程序"""
    inno_script = """
[Setup]
AppName=NCM解码器
AppVersion=1.0.0
AppPublisher=CloudMusicDecoder
DefaultDirName={{pf}\\NCMDecoder
DefaultGroupName=NCM解码器
OutputDir=.
OutputBaseFilename={output_base}
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: "{dist_dir}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{{group}}\\NCM解码器"; Filename: "{{app}}\\NCMDecoder.exe"
Name: "{{group}}\\卸载"; Filename: "{{uninstallexe}}"
Name: "{{commondesktop}}\\NCM解码器"; Filename: "{{app}}\\NCMDecoder.exe"

[Run]
Filename: "{{app}}\\NCMDecoder.exe"; Description: "启动NCM解码器"; Flags: nowait postinstall skipifsilent
""".format(
        dist_dir=dist_dir.replace("\\", "\\\\"),
        output_base=Path(output_file).stem
    )
    
    script_path = Path("installer.iss")
    script_path.write_text(inno_script, encoding='utf-8')
    
    # 运行Inno Setup编译器
    iscc = "iscc"
    if sys.platform == "win32":
        possible_paths = [
            r"C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe",
            r"C:\\Program Files\\Inno Setup 6\\ISCC.exe",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                iscc = path
                break
    
    try:
        subprocess.run([iscc, str(script_path)], check=True)
        print(f"安装程序已创建: {output_file}")
        script_path.unlink()
    except subprocess.CalledProcessError as e:
        print(f"Inno Setup编译失败: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("错误: 未找到Inno Setup编译器 (iscc)")
        print("请安装Inno Setup: https://jrsoftware.org/isdl.php")
        sys.exit(1)


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: python create_windows_installer.py <dist_dir> <output_file> [nsis|inno]")
        print("  dist_dir: PyInstaller输出的目录")
        print("  output_file: 输出安装程序文件名")
        print("  [nsis|inno]: 安装程序类型（默认: nsis）")
        sys.exit(1)
    
    dist_dir = sys.argv[1]
    output_file = sys.argv[2]
    installer_type = sys.argv[3] if len(sys.argv) > 3 else "nsis"
    
    if not os.path.exists(dist_dir):
        print(f"错误: 目录不存在: {dist_dir}")
        sys.exit(1)
    
    if installer_type == "nsis":
        create_nsis_installer(dist_dir, output_file)
    elif installer_type == "inno":
        create_inno_setup_installer(dist_dir, output_file)
    else:
        print(f"错误: 未知的安装程序类型: {installer_type}")
        print("支持的类型: nsis, inno")
        sys.exit(1)


if __name__ == "__main__":
    main()
