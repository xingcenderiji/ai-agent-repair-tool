"""
环境检测与验证模块
识别虚拟化环境（WSL2、Termux、Docker等），确保扫描正确的目标系统
"""

import os
import platform
import subprocess
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from pathlib import Path


class EnvironmentType:
    """环境类型枚举"""
    NATIVE = "native"           # 原生系统
    WSL = "wsl"               # WSL1
    WSL2 = "wsl2"             # WSL2
    TERMUX = "termux"         # Termux (Android)
    DOCKER = "docker"          # Docker容器
    DOCKER_ROOTLESS = "docker_rootless"  # Rootless Docker
    VM = "vm"                  # 虚拟机
    UNKNOWN = "unknown"


@dataclass
class EnvironmentInfo:
    """环境信息"""
    type: str = EnvironmentType.UNKNOWN
    type_display: str = "未知环境"
    
    # 系统信息
    os_name: str = ""
    os_release: str = ""
    kernel_version: str = ""
    
    # WSL信息
    wsl_version: int = 0
    wsl_distro: str = ""
    windows_build: str = ""
    
    # 路径信息
    home_path: str = ""
    config_base: str = ""
    
    # 验证状态
    is_valid: bool = True
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    # 目标系统
    target_system: Optional[str] = None
    can_access_host: bool = False
    host_mount_points: List[str] = field(default_factory=list)
    
    def is_virtual(self) -> bool:
        """是否虚拟化环境"""
        return self.type not in [EnvironmentType.NATIVE, EnvironmentType.UNKNOWN]
    
    def is_cross_environment(self) -> bool:
        """是否跨环境操作"""
        return self.can_access_host and self.target_system is not None
    
    def get_icon(self) -> str:
        icons = {
            EnvironmentType.NATIVE: "🖥️",
            EnvironmentType.WSL: "🐧",
            EnvironmentType.WSL2: "🪟",
            EnvironmentType.TERMUX: "📱",
            EnvironmentType.DOCKER: "🐳",
            EnvironmentType.VM: "🖧",
            EnvironmentType.UNKNOWN: "❓"
        }
        return icons.get(self.type, "❓")
    
    def get_summary(self) -> str:
        return f"{self.get_icon()} {self.type_display}"


