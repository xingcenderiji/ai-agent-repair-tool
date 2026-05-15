"""
环境检测器测试套件
测试WSL、Termux、Docker、VM等虚拟化环境检测功能
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.env_detector import (
    EnvironmentDetector, EnvironmentInfo, EnvironmentType,
    detect_environment, is_virtual_env
)


class TestEnvironmentInfo(unittest.TestCase):
    """测试环境信息类"""
    
    def test_environment_info_defaults(self):
        """测试环境信息默认值"""
        info = EnvironmentInfo()
        self.assertEqual(info.type, EnvironmentType.UNKNOWN)
        self.assertEqual(info.type_display, "未知环境")
        self.assertTrue(info.is_valid)
        self.assertEqual(info.warnings, [])
        self.assertEqual(info.errors, [])
    
    def test_is_virtual_native(self):
        """测试原生环境判断"""
        info = EnvironmentInfo(type=EnvironmentType.NATIVE)
        self.assertFalse(info.is_virtual())
    
    def test_is_virtual_wsl(self):
        """测试WSL虚拟环境判断"""
        info = EnvironmentInfo(type=EnvironmentType.WSL2)
        self.assertTrue(info.is_virtual())
    
    def test_is_virtual_docker(self):
        """测试Docker虚拟环境判断"""
        info = EnvironmentInfo(type=EnvironmentType.DOCKER)
        self.assertTrue(info.is_virtual())
    
    def test_is_cross_environment(self):
        """测试跨环境判断"""
        info = EnvironmentInfo(
            can_access_host=True,
            target_system="windows"
        )
        self.assertTrue(info.is_cross_environment())
        
        info2 = EnvironmentInfo(can_access_host=False)
        self.assertFalse(info2.is_cross_environment())
    
    def test_get_icon(self):
        """测试图标获取"""
        self.assertEqual(EnvironmentInfo(type=EnvironmentType.NATIVE).get_icon(), "🖥️")
        self.assertEqual(EnvironmentInfo(type=EnvironmentType.WSL).get_icon(), "🐧")
        self.assertEqual(EnvironmentInfo(type=EnvironmentType.WSL2).get_icon(), "🪟")
        self.assertEqual(EnvironmentInfo(type=EnvironmentType.TERMUX).get_icon(), "📱")
        self.assertEqual(EnvironmentInfo(type=EnvironmentType.DOCKER).get_icon(), "🐳")
        self.assertEqual(EnvironmentInfo(type=EnvironmentType.VM).get_icon(), "🖧")
        self.assertEqual(EnvironmentInfo(type=EnvironmentType.UNKNOWN).get_icon(), "❓")
    
    def test_get_summary(self):
        """测试摘要获取"""
        info = EnvironmentInfo(type=EnvironmentType.WSL2, type_display="WSL2 (Ubuntu)")
        self.assertEqual(info.get_summary(), "🪟 WSL2 (Ubuntu)")


class TestEnvironmentDetector(unittest.TestCase):
    """测试环境检测器核心功能"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('core.env_detector.subprocess.run')
    def test_run_cmd_success(self, mock_run):
        """测试命令执行成功"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="test output",
            stderr=""
        )
        
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo()
        
        code, out, err = detector._run_cmd("echo test")
        self.assertEqual(code, 0)
        self.assertEqual(out, "test output")
    
    @patch('core.env_detector.subprocess.run')
    def test_run_cmd_timeout(self, mock_run):
        """测试命令执行超时"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 3)
        
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo()
        
        code, out, err = detector._run_cmd("sleep 10")
        self.assertEqual(code, -1)
        self.assertEqual(err, "命令超时")
    
    @patch('core.env_detector.subprocess.run')
    def test_run_cmd_not_found(self, mock_run):
        """测试命令不存在"""
        mock_run.side_effect = FileNotFoundError()
        
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo()
        
        code, out, err = detector._run_cmd("nonexistent_cmd")
        self.assertEqual(code, -1)
        self.assertEqual(err, "命令不存在")
    
    @patch('core.env_detector.platform.system')
    @patch('core.env_detector.platform.release')
    def test_detect_os_type_linux(self, mock_release, mock_system):
        """测试Linux系统检测"""
        mock_system.return_value = "Linux"
        mock_release.return_value = "5.15.0"
        
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo()
        
        detector._detect_os_type()
        self.assertEqual(detector.info.os_name, "Linux")
        self.assertEqual(detector.info.kernel_version, "5.15.0")
    
    @patch('core.env_detector.platform.system')
    @patch('core.env_detector.platform.release')
    def test_detect_os_type_windows(self, mock_release, mock_system):
        """测试Windows系统检测"""
        mock_system.return_value = "Windows"
        mock_release.return_value = "10.0.19044"
        
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo()
        
        with patch.object(detector, '_run_cmd', return_value=(0, "[Version 10.0.19044.1234]", "")):
            detector._detect_os_type()
            self.assertEqual(detector.info.os_name, "Windows")
    
    @patch('core.env_detector.platform.system')
    @patch('core.env_detector.platform.release')
    def test_detect_os_type_macos(self, mock_release, mock_system):
        """测试macOS系统检测"""
        mock_system.return_value = "Darwin"
        mock_release.return_value = "21.6.0"
        
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo()
        
        with patch.object(detector, '_run_cmd', return_value=(0, "12.6", "")):
            detector._detect_os_type()
            self.assertEqual(detector.info.os_name, "Darwin")
            self.assertEqual(detector.info.os_release, "12.6")
    
    @patch('core.env_detector.Path.exists')
    @patch('core.env_detector.subprocess.run')
    def test_detect_wsl2(self, mock_run, mock_exists):
        """测试WSL2检测"""
        mock_exists.side_effect = lambda p: "WSLInterop" in str(p) or "WSL" in str(p)
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="5.15.90.1-microsoft-standard-WSL2",
            stderr=""
        )
        
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo()
        detector._detect_os_type = MagicMock()
        
        detector._detect_wsl()
        self.assertEqual(detector.info.type, EnvironmentType.WSL2)
        self.assertEqual(detector.info.wsl_version, 2)
    
    @patch('core.env_detector.Path.exists')
    @patch('core.env_detector.subprocess.run')
    def test_detect_wsl1(self, mock_run, mock_exists):
        """测试WSL1检测"""
        mock_exists.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="4.4.0-19041-Microsoft",
            stderr=""
        )
        
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo()
        detector._detect_os_type = MagicMock()
        
        detector._detect_wsl()
        self.assertEqual(detector.info.type, EnvironmentType.WSL)
        self.assertEqual(detector.info.wsl_version, 1)
    
    @patch.dict(os.environ, {'TERMUX_VERSION': '0.118', 'PREFIX': '/data/data/com.termux/files/usr'})
    @patch('core.env_detector.Path.exists')
    def test_detect_termux(self, mock_exists):
        """测试Termux检测"""
        mock_exists.return_value = True
        
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo()
        detector._detect_os_type = MagicMock()
        
        detector._detect_termux()
        self.assertEqual(detector.info.type, EnvironmentType.TERMUX)
        self.assertEqual(detector.info.target_system, "android")
        self.assertIn("Termux", detector.info.warnings[0])
    
    @patch('core.env_detector.Path.exists')
    @patch('core.env_detector.subprocess.run')
    def test_detect_docker(self, mock_run, mock_exists):
        """测试Docker检测"""
        mock_exists.side_effect = lambda p: ".dockerenv" in str(p)
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="docker",
            stderr=""
        )
        
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo()
        detector._detect_os_type = MagicMock()
        
        detector._detect_docker()
        self.assertEqual(detector.info.type, EnvironmentType.DOCKER)
        self.assertIn("Docker", detector.info.warnings[0])
    
    @patch('core.env_detector.Path.exists')
    @patch('core.env_detector.Path.read_text')
    def test_detect_vm_virtualbox(self, mock_read, mock_exists):
        """测试VirtualBox VM检测"""
        mock_exists.return_value = True
        mock_read.return_value = "VirtualBox"
        
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo()
        detector.info.type = EnvironmentType.UNKNOWN  # 确保初始状态
        
        detector._detect_vm()
        self.assertEqual(detector.info.type, EnvironmentType.VM)
        self.assertIn("VirtualBox", detector.info.warnings[0])
    
    @patch('core.env_detector.Path.exists')
    @patch('core.env_detector.Path.read_text')
    def test_detect_vm_vmware(self, mock_read, mock_exists):
        """测试VMware VM检测"""
        mock_exists.return_value = True
        mock_read.return_value = "VMware Virtual Platform"
        
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo()
        detector.info.type = EnvironmentType.UNKNOWN
        
        detector._detect_vm()
        self.assertEqual(detector.info.type, EnvironmentType.VM)
    
    def test_is_virtual_environment(self):
        """测试虚拟环境判断方法"""
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo(type=EnvironmentType.DOCKER)
        self.assertTrue(detector.is_virtual_environment())
        
        detector.info.type = EnvironmentType.NATIVE
        self.assertFalse(detector.is_virtual_environment())
    
    def test_is_cross_environment(self):
        """测试跨环境判断方法"""
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo(
            can_access_host=True,
            target_system="windows"
        )
        self.assertTrue(detector.is_cross_environment())
    
    def test_validate_agent_path_exists(self):
        """测试验证存在的Agent路径"""
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo(type=EnvironmentType.NATIVE)
        
        with patch('core.env_detector.Path.exists', return_value=True):
            valid, msg = detector.validate_agent_path("cursor", "/test/path")
            self.assertTrue(valid)
            self.assertEqual(msg, "路径有效")
    
    def test_validate_agent_path_not_exists(self):
        """测试验证不存在的Agent路径"""
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo(type=EnvironmentType.NATIVE)
        
        with patch('core.env_detector.Path.exists', return_value=False):
            valid, msg = detector.validate_agent_path("cursor", "/nonexistent/path")
            self.assertFalse(valid)
            self.assertIn("路径不存在", msg)
    
    def test_validate_agent_path_docker_restricted(self):
        """测试Docker环境路径限制"""
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo(type=EnvironmentType.DOCKER)
        
        with patch('core.env_detector.Path.exists', return_value=True):
            valid, msg = detector.validate_agent_path("cursor", "/etc/config")
            self.assertFalse(valid)
            self.assertIn("Docker", msg)
    
    def test_validate_agent_path_wsl_host(self):
        """测试WSL访问Windows路径"""
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo(type=EnvironmentType.WSL2)
        
        with patch('core.env_detector.Path.exists', return_value=True):
            valid, msg = detector.validate_agent_path("cursor", "/mnt/c/Users/test")
            self.assertTrue(valid)
            self.assertIn("WSL2访问Windows路径", msg)
    
    def test_get_environment_warning_native(self):
        """测试原生环境警告（应为空）"""
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo(type=EnvironmentType.NATIVE)
        
        warning = detector.get_environment_warning()
        self.assertEqual(warning, "")
    
    def test_get_environment_warning_wsl(self):
        """测试WSL环境警告"""
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo(
            type=EnvironmentType.WSL2,
            can_access_host=True,
            target_system="windows"
        )
        
        warning = detector.get_environment_warning()
        self.assertIn("WSL环境警告", warning)
        self.assertIn("/mnt/c", warning)
    
    def test_get_environment_warning_termux(self):
        """测试Termux环境警告"""
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo(type=EnvironmentType.TERMUX)
        
        warning = detector.get_environment_warning()
        self.assertIn("Termux", warning)
        self.assertIn("Android", warning)
    
    def test_get_environment_warning_docker(self):
        """测试Docker环境警告"""
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo(type=EnvironmentType.DOCKER)
        
        warning = detector.get_environment_warning()
        self.assertIn("Docker", warning)
        self.assertIn("容器", warning)
    
    def test_to_dict(self):
        """测试转换为字典"""
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo(
            type=EnvironmentType.WSL2,
            type_display="WSL2 (Ubuntu)",
            os_name="Linux",
            wsl_version=2,
            can_access_host=True,
            target_system="windows",
            is_valid=True
        )
        
        data = detector.to_dict()
        self.assertEqual(data["type"], EnvironmentType.WSL2)
        self.assertEqual(data["type_display"], "WSL2 (Ubuntu)")
        self.assertEqual(data["os_name"], "Linux")
        self.assertEqual(data["wsl_version"], 2)
        self.assertTrue(data["is_virtual"])
        self.assertTrue(data["can_access_host"])
        self.assertIn("environment_warning", data)


