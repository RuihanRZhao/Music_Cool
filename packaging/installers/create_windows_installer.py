"""
Windows安装程序创建脚本
使用NSIS或Inno Setup创建Windows安装程序
"""

import os
import sys
import subprocess
from pathlib import Path


def create_nsis_installer(dist_dir: str, output_file: str, app_name: str = "NCM解码器", app_version: str = "1.0.0", publisher: str = "CloudMusicDecoder"):
    """使用NSIS创建安装程序"""
    nsis_script = """
; {app_name}安装脚本
!define APP_NAME "{app_name}"
!define APP_VERSION "{app_version}"
!define APP_PUBLISHER "{publisher}"
!define APP_EXE "NCMDecoder.exe"
!define APP_DIR "{app_dir}"

Name "${{APP_NAME}}"
OutFile "{output_file}"
InstallDir "$PROGRAMFILES\\${{APP_DIR}}"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Install"
    SetOutPath "$INSTDIR"
    File /r "{dist_dir}\\*"
    
    ; 创建开始菜单快捷方式
    CreateDirectory "$SMPROGRAMS\\${{APP_DIR}}"
    CreateShortCut "$SMPROGRAMS\\${{APP_DIR}}\\${{APP_NAME}}.lnk" "$INSTDIR\\${{APP_EXE}}"
    CreateShortCut "$SMPROGRAMS\\${{APP_DIR}}\\卸载.lnk" "$INSTDIR\\uninstall.exe"
    
    ; 创建桌面快捷方式
    CreateShortCut "$DESKTOP\\${{APP_NAME}}.lnk" "$INSTDIR\\${{APP_EXE}}"
    
    ; 写入卸载信息
    WriteUninstaller "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "DisplayName" "${{APP_NAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "Publisher" "${{APP_PUBLISHER}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "DisplayVersion" "${{APP_VERSION}}"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\uninstall.exe"
    RMDir /r "$INSTDIR"
    RMDir /r "$SMPROGRAMS\\${{APP_DIR}}"
    Delete "$DESKTOP\\${{APP_NAME}}.lnk"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}"
SectionEnd
""".format(
        output_file=output_file, 
        dist_dir=dist_dir,
        app_name=app_name,
        app_version=app_version,
        publisher=publisher,
        app_dir=app_name.replace(" ", "")
    )
    
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


def create_inno_setup_installer(dist_dir: str, output_file: str, app_name: str = "NCM解码器", app_version: str = "1.0.0", publisher: str = "CloudMusicDecoder"):
    """使用Inno Setup创建安装程序"""
    # Get output directory and filename
    output_path = Path(output_file)
    output_dir = output_path.parent.resolve()
    output_base = output_path.stem
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    inno_script = """
[Setup]
AppName={app_name}
AppVersion={app_version}
AppPublisher={publisher}
DefaultDirName={{pf}}\\{app_dir}
DefaultGroupName={app_name}
OutputDir={output_dir}
OutputBaseFilename={output_base}
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: "{dist_dir}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{{group}}\\{app_name}"; Filename: "{{app}}\\NCMDecoder.exe"
Name: "{{group}}\\卸载"; Filename: "{{uninstallexe}}"
Name: "{{commondesktop}}\\{app_name}"; Filename: "{{app}}\\NCMDecoder.exe"

[Run]
Filename: "{{app}}\\NCMDecoder.exe"; Description: "启动{app_name}"; Flags: nowait postinstall skipifsilent
""".format(
        dist_dir=dist_dir.replace("\\", "\\\\"),
        output_dir=str(output_dir).replace("\\", "\\\\"),
        output_base=output_base,
        app_name=app_name,
        app_version=app_version,
        publisher=publisher,
        app_dir=app_name.replace(" ", "")
    )
    
    script_path = Path("installer.iss")
    script_path.write_text(inno_script, encoding='utf-8')
    
    # 运行Inno Setup编译器
    iscc = "iscc"
    if sys.platform == "win32":
        # First, try to find ISCC.exe in PATH
        import shutil
        iscc_in_path = shutil.which("ISCC.exe")
        if iscc_in_path:
            iscc = iscc_in_path
        else:
            # Try common installation paths
            possible_paths = [
                r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
                r"C:\Program Files\Inno Setup 6\ISCC.exe",
                r"D:\Program Files (x86)\Inno Setup 6\ISCC.exe",
                r"D:\Program Files\Inno Setup 6\ISCC.exe",
                r"E:\Program Files (x86)\Inno Setup 6\ISCC.exe",
                r"E:\Program Files\Inno Setup 6\ISCC.exe",
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
    import argparse
    
    parser = argparse.ArgumentParser(description='创建Windows安装程序')
    parser.add_argument('dist_dir', help='PyInstaller输出的目录')
    parser.add_argument('output_file', help='输出安装程序文件名')
    parser.add_argument('installer_type', nargs='?', default='nsis', choices=['nsis', 'inno'], help='安装程序类型（默认: nsis）')
    parser.add_argument('--version', default='1.0.0', help='应用版本号（默认: 1.0.0）')
    parser.add_argument('--app-name', default='NCM解码器', help='应用名称（默认: NCM解码器）')
    parser.add_argument('--publisher', default='CloudMusicDecoder', help='发布者名称（默认: CloudMusicDecoder）')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.dist_dir):
        print(f"错误: 目录不存在: {args.dist_dir}")
        sys.exit(1)
    
    if args.installer_type == "nsis":
        create_nsis_installer(args.dist_dir, args.output_file, args.app_name, args.version, args.publisher)
    elif args.installer_type == "inno":
        create_inno_setup_installer(args.dist_dir, args.output_file, args.app_name, args.version, args.publisher)
    else:
        print(f"错误: 未知的安装程序类型: {args.installer_type}")
        print("支持的类型: nsis, inno")
        sys.exit(1)


if __name__ == "__main__":
    main()
