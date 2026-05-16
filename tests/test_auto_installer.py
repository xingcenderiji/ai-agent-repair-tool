"""
自动安装器测试套件
测试文件类型检测、安装包识别、安装命令生成等功能
"""

import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.auto_installer import (
    AutoInstaller,
    DetectedFile,
    FileType,
    FileTypeDetector,
    InstallStatus,
    auto_installer,
)


class TestFileType(unittest.TestCase):
    """测试文件类型枚举"""

    def test_file_type_values(self):
        """测试文件类型值"""
        self.assertEqual(FileType.UNKNOWN.value, "unknown")
        self.assertEqual(FileType.INSTALLER_EXE.value, "installer_exe")
        self.assertEqual(FileType.INSTALLER_MSI.value, "installer_msi")
        self.assertEqual(FileType.INSTALLER_PKG.value, "installer_pkg")
        self.assertEqual(FileType.INSTALLER_DMG.value, "installer_dmg")
        self.assertEqual(FileType.INSTALLER_DEB.value, "installer_deb")
        self.assertEqual(FileType.INSTALLER_RPM.value, "installer_rpm")
        self.assertEqual(
            FileType.INSTALLER_APPIMAGE.value, "installer_appimage"
        )
        self.assertEqual(FileType.ARCHIVE_ZIP.value, "archive_zip")
        self.assertEqual(FileType.ARCHIVE_TAR.value, "archive_tar")
        self.assertEqual(FileType.ARCHIVE_TAR_GZ.value, "archive_tar_gz")
        self.assertEqual(FileType.ARCHIVE_7Z.value, "archive_7z")
        self.assertEqual(FileType.PYTHON_WHEEL.value, "python_wheel")
        self.assertEqual(FileType.PYTHON_EGG.value, "python_egg")


class TestDetectedFile(unittest.TestCase):
    """测试检测到的文件类"""

    def test_detected_file_defaults(self):
        """测试检测文件默认值"""
        file_info = DetectedFile(
            id="file-1",
            path="/downloads/test.exe",
            filename="test.exe",
            file_type=FileType.INSTALLER_EXE,
            size_bytes=1024,
            size_display="1.0 KB",
            modified_time=time.time(),
        )
        self.assertEqual(file_info.id, "file-1")
        self.assertEqual(file_info.status, InstallStatus.PENDING)
        self.assertEqual(file_info.progress, 0.0)
        self.assertIsNone(file_info.target_agent)

    def test_get_icon(self):
        """测试获取图标"""
        file_info = DetectedFile(
            id="file-1",
            path="/test.exe",
            filename="test.exe",
            file_type=FileType.INSTALLER_EXE,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )
        self.assertEqual(file_info.get_icon(), "📦")

        file_info.file_type = FileType.INSTALLER_DMG
        self.assertEqual(file_info.get_icon(), "💿")

        file_info.file_type = FileType.ARCHIVE_ZIP
        self.assertEqual(file_info.get_icon(), "🗜️")

        file_info.file_type = FileType.PYTHON_WHEEL
        self.assertEqual(file_info.get_icon(), "🐍")

        file_info.file_type = FileType.UNKNOWN
        self.assertEqual(file_info.get_icon(), "📄")

    def test_to_dict(self):
        """测试转换为字典"""
        file_info = DetectedFile(
            id="file-1",
            path="/downloads/test.exe",
            filename="test.exe",
            file_type=FileType.INSTALLER_EXE,
            size_bytes=1024 * 1024,
            size_display="1.0 MB",
            modified_time=time.time(),
            status=InstallStatus.READY,
            target_agent="cursor",
            version="1.0.0",
            description="Test installer",
        )

        data = file_info.to_dict()
        self.assertEqual(data["id"], "file-1")
        self.assertEqual(data["filename"], "test.exe")
        self.assertEqual(data["icon"], "📦")
        self.assertEqual(data["file_type"], "installer_exe")
        self.assertEqual(data["size"], "1.0 MB")
        self.assertEqual(data["status"], "ready")
        self.assertEqual(data["target_agent"], "cursor")
        self.assertEqual(data["version"], "1.0.0")


