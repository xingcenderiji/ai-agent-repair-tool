"""
自动安装模块
监控下载目录，识别用户自行下载的安装包，自动执行安装
"""

import hashlib
import os
import re
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple


class FileType(Enum):
    """文件类型"""

    UNKNOWN = "unknown"
    INSTALLER_EXE = "installer_exe"  # Windows安装程序
    INSTALLER_MSI = "installer_msi"  # Windows MSI
    INSTALLER_PKG = "installer_pkg"  # macOS PKG
    INSTALLER_DMG = "installer_dmg"  # macOS DMG
    INSTALLER_DEB = "installer_deb"  # Linux DEB
    INSTALLER_RPM = "installer_rpm"  # Linux RPM
    INSTALLER_APPIMAGE = "installer_appimage"  # Linux AppImage
    ARCHIVE_ZIP = "archive_zip"
    ARCHIVE_TAR = "archive_tar"
    ARCHIVE_TAR_GZ = "archive_tar_gz"
    ARCHIVE_7Z = "archive_7z"
    PYTHON_WHEEL = "python_wheel"  # Python wheel
    PYTHON_EGG = "python_egg"  # Python egg


class InstallStatus(Enum):
    """安装状态"""

    PENDING = "pending"  # 待处理
    DETECTED = "detected"  # 已检测到
    ANALYZING = "analyzing"  # 分析中
    READY = "ready"  # 准备安装
    INSTALLING = "installing"  # 安装中
    SUCCESS = "success"  # 安装成功
    FAILED = "failed"  # 安装失败
    SKIPPED = "skipped"  # 已跳过


@dataclass
class DetectedFile:
    """检测到的文件"""

    id: str
    path: str
    filename: str
    file_type: FileType
    size_bytes: int
    size_display: str
    modified_time: float
    status: InstallStatus = InstallStatus.PENDING

    # 文件信息
    checksum: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None

    # 安装信息
    target_agent: Optional[str] = None  # 目标Agent ID
    install_command: Optional[str] = None
    install_args: List[str] = field(default_factory=list)

    # 状态
    progress: float = 0.0
    error_message: Optional[str] = None
    install_log: List[str] = field(default_factory=list)

    def get_icon(self) -> str:
        """获取文件类型图标"""
        icons = {
            FileType.INSTALLER_EXE: "📦",
            FileType.INSTALLER_MSI: "📦",
            FileType.INSTALLER_PKG: "📦",
            FileType.INSTALLER_DMG: "💿",
            FileType.INSTALLER_DEB: "📦",
            FileType.INSTALLER_RPM: "📦",
            FileType.INSTALLER_APPIMAGE: "🚀",
            FileType.ARCHIVE_ZIP: "🗜️",
            FileType.ARCHIVE_TAR: "🗜️",
            FileType.ARCHIVE_TAR_GZ: "🗜️",
            FileType.ARCHIVE_7Z: "🗜️",
            FileType.PYTHON_WHEEL: "🐍",
            FileType.PYTHON_EGG: "🐍",
            FileType.UNKNOWN: "📄",
        }
        return icons.get(self.file_type, "📄")

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "path": self.path,
            "filename": self.filename,
            "icon": self.get_icon(),
            "file_type": self.file_type.value,
            "size": self.size_display,
            "status": self.status.value,
            "progress": self.progress,
            "target_agent": self.target_agent,
            "version": self.version,
            "description": self.description,
            "error": self.error_message,
            "detected_at": datetime.fromtimestamp(
                self.modified_time
            ).isoformat(),
        }