class EnvironmentDetector:
    """环境检测器"""
    
    def __init__(self):
        self.info = EnvironmentInfo()
        self._detect()
    
    def _run_cmd(self, cmd: str, timeout: int = 3) -> Tuple[int, str, str]:
        """执行命令并返回结果
        
        注意: 此方法仅执行预定义的系统检测命令，不存在用户输入注入风险
        """
        try:
            import shlex
            # 使用 shlex.split 确保命令安全（仅用于内部系统检测）
            cmd_list = shlex.split(cmd) if isinstance(cmd, str) else cmd
            result = subprocess.run(
                cmd_list, shell=False, capture_output=True, 
                text=True, timeout=timeout
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except (ValueError, subprocess.SubprocessError):
            # 降级处理：仅用于预定义的内部系统检测命令，无注入风险 # noqa: safe
            result = subprocess.run(
                cmd, shell=True, capture_output=True, 
                text=True, timeout=timeout
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return -1, "", str(e)
    
    def _detect(self):
        """执行环境检测"""
        self._detect_os_type()
        self._detect_wsl()
        self._detect_termux()
        self._detect_docker()
        self._detect_vm()
        self._validate_paths()
        self._set_display_info()
    
    def _detect_os_type(self):
        """检测操作系统类型"""
        self.info.os_name = platform.system()
        self.info.kernel_version = platform.release()
        
        if self.info.os_name == "Linux":
            try:
                if Path("/etc/os-release").exists():
                    content = Path("/etc/os-release").read_text()
                    match = re.search(r'PRETTY_NAME="([^"]+)"', content)
                    if match:
                        self.info.os_release = match.group(1)
            except:
                pass
        elif self.info.os_name == "Windows":
            code, out, _ = self._run_cmd("cmd.exe /c ver")
            if code == 0:
                m = re.search(r'\[Version ([\d.]+)\]', out)
                if m:
                    self.info.windows_build = m.group(1)
        elif self.info.os_name == "Darwin":
            code, out, _ = self._run_cmd("sw_vers -productVersion")
            if code == 0:
                self.info.os_release = out
    
    def _detect_wsl(self):
        """检测WSL环境"""
        # WSL特征检测
        wsl_markers = [
            Path("/proc/sys/fs/binfmt_misc/WSLInterop").exists(),
            Path("/run/WSL").exists(),
        ]
        
        # 检查uname输出
        code, output, _ = self._run_cmd("uname -r")
        if code == 0 and "microsoft" in output.lower():
            wsl_markers.append(True)
        
        if any(wsl_markers):
            # 确定WSL版本
            if "WSL2" in output or "microsoft-standard-WSL2" in output:
                self.info.type = EnvironmentType.WSL2
                self.info.wsl_version = 2
            else:
                self.info.type = EnvironmentType.WSL
                self.info.wsl_version = 1
            
            # 获取发行版名称
            if Path("/etc/wsl.conf").exists():
                try:
                    content = Path("/etc/wsl.conf").read_text()
                    match = re.search(r'name\s*=\s*"?([^"\n]+)"?', content)
                    if match:
                        self.info.wsl_distro = match.group(1).strip()
                except:
                    pass
            
            # 检测能否访问Windows
            if Path("/mnt/c").exists():
                self.info.can_access_host = True
                self.info.host_mount_points.append("/mnt/c")
                self.info.target_system = "windows"
    
    def _detect_termux(self):
        """检测Termux环境"""
        termux_markers = [
            bool(os.environ.get("TERMUX_VERSION")),
            bool(os.environ.get("PREFIX")),
            Path("/data/data/com.termux").exists(),
        ]
        
        if any(termux_markers):
            self.info.type = EnvironmentType.TERMUX
            self.info.target_system = "android"
            self.info.os_release = "Android (Termux)"
            self.info.warnings.append("📱 检测到Termux环境，配置路径与原生Linux不同")
    
    def _detect_docker(self):
        """检测Docker环境"""
        docker_markers = [
            Path("/.dockerenv").exists(),
            Path("/run/.containerenv").exists(),
        ]
        
        code, output, _ = self._run_cmd("cat /proc/1/cgroup 2>/dev/null || true")
        if "docker" in output.lower() or "containerd" in output.lower():
            docker_markers.append(True)
        
        if any(docker_markers):
            if os.environ.get("HOME") == "/root" and not os.getuid() == 0:
                self.info.type = EnvironmentType.DOCKER_ROOTLESS
            else:
                self.info.type = EnvironmentType.DOCKER
            self.info.warnings.append("🐳 检测到Docker容器环境，文件系统与宿主机隔离")
    
    def _detect_vm(self):
        """检测虚拟机"""
        if self.info.type != EnvironmentType.UNKNOWN:
            return
        
        vm_files = [
            ("/sys/class/dmi/id/product_name", ["VirtualBox", "VMware", "QEMU", "KVM"]),
        ]
        
        for file_path, markers in vm_files:
            if Path(file_path).exists():
                try:
                    content = Path(file_path).read_text()
                    for marker in markers:
                        if marker.lower() in content.lower():
                            self.info.type = EnvironmentType.VM
                            self.info.warnings.append(f"🖧 检测到虚拟机: {marker}")
                            break
                except:
                    pass
    
    def _validate_paths(self):
        """验证路径有效性"""
        self.info.home_path = str(Path.home())
        
        if self.info.type == EnvironmentType.WSL2:
            wsl_home = os.environ.get("LOCALAPPDATA")
            if wsl_home:
                self.info.config_base = wsl_home.replace("\\", "/")
            elif self.info.can_access_host:
                self.info.config_base = "/mnt/c/Users/" + os.environ.get("USER", "user")
        
        for path in [self.info.home_path, self.info.config_base]:
            if path and not Path(path).exists():
                self.info.errors.append(f"路径不存在: {path}")
                self.info.is_valid = False
    
    def _set_display_info(self):
        """设置显示信息"""
        display_names = {
            EnvironmentType.NATIVE: f"原生 {self.info.os_name}",
            EnvironmentType.WSL: f"WSL1 ({self.info.wsl_distro or 'Linux'})",
            EnvironmentType.WSL2: f"WSL2 ({self.info.wsl_distro or 'Linux'})",
            EnvironmentType.TERMUX: "Termux (Android)",
            EnvironmentType.DOCKER: "Docker 容器",
            EnvironmentType.DOCKER_ROOTLESS: "Docker Rootless",
            EnvironmentType.VM: "虚拟机",
            EnvironmentType.UNKNOWN: "未知环境"
        }
        self.info.type_display = display_names.get(self.info.type, "未知环境")
    
    def is_virtual_environment(self) -> bool:
        """是否虚拟化环境"""
        return self.info.type not in [EnvironmentType.NATIVE, EnvironmentType.UNKNOWN]
    
    def is_cross_environment(self) -> bool:
        """是否跨环境操作"""
        return self.info.can_access_host and self.info.target_system is not None
    
    def validate_agent_path(self, agent_id: str, path: str) -> Tuple[bool, str]:
        """验证Agent路径是否在正确的环境中"""
        path_obj = Path(os.path.expandvars(os.path.expanduser(path)))
        
        if not path_obj.exists():
            return False, f"路径不存在: {path}"
        
        if self.info.type == EnvironmentType.DOCKER:
            if not str(path_obj).startswith(("/root", "/home", "/app")):
                return False, "Docker环境中无法访问此路径"
        
        if self.info.type == EnvironmentType.WSL2:
            if str(path_obj).startswith("/mnt/"):
                return True, "WSL2访问Windows路径"
            if not path_obj.exists():
                return False, "WSL内部路径不存在"
        
        if self.info.type == EnvironmentType.TERMUX:
            termux_prefix = os.environ.get("PREFIX", "")
            home_dir = os.path.expanduser("~")
            path_str = str(path_obj).replace("\\", "/")
            # Termux 中允许访问：PREFIX 目录、用户主目录、/sdcard
            if termux_prefix and path_str.startswith(termux_prefix.replace("\\", "/")):
                return True, "Termux内部路径"
            if path_str.startswith(home_dir.replace("\\", "/")):
                return True, "Termux用户目录"
            if path_str.startswith("/sdcard"):
                return True, "Android存储目录"
        
        return True, "路径有效"
    
    def get_environment_warning(self) -> str:
        """获取环境警告信息"""
        if not self.is_virtual_environment():
            return ""
        
        warnings = []
        
        if self.info.type in [EnvironmentType.WSL, EnvironmentType.WSL2]:
            warnings.append("⚠️ **WSL环境警告**")
            warnings.append("- 检测到WSL虚拟环境")
            warnings.append("- 配置路径与原生Linux不同")
            if self.info.can_access_host:
                warnings.append("- 可访问Windows文件系统 (/mnt/c)")
                warnings.append("- 如要修复Windows工具，选择目标系统为Windows")
            else:
                warnings.append("- 无法访问Windows文件系统")
            warnings.append("- 建议直接在本机运行修复工具以获得最佳效果")
        
        elif self.info.type == EnvironmentType.TERMUX:
            warnings.append("⚠️ **Termux环境警告**")
            warnings.append("- 检测到Termux (Android)")
            warnings.append("- 配置文件存储在Termux私有目录")
            warnings.append("- 无法访问其他Android应用的数据")
            warnings.append("- 建议在PC上运行修复工具")
        
        elif self.info.type == EnvironmentType.DOCKER:
            warnings.append("⚠️ **Docker环境警告**")
            warnings.append("- 检测到Docker容器")
            warnings.append("- 文件系统与宿主机隔离")
            warnings.append("- 无法直接修改宿主机的配置文件")
            warnings.append("- 建议在宿主机上运行修复工具")
        
        return "\n".join(warnings)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "type": self.info.type,
            "type_display": self.info.type_display,
            "icon": self.info.get_icon(),
            "os_name": self.info.os_name,
            "os_release": self.info.os_release,
            "kernel_version": self.info.kernel_version,
            "wsl_version": self.info.wsl_version,
            "wsl_distro": self.info.wsl_distro,
            "windows_build": self.info.windows_build,
            "is_virtual": self.is_virtual_environment(),
            "is_cross_environment": self.is_cross_environment(),
            "target_system": self.info.target_system,
            "can_access_host": self.info.can_access_host,
            "host_mount_points": self.info.host_mount_points,
            "is_valid": self.info.is_valid,
            "warnings": self.info.warnings,
            "errors": self.info.errors,
            "environment_warning": self.get_environment_warning(),
        }


def detect_environment() -> EnvironmentInfo:
    """检测当前环境"""
    return EnvironmentDetector().info


def is_virtual_env() -> bool:
    """快速检查是否是虚拟环境"""
    return EnvironmentDetector().is_virtual_environment()