class TestFileTypeDetector(unittest.TestCase):
    """测试文件类型检测器"""

    def test_detect_windows_installers(self):
        """测试Windows安装程序检测"""
        self.assertEqual(
            FileTypeDetector.detect(Path("app.exe")), FileType.INSTALLER_EXE
        )
        self.assertEqual(
            FileTypeDetector.detect(Path("app.msi")), FileType.INSTALLER_MSI
        )
        self.assertEqual(
            FileTypeDetector.detect(Path("app.msix")), FileType.INSTALLER_MSI
        )
        self.assertEqual(
            FileTypeDetector.detect(Path("app.appx")), FileType.INSTALLER_MSI
        )

    def test_detect_macos_installers(self):
        """测试macOS安装程序检测"""
        self.assertEqual(
            FileTypeDetector.detect(Path("app.pkg")), FileType.INSTALLER_PKG
        )
        self.assertEqual(
            FileTypeDetector.detect(Path("app.dmg")), FileType.INSTALLER_DMG
        )

    def test_detect_linux_installers(self):
        """测试Linux安装程序检测"""
        self.assertEqual(
            FileTypeDetector.detect(Path("app.deb")), FileType.INSTALLER_DEB
        )
        self.assertEqual(
            FileTypeDetector.detect(Path("app.rpm")), FileType.INSTALLER_RPM
        )
        self.assertEqual(
            FileTypeDetector.detect(Path("app.AppImage")),
            FileType.INSTALLER_APPIMAGE,
        )
        self.assertEqual(
            FileTypeDetector.detect(Path("app.appimage")),
            FileType.INSTALLER_APPIMAGE,
        )

    def test_detect_archives(self):
        """测试压缩包检测"""
        self.assertEqual(
            FileTypeDetector.detect(Path("app.zip")), FileType.ARCHIVE_ZIP
        )
        self.assertEqual(
            FileTypeDetector.detect(Path("app.tar")), FileType.ARCHIVE_TAR
        )
        self.assertEqual(
            FileTypeDetector.detect(Path("app.gz")), FileType.ARCHIVE_TAR_GZ
        )
        self.assertEqual(
            FileTypeDetector.detect(Path("app.tgz")), FileType.ARCHIVE_TAR_GZ
        )
        self.assertEqual(
            FileTypeDetector.detect(Path("app.bz2")), FileType.ARCHIVE_TAR
        )
        self.assertEqual(
            FileTypeDetector.detect(Path("app.7z")), FileType.ARCHIVE_7Z
        )
        self.assertEqual(
            FileTypeDetector.detect(Path("app.rar")), FileType.ARCHIVE_ZIP
        )

    def test_detect_python_packages(self):
        """测试Python包检测"""
        self.assertEqual(
            FileTypeDetector.detect(Path("app.whl")), FileType.PYTHON_WHEEL
        )
        self.assertEqual(
            FileTypeDetector.detect(Path("app.egg")), FileType.PYTHON_EGG
        )

    def test_detect_unknown(self):
        """测试未知文件类型"""
        self.assertEqual(
            FileTypeDetector.detect(Path("app.txt")), FileType.UNKNOWN
        )
        self.assertEqual(
            FileTypeDetector.detect(Path("app.pdf")), FileType.UNKNOWN
        )

    def test_detect_case_insensitive(self):
        """测试大小写不敏感"""
        self.assertEqual(
            FileTypeDetector.detect(Path("app.EXE")), FileType.INSTALLER_EXE
        )
        self.assertEqual(
            FileTypeDetector.detect(Path("app.ZIP")), FileType.ARCHIVE_ZIP
        )

    def test_is_installer(self):
        """测试安装程序判断"""
        self.assertTrue(FileTypeDetector.is_installer(FileType.INSTALLER_EXE))
        self.assertTrue(FileTypeDetector.is_installer(FileType.INSTALLER_MSI))
        self.assertTrue(FileTypeDetector.is_installer(FileType.INSTALLER_PKG))
        self.assertTrue(FileTypeDetector.is_installer(FileType.INSTALLER_DMG))
        self.assertTrue(FileTypeDetector.is_installer(FileType.INSTALLER_DEB))
        self.assertTrue(FileTypeDetector.is_installer(FileType.INSTALLER_RPM))
        self.assertTrue(
            FileTypeDetector.is_installer(FileType.INSTALLER_APPIMAGE)
        )

        self.assertFalse(FileTypeDetector.is_installer(FileType.ARCHIVE_ZIP))
        self.assertFalse(FileTypeDetector.is_installer(FileType.PYTHON_WHEEL))
        self.assertFalse(FileTypeDetector.is_installer(FileType.UNKNOWN))

    def test_is_archive(self):
        """测试压缩包判断"""
        self.assertTrue(FileTypeDetector.is_archive(FileType.ARCHIVE_ZIP))
        self.assertTrue(FileTypeDetector.is_archive(FileType.ARCHIVE_TAR))
        self.assertTrue(FileTypeDetector.is_archive(FileType.ARCHIVE_TAR_GZ))
        self.assertTrue(FileTypeDetector.is_archive(FileType.ARCHIVE_7Z))

        self.assertFalse(FileTypeDetector.is_archive(FileType.INSTALLER_EXE))
        self.assertFalse(FileTypeDetector.is_archive(FileType.PYTHON_WHEEL))
        self.assertFalse(FileTypeDetector.is_archive(FileType.UNKNOWN))