class FileTypeDetector:
    """文件类型检测器"""

    EXTENSION_MAP = {
        # Windows
        ".exe": FileType.INSTALLER_EXE,
        ".msi": FileType.INSTALLER_MSI,
        ".msix": FileType.INSTALLER_MSI,
        ".appx": FileType.INSTALLER_MSI,
        # macOS
        ".pkg": FileType.INSTALLER_PKG,
        ".dmg": FileType.INSTALLER_DMG,
        # Linux
        ".deb": FileType.INSTALLER_DEB,
        ".rpm": FileType.INSTALLER_RPM,
        ".AppImage": FileType.INSTALLER_APPIMAGE,
        ".appimage": FileType.INSTALLER_APPIMAGE,
        # Archives
        ".zip": FileType.ARCHIVE_ZIP,
        ".tar": FileType.ARCHIVE_TAR,
        ".gz": FileType.ARCHIVE_TAR_GZ,
        ".tgz": FileType.ARCHIVE_TAR_GZ,
        ".bz2": FileType.ARCHIVE_TAR,
        ".7z": FileType.ARCHIVE_7Z,
        ".rar": FileType.ARCHIVE_ZIP,
        # Python
        ".whl": FileType.PYTHON_WHEEL,
        ".egg": FileType.PYTHON_EGG,
    }

    @classmethod
    def detect(cls, file_path: Path) -> FileType:
        """检测文件类型"""
        ext = file_path.suffix.lower()
        return cls.EXTENSION_MAP.get(ext, FileType.UNKNOWN)

    @classmethod
    def is_installer(cls, file_type: FileType) -> bool:
        """是否是安装程序"""
        return file_type in [
            FileType.INSTALLER_EXE,
            FileType.INSTALLER_MSI,
            FileType.INSTALLER_PKG,
            FileType.INSTALLER_DMG,
            FileType.INSTALLER_DEB,
            FileType.INSTALLER_RPM,
            FileType.INSTALLER_APPIMAGE,
        ]

    @classmethod
    def is_archive(cls, file_type: FileType) -> bool:
        """是否是压缩包"""
        return file_type in [
            FileType.ARCHIVE_ZIP,
            FileType.ARCHIVE_TAR,
            FileType.ARCHIVE_TAR_GZ,
            FileType.ARCHIVE_7Z,
        ]