class TestEnvironmentDetectionEdgeCases(unittest.TestCase):
    """测试环境检测边界条件"""
    
    def test_wsl_conf_parsing(self):
        """测试wsl.conf解析"""
        wsl_conf_content = """
[network]
generateHosts = false

[user]
default = ubuntu
name = Ubuntu-22.04
"""
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo()
        
        with patch('builtins.open', mock_open(read_data=wsl_conf_content)):
            with patch('core.env_detector.Path.exists', return_value=True):
                # 这里需要模拟完整的WSL检测流程
                pass  # 实际测试中需要更复杂的mock
    
    def test_os_release_parsing(self):
        """测试/etc/os-release解析"""
        os_release_content = """
PRETTY_NAME="Ubuntu 22.04.3 LTS"
NAME="Ubuntu"
VERSION_ID="22.04"
"""
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo()
        
        with patch('builtins.open', mock_open(read_data=os_release_content)):
            with patch('core.env_detector.Path.exists', return_value=True):
                with patch('core.env_detector.re.search') as mock_search:
                    mock_search.return_value = MagicMock(group=lambda x: "Ubuntu 22.04.3 LTS")
                    detector._detect_os_type()
    
    def test_multiple_virtualization_markers(self):
        """测试多种虚拟化标记同时存在"""
        # WSL和Docker标记同时存在时，应该优先检测到什么
        detector = EnvironmentDetector.__new__(EnvironmentDetector)
        detector.info = EnvironmentInfo()
        
        # 模拟同时存在WSL和Docker标记
        with patch('core.env_detector.Path.exists') as mock_exists:
            def side_effect(path):
                path_str = str(path)
                return any(marker in path_str for marker in [
                    "WSLInterop", ".dockerenv", ".containerenv"
                ])
            mock_exists.side_effect = side_effect
            
            with patch('core.env_detector.subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="5.15.90.1-microsoft-standard-WSL2",
                    stderr=""
                )
                
                detector._detect_wsl()
                # WSL检测应该优先
                self.assertIn(detector.info.type, [EnvironmentType.WSL, EnvironmentType.WSL2])


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""
    
    @patch('core.env_detector.EnvironmentDetector')
    def test_detect_environment(self, mock_detector_class):
        """测试detect_environment函数"""
        mock_info = EnvironmentInfo(type=EnvironmentType.NATIVE)
        mock_detector = MagicMock()
        mock_detector.info = mock_info
        mock_detector_class.return_value = mock_detector
        
        result = detect_environment()
        self.assertEqual(result.type, EnvironmentType.NATIVE)
    
    @patch('core.env_detector.EnvironmentDetector')
    def test_is_virtual_env(self, mock_detector_class):
        """测试is_virtual_env函数"""
        mock_info = EnvironmentInfo(type=EnvironmentType.DOCKER)
        mock_detector = MagicMock()
        mock_detector.is_virtual_environment.return_value = True
        mock_detector_class.return_value = mock_detector
        
        result = is_virtual_env()
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