class TestAutoInstaller(unittest.TestCase):
    """测试自动安装器核心功能"""

    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.installer = AutoInstaller.__new__(AutoInstaller)
        self.installer.detected_files = {}
        self.installer._lock = threading.Lock()
        self.installer._callbacks = []
        self.installer._monitor_thread = None
        self.installer._stop_event = threading.Event()

    def tearDown(self):
        """测试后清理"""
        import shutil

        self.installer.stop_monitoring()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_format_size(self):
        """测试文件大小格式化"""
        self.assertEqual(self.installer._format_size(512), "512 B")
        self.assertEqual(self.installer._format_size(1024), "1.0 KB")
        self.assertEqual(self.installer._format_size(1024 * 1024), "1.0 MB")
        self.assertEqual(
            self.installer._format_size(1024 * 1024 * 1024), "1.00 GB"
        )

    def test_scan_downloads_empty(self):
        """测试扫描空目录"""
        # 使用临时目录作为下载目录
        with patch.object(self.installer, "DOWNLOAD_PATHS", [self.temp_dir]):
            detected = self.installer.scan_downloads()
            self.assertEqual(len(detected), 0)

    def test_scan_downloads_with_files(self):
        """测试扫描包含文件的目录"""
        # 创建测试文件
        test_file = Path(self.temp_dir) / "cursor-setup.exe"
        test_file.write_text("fake exe content")

        with patch.object(self.installer, "DOWNLOAD_PATHS", [self.temp_dir]):
            detected = self.installer.scan_downloads()
            self.assertEqual(len(detected), 1)
            self.assertEqual(detected[0].filename, "cursor-setup.exe")
            self.assertEqual(detected[0].file_type, FileType.INSTALLER_EXE)

    def test_scan_downloads_ignores_unknown(self):
        """测试扫描忽略未知文件"""
        # 创建未知类型文件
        test_file = Path(self.temp_dir) / "readme.txt"
        test_file.write_text("readme content")

        with patch.object(self.installer, "DOWNLOAD_PATHS", [self.temp_dir]):
            detected = self.installer.scan_downloads()
            self.assertEqual(len(detected), 0)

    def test_scan_downloads_skips_directories(self):
        """测试扫描跳过目录"""
        # 创建子目录
        sub_dir = Path(self.temp_dir) / "subdir"
        sub_dir.mkdir()

        with patch.object(self.installer, "DOWNLOAD_PATHS", [self.temp_dir]):
            detected = self.installer.scan_downloads()
            self.assertEqual(len(detected), 0)

    def test_identify_target_cursor(self):
        """测试识别Cursor目标"""
        file_info = DetectedFile(
            id="file-1",
            path="/test.exe",
            filename="cursor-setup.exe",
            file_type=FileType.INSTALLER_EXE,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )

        self.installer._identify_target(file_info)
        self.assertEqual(file_info.target_agent, "cursor")
        self.assertIn("Cursor", file_info.description)

    def test_identify_target_claude(self):
        """测试识别Claude目标"""
        file_info = DetectedFile(
            id="file-1",
            path="/test.pkg",
            filename="claude-code.pkg",
            file_type=FileType.INSTALLER_PKG,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )

        self.installer._identify_target(file_info)
        self.assertEqual(file_info.target_agent, "claude")

    def test_identify_target_vscode(self):
        """测试识别VS Code目标"""
        file_info = DetectedFile(
            id="file-1",
            path="/test.deb",
            filename="vscode-amd64.deb",
            file_type=FileType.INSTALLER_DEB,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )

        self.installer._identify_target(file_info)
        self.assertEqual(file_info.target_agent, "vscode")

    def test_identify_target_generic_installer(self):
        """测试识别通用安装包"""
        file_info = DetectedFile(
            id="file-1",
            path="/test.exe",
            filename="unknown-tool.exe",
            file_type=FileType.INSTALLER_EXE,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )

        self.installer._identify_target(file_info)
        self.assertIsNone(file_info.target_agent)
        self.assertEqual(file_info.description, "通用安装包")

    def test_identify_target_archive(self):
        """测试识别压缩包"""
        file_info = DetectedFile(
            id="file-1",
            path="/test.zip",
            filename="tools.zip",
            file_type=FileType.ARCHIVE_ZIP,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )

        self.installer._identify_target(file_info)
        self.assertIsNone(file_info.target_agent)
        self.assertIn("压缩包", file_info.description)

    def test_prepare_install_command_exe_windows(self):
        """测试准备Windows EXE安装命令"""
        with patch("core.auto_installer.sys.platform", "win32"):
            file_info = DetectedFile(
                id="file-1",
                path="/test.exe",
                filename="test.exe",
                file_type=FileType.INSTALLER_EXE,
                size_bytes=0,
                size_display="0 B",
                modified_time=0,
            )

            self.installer._prepare_install_command(file_info)
            self.assertEqual(file_info.install_command, "/test.exe")
            self.assertEqual(file_info.install_args, ["/S", "/quiet"])

    def test_prepare_install_command_exe_linux(self):
        """测试准备Linux下EXE安装命令（Wine）"""
        with patch("core.auto_installer.sys.platform", "linux"):
            file_info = DetectedFile(
                id="file-1",
                path="/test.exe",
                filename="test.exe",
                file_type=FileType.INSTALLER_EXE,
                size_bytes=0,
                size_display="0 B",
                modified_time=0,
            )

            self.installer._prepare_install_command(file_info)
            self.assertEqual(file_info.install_command, "wine")
            self.assertEqual(file_info.install_args, ["/test.exe"])

    def test_prepare_install_command_deb(self):
        """测试准备DEB安装命令"""
        file_info = DetectedFile(
            id="file-1",
            path="/test.deb",
            filename="test.deb",
            file_type=FileType.INSTALLER_DEB,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )

        self.installer._prepare_install_command(file_info)
        self.assertEqual(file_info.install_command, "sudo dpkg")
        self.assertEqual(file_info.install_args, ["-i", "/test.deb"])

    def test_prepare_install_command_rpm(self):
        """测试准备RPM安装命令"""
        file_info = DetectedFile(
            id="file-1",
            path="/test.rpm",
            filename="test.rpm",
            file_type=FileType.INSTALLER_RPM,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )

        self.installer._prepare_install_command(file_info)
        self.assertEqual(file_info.install_command, "sudo rpm")
        self.assertEqual(file_info.install_args, ["-i", "/test.rpm"])

    def test_prepare_install_command_appimage(self):
        """测试准备AppImage安装命令"""
        file_info = DetectedFile(
            id="file-1",
            path="/test.AppImage",
            filename="test.AppImage",
            file_type=FileType.INSTALLER_APPIMAGE,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
            description="Test AppImage",
        )

        self.installer._prepare_install_command(file_info)
        self.assertIn("chmod", file_info.install_command)
        self.assertIn("AppImage将直接运行", file_info.description)

    def test_prepare_install_command_zip(self):
        """测试准备ZIP解压命令"""
        file_info = DetectedFile(
            id="file-1",
            path="/test.zip",
            filename="test.zip",
            file_type=FileType.ARCHIVE_ZIP,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )

        self.installer._prepare_install_command(file_info)
        self.assertEqual(file_info.install_command, "unzip")
        self.assertIn("-d", file_info.install_args)

    def test_prepare_install_command_tar_gz(self):
        """测试准备TAR.GZ解压命令"""
        file_info = DetectedFile(
            id="file-1",
            path="/test.tar.gz",
            filename="test.tar.gz",
            file_type=FileType.ARCHIVE_TAR_GZ,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )

        self.installer._prepare_install_command(file_info)
        self.assertEqual(file_info.install_command, "tar")
        # Path("/test.tar.gz").stem = "test.tar", replace(".tar.gz", "") = "test.tar"
        expected_dir = str(Path("/test.tar"))
        self.assertEqual(
            file_info.install_args,
            ["-xzf", "/test.tar.gz", "-C", expected_dir],
        )

    def test_prepare_install_command_wheel(self):
        """测试准备Python Wheel安装命令"""
        file_info = DetectedFile(
            id="file-1",
            path="/test.whl",
            filename="test.whl",
            file_type=FileType.PYTHON_WHEEL,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )

        self.installer._prepare_install_command(file_info)
        self.assertEqual(file_info.install_command, "pip")
        self.assertEqual(file_info.install_args, ["install", "/test.whl"])

    def test_get_detected_files(self):
        """测试获取检测到的文件列表"""
        file_info = DetectedFile(
            id="file-1",
            path="/test.exe",
            filename="test.exe",
            file_type=FileType.INSTALLER_EXE,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )
        self.installer.detected_files["file-1"] = file_info

        files = self.installer.get_detected_files()
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["id"], "file-1")

    def test_get_file_status(self):
        """测试获取单个文件状态"""
        file_info = DetectedFile(
            id="file-1",
            path="/test.exe",
            filename="test.exe",
            file_type=FileType.INSTALLER_EXE,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )
        self.installer.detected_files["file-1"] = file_info

        status = self.installer.get_file_status("file-1")
        self.assertIsNotNone(status)
        self.assertEqual(status["id"], "file-1")

        status = self.installer.get_file_status("nonexistent")
        self.assertIsNone(status)

    def test_clear_completed(self):
        """测试清除已完成文件"""
        # 添加不同状态的文件
        file1 = DetectedFile(
            id="file-1",
            path="/test1.exe",
            filename="test1.exe",
            file_type=FileType.INSTALLER_EXE,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
            status=InstallStatus.SUCCESS,
        )
        file2 = DetectedFile(
            id="file-2",
            path="/test2.exe",
            filename="test2.exe",
            file_type=FileType.INSTALLER_EXE,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
            status=InstallStatus.SKIPPED,
        )
        file3 = DetectedFile(
            id="file-3",
            path="/test3.exe",
            filename="test3.exe",
            file_type=FileType.INSTALLER_EXE,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
            status=InstallStatus.PENDING,
        )

        self.installer.detected_files["file-1"] = file1
        self.installer.detected_files["file-2"] = file2
        self.installer.detected_files["file-3"] = file3

        self.installer.clear_completed()

        self.assertNotIn("file-1", self.installer.detected_files)
        self.assertNotIn("file-2", self.installer.detected_files)
        self.assertIn("file-3", self.installer.detected_files)