class AutoInstaller:
    """自动安装器"""

    # 常见下载目录
    DOWNLOAD_PATHS = [
        "~/Downloads",
        "~/下载",
        "~/Desktop",
        "~/桌面",
        "~/.ai_agent_repair/downloads",
    ]

    # 文件名模式匹配（识别目标Agent）
    AGENT_PATTERNS = {
        "cursor": [r"cursor", r"cursor-editor"],
        "windsurf": [r"windsurf", r"codeium"],
        "cline": [r"cline", r"claude-dev"],
        "continue": [r"continue"],
        "copilot": [r"copilot", r"github-copilot"],
        "claude": [r"claude", r"claude-code"],
        "vscode": [r"vscode", r"visual-studio-code", r"code"],
    }

    def __init__(self):
        self.detected_files: Dict[str, DetectedFile] = {}
        self._lock = threading.Lock()
        self._callbacks: List[Callable] = []
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # 确保下载目录存在
        self._ensure_download_dirs()

    def _ensure_download_dirs(self):
        """确保下载目录存在"""
        for path_template in self.DOWNLOAD_PATHS:
            path = Path(os.path.expanduser(path_template))
            path.mkdir(parents=True, exist_ok=True)

    def register_callback(self, callback: Callable):
        """注册状态更新回调"""
        self._callbacks.append(callback)

    def _notify(self, file_info: DetectedFile):
        """通知状态更新"""
        for cb in self._callbacks:
            try:
                cb(file_info)
            except:
                pass

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def scan_downloads(self) -> List[DetectedFile]:
        """扫描下载目录，检测新文件"""
        detected = []

        for path_template in self.DOWNLOAD_PATHS:
            path = Path(os.path.expanduser(path_template))
            if not path.exists():
                continue

            try:
                for file_path in path.iterdir():
                    if not file_path.is_file():
                        continue

                    # 检查是否是安装包类型
                    file_type = FileTypeDetector.detect(file_path)
                    if file_type == FileType.UNKNOWN:
                        continue

                    # 计算文件ID（基于路径和修改时间）
                    stat = file_path.stat()
                    file_id = hashlib.md5(
                        f"{file_path}:{stat.st_mtime}".encode()
                    ).hexdigest()[:12]

                    # 检查是否已记录
                    with self._lock:
                        if file_id in self.detected_files:
                            continue

                    # 创建检测记录
                    file_info = DetectedFile(
                        id=file_id,
                        path=str(file_path),
                        filename=file_path.name,
                        file_type=file_type,
                        size_bytes=stat.st_size,
                        size_display=self._format_size(stat.st_size),
                        modified_time=stat.st_mtime,
                        status=InstallStatus.DETECTED,
                    )

                    # 识别目标Agent
                    self._identify_target(file_info)

                    # 设置安装命令
                    self._prepare_install_command(file_info)

                    with self._lock:
                        self.detected_files[file_id] = file_info

                    detected.append(file_info)
                    self._notify(file_info)

            except PermissionError:
                continue
            except Exception:
                continue

        return detected

    def _identify_target(self, file_info: DetectedFile):
        """识别文件对应的目标Agent"""
        filename_lower = file_info.filename.lower()

        for agent_id, patterns in self.AGENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower, re.IGNORECASE):
                    file_info.target_agent = agent_id

                    # 设置描述
                    file_info.description = (
                        f"适用于 {agent_id.title()} 的安装包"
                    )
                    break
            if file_info.target_agent:
                break

        if not file_info.target_agent:
            # 通用安装包
            if FileTypeDetector.is_installer(file_info.file_type):
                file_info.description = "通用安装包"
            elif FileTypeDetector.is_archive(file_info.file_type):
                file_info.description = "压缩包，需要解压后使用"

    def _prepare_install_command(self, file_info: DetectedFile):
        """准备安装命令"""
        file_path = file_info.path

        if file_info.file_type == FileType.INSTALLER_EXE:
            if sys.platform == "win32":
                file_info.install_command = file_path
                file_info.install_args = ["/S", "/quiet"]  # 静默安装
            else:
                file_info.install_command = "wine"
                file_info.install_args = [file_path]

        elif file_info.file_type == FileType.INSTALLER_MSI:
            if sys.platform == "win32":
                file_info.install_command = "msiexec"
                file_info.install_args = ["/i", file_path, "/quiet"]
            else:
                file_info.install_command = f"alien -i {file_path}"
                file_info.install_args = []

        elif file_info.file_type == FileType.INSTALLER_DMG:
            file_info.install_command = f"hdiutil attach {file_path}"
            file_info.install_args = ["-nobrowse"]
            file_info.description += "\n\nmacOS DMG需要手动挂载后安装"

        elif file_info.file_type == FileType.INSTALLER_PKG:
            file_info.install_command = "sudo installer"
            file_info.install_args = ["-pkg", file_path, "-target", "/"]

        elif file_info.file_type == FileType.INSTALLER_DEB:
            file_info.install_command = "sudo dpkg"
            file_info.install_args = ["-i", file_path]

        elif file_info.file_type == FileType.INSTALLER_RPM:
            file_info.install_command = "sudo rpm"
            file_info.install_args = ["-i", file_path]

        elif file_info.file_type == FileType.INSTALLER_APPIMAGE:
            # AppImage需要添加执行权限
            file_info.install_command = f"chmod +x {file_path} && {file_path}"
            file_info.install_args = []
            file_info.description += "\n\nAppImage将直接运行，无需安装"

        elif file_info.file_type == FileType.ARCHIVE_ZIP:
            # 解压到当前目录
            extract_dir = Path(file_path).parent / Path(file_path).stem
            file_info.install_command = "unzip"
            file_info.install_args = [file_path, "-d", str(extract_dir)]

        elif file_info.file_type == FileType.ARCHIVE_TAR_GZ:
            extract_dir = Path(file_path).parent / Path(
                file_path
            ).stem.replace(".tar.gz", "")
            file_info.install_command = "tar"
            file_info.install_args = [
                "-xzf",
                file_path,
                "-C",
                str(extract_dir),
            ]

        elif file_info.file_type == FileType.PYTHON_WHEEL:
            file_info.install_command = "pip"
            file_info.install_args = ["install", file_path]

    def install_file(
        self, file_id: str, auto: bool = True
    ) -> Tuple[bool, str]:
        """执行安装"""
        with self._lock:
            if file_id not in self.detected_files:
                return False, "文件不存在"
            file_info = self.detected_files[file_id]

        if file_info.status == InstallStatus.INSTALLING:
            return False, "正在安装中"

        if file_info.status == InstallStatus.SUCCESS:
            return False, "已安装完成"

        # 更新状态
        file_info.status = InstallStatus.INSTALLING
        file_info.progress = 0
        file_info.error_message = None
        file_info.install_log = []
        self._notify(file_info)

        try:
            # 根据文件类型执行安装
            if file_info.file_type == FileType.INSTALLER_APPIMAGE:
                # AppImage 直接运行
                self._install_appimage(file_info)
            elif file_info.file_type in [
                FileType.ARCHIVE_ZIP,
                FileType.ARCHIVE_TAR_GZ,
            ]:
                # 解压
                self._install_archive(file_info)
            elif (
                file_info.file_type == FileType.INSTALLER_EXE
                and sys.platform != "win32"
            ):
                # wine 安装
                self._install_with_wine(file_info)
            else:
                # 其他类型，记录日志但不实际安装
                file_info.install_log.append(
                    f"检测到安装包: {file_info.filename}"
                )
                file_info.install_log.append(
                    f"类型: {file_info.file_type.value}"
                )
                file_info.install_log.append(f"建议手动安装或添加到系统PATH")
                file_info.status = InstallStatus.READY
                self._notify(file_info)
                return True, "已准备就绪，请手动完成最后步骤"

            file_info.status = InstallStatus.SUCCESS
            file_info.progress = 100
            file_info.install_log.append(
                f"{datetime.now().isoformat()} 安装完成"
            )
            self._notify(file_info)
            return True, "安装成功"

        except Exception as e:
            file_info.status = InstallStatus.FAILED
            file_info.error_message = str(e)
            file_info.install_log.append(
                f"{datetime.now().isoformat()} 安装失败: {e}"
            )
            self._notify(file_info)
            return False, str(e)

    def _install_appimage(self, file_info: DetectedFile):
        """安装AppImage"""
        file_info.install_log.append(
            f"{datetime.now().isoformat()} 添加执行权限..."
        )
        file_info.progress = 20
        self._notify(file_info)

        # 添加执行权限
        result = subprocess.run(
            ["chmod", "+x", file_info.path], capture_output=True, text=True
        )
        if result.returncode != 0:
            raise Exception(f"添加执行权限失败: {result.stderr}")

        file_info.install_log.append(
            f"{datetime.now().isoformat()} AppImage已准备就绪"
        )
        file_info.install_log.append(f"路径: {file_info.path}")
        file_info.install_log.append(f"可以在终端运行: ./{file_info.path}")
        file_info.progress = 100

    def _install_archive(self, file_info: DetectedFile):
        """解压压缩包"""
        file_info.install_log.append(
            f"{datetime.now().isoformat()} 开始解压..."
        )
        file_info.progress = 30
        self._notify(file_info)

        extract_dir = Path(file_info.path).parent / Path(file_info.path).stem
        extract_dir.mkdir(exist_ok=True)

        if file_info.file_type == FileType.ARCHIVE_ZIP:
            result = subprocess.run(
                ["unzip", "-o", file_info.path, "-d", str(extract_dir)],
                capture_output=True,
                text=True,
            )
        else:
            result = subprocess.run(
                ["tar", "-xzf", file_info.path, "-C", str(extract_dir)],
                capture_output=True,
                text=True,
            )

        if result.returncode != 0:
            raise Exception(f"解压失败: {result.stderr}")

        file_info.install_log.append(f"{datetime.now().isoformat()} 解压完成")
        file_info.install_log.append(f"解压目录: {extract_dir}")
        file_info.progress = 100

    def _install_with_wine(self, file_info: DetectedFile):
        """用Wine安装"""
        file_info.install_log.append(
            f"{datetime.now().isoformat()} 使用Wine安装..."
        )
        file_info.progress = 50
        self._notify(file_info)

        result = subprocess.run(
            ["wine", file_info.path], capture_output=True, text=True
        )

        if result.returncode != 0:
            raise Exception(f"Wine安装失败: {result.stderr}")

        file_info.progress = 100

    def get_detected_files(self) -> List[Dict]:
        """获取所有检测到的文件"""
        with self._lock:
            return [f.to_dict() for f in self.detected_files.values()]

    def get_file_status(self, file_id: str) -> Optional[Dict]:
        """获取单个文件状态"""
        with self._lock:
            if file_id in self.detected_files:
                return self.detected_files[file_id].to_dict()
        return None

    def start_monitoring(self, interval: int = 5):
        """开始监控下载目录"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, args=(interval,), daemon=True
        )
        self._monitor_thread.start()

    def _monitor_loop(self, interval: int):
        """监控循环"""
        while not self._stop_event.is_set():
            try:
                self.scan_downloads()
            except:
                pass
            self._stop_event.wait(interval)

    def stop_monitoring(self):
        """停止监控"""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)

    def clear_completed(self):
        """清除已完成的文件记录"""
        with self._lock:
            completed = [
                fid
                for fid, f in self.detected_files.items()
                if f.status in [InstallStatus.SUCCESS, InstallStatus.SKIPPED]
            ]
            for fid in completed:
                del self.detected_files[fid]


# 全局实例
auto_installer = AutoInstaller()