class TestAutoInstallerInstall(unittest.TestCase):
    """测试自动安装器安装功能"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.installer = AutoInstaller.__new__(AutoInstaller)
        self.installer.detected_files = {}
        self.installer._lock = threading.Lock()
        self.installer._callbacks = []
        self.installer._monitor_thread = None
        self.installer._stop_event = threading.Event()

    def tearDown(self):
        import shutil

        self.installer.stop_monitoring()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_install_file_not_found(self):
        """测试安装不存在的文件"""
        success, msg = self.installer.install_file("nonexistent")
        self.assertFalse(success)
        self.assertEqual(msg, "文件不存在")

    def test_install_file_already_installing(self):
        """测试重复安装"""
        file_info = DetectedFile(
            id="file-1",
            path="/test.AppImage",
            filename="test.AppImage",
            file_type=FileType.INSTALLER_APPIMAGE,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
            status=InstallStatus.INSTALLING,
        )
        self.installer.detected_files["file-1"] = file_info

        success, msg = self.installer.install_file("file-1")
        self.assertFalse(success)
        self.assertEqual(msg, "正在安装中")

    def test_install_file_already_success(self):
        """测试安装已成功的文件"""
        file_info = DetectedFile(
            id="file-1",
            path="/test.AppImage",
            filename="test.AppImage",
            file_type=FileType.INSTALLER_APPIMAGE,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
            status=InstallStatus.SUCCESS,
        )
        self.installer.detected_files["file-1"] = file_info

        success, msg = self.installer.install_file("file-1")
        self.assertFalse(success)
        self.assertEqual(msg, "已安装完成")

    @patch("core.auto_installer.subprocess.run")
    def test_install_appimage(self, mock_run):
        """测试安装AppImage"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        test_file = Path(self.temp_dir) / "test.AppImage"
        test_file.write_text("fake appimage")

        file_info = DetectedFile(
            id="file-1",
            path=str(test_file),
            filename="test.AppImage",
            file_type=FileType.INSTALLER_APPIMAGE,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )
        self.installer.detected_files["file-1"] = file_info

        success, msg = self.installer.install_file("file-1")
        self.assertTrue(success)
        self.assertEqual(file_info.status, InstallStatus.SUCCESS)
        self.assertEqual(file_info.progress, 100)

    @patch("core.auto_installer.subprocess.run")
    def test_install_archive_zip(self, mock_run):
        """测试解压ZIP"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        test_file = Path(self.temp_dir) / "test.zip"
        test_file.write_text("fake zip")

        file_info = DetectedFile(
            id="file-1",
            path=str(test_file),
            filename="test.zip",
            file_type=FileType.ARCHIVE_ZIP,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )
        self.installer.detected_files["file-1"] = file_info

        success, msg = self.installer.install_file("file-1")
        self.assertTrue(success)
        self.assertEqual(file_info.status, InstallStatus.SUCCESS)

    @patch("core.auto_installer.subprocess.run")
    def test_install_appimage_failure(self, mock_run):
        """测试AppImage安装失败"""
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="Permission denied"
        )

        test_file = Path(self.temp_dir) / "test.AppImage"
        test_file.write_text("fake appimage")

        file_info = DetectedFile(
            id="file-1",
            path=str(test_file),
            filename="test.AppImage",
            file_type=FileType.INSTALLER_APPIMAGE,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )
        self.installer.detected_files["file-1"] = file_info

        success, msg = self.installer.install_file("file-1")
        self.assertFalse(success)
        self.assertEqual(file_info.status, InstallStatus.FAILED)
        self.assertIsNotNone(file_info.error_message)

    @patch("core.auto_installer.subprocess.run")
    def test_install_unsupported_type(self, mock_run):
        """测试安装不支持的类型（在非Windows平台用Wine安装EXE）"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        test_file = Path(self.temp_dir) / "test.exe"
        test_file.write_text("fake exe")

        file_info = DetectedFile(
            id="file-1",
            path=str(test_file),
            filename="test.exe",
            file_type=FileType.INSTALLER_EXE,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )
        self.installer.detected_files["file-1"] = file_info

        # 在非Windows平台，EXE应该使用Wine安装
        with patch("core.auto_installer.sys.platform", "linux"):
            success, msg = self.installer.install_file("file-1")
            self.assertTrue(success)
            self.assertEqual(file_info.status, InstallStatus.SUCCESS)


class TestAutoInstallerMonitoring(unittest.TestCase):
    """测试自动安装器监控功能"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.installer = AutoInstaller.__new__(AutoInstaller)
        self.installer.detected_files = {}
        self.installer._lock = threading.Lock()
        self.installer._callbacks = []
        self.installer._monitor_thread = None
        self.installer._stop_event = threading.Event()

    def tearDown(self):
        import shutil

        self.installer.stop_monitoring()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_start_monitoring(self):
        """测试开始监控"""
        self.installer.start_monitoring(interval=1)
        self.assertIsNotNone(self.installer._monitor_thread)
        self.assertTrue(self.installer._monitor_thread.is_alive())

        # 停止监控
        self.installer.stop_monitoring()
        self.assertFalse(self.installer._monitor_thread.is_alive())

    def test_start_monitoring_already_running(self):
        """测试重复开始监控"""
        self.installer.start_monitoring(interval=1)
        first_thread = self.installer._monitor_thread

        # 再次开始不应该创建新线程
        self.installer.start_monitoring(interval=1)
        self.assertIs(self.installer._monitor_thread, first_thread)

    def test_stop_monitoring_not_started(self):
        """测试停止未开始的监控"""
        # 不应该抛出异常
        self.installer.stop_monitoring()


class TestAutoInstallerEdgeCases(unittest.TestCase):
    """测试自动安装器边界条件"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.installer = AutoInstaller.__new__(AutoInstaller)
        self.installer.detected_files = {}
        self.installer._lock = threading.Lock()
        self.installer._callbacks = []
        self.installer._monitor_thread = None
        self.installer._stop_event = threading.Event()

    def tearDown(self):
        import shutil

        self.installer.stop_monitoring()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_permission_error_handling(self):
        """测试权限错误处理"""
        # 模拟权限错误
        with patch.object(Path, "iterdir", side_effect=PermissionError()):
            with patch.object(
                self.installer, "DOWNLOAD_PATHS", [self.temp_dir]
            ):
                detected = self.installer.scan_downloads()
                self.assertEqual(len(detected), 0)

    def test_callback_exception_handling(self):
        """测试回调异常处理"""

        def bad_callback(file_info):
            raise Exception("Callback error")

        self.installer.register_callback(bad_callback)

        # 不应该抛出异常
        file_info = DetectedFile(
            id="file-1",
            path="/test.exe",
            filename="test.exe",
            file_type=FileType.INSTALLER_EXE,
            size_bytes=0,
            size_display="0 B",
            modified_time=0,
        )
        try:
            self.installer._notify(file_info)
        except Exception:
            self.fail("_notify should not raise exception")


class TestGlobalAutoInstaller(unittest.TestCase):
    """测试全局自动安装器实例"""

    def test_global_instance_exists(self):
        """测试全局实例存在"""
        self.assertIsNotNone(auto_installer)
        self.assertIsInstance(auto_installer, AutoInstaller)

    def test_global_instance_is_singleton(self):
        """测试全局实例是单例"""
        from core.auto_installer import auto_installer as ai2

        self.assertIs(auto_installer, ai2)


if __name__ == "__main__":
    unittest.main()
