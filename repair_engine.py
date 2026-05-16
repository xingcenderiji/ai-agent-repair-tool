#!/usr/bin/env python3
"""
AI Agent 智能修复引擎
支持: OpenCode, Hermes-Agent, Claude Code, OpenClaw, Cursor, Windsurf 等

功能:
1. 自动检测Agent安装状态和配置完整性
2. 智能修复配置文件、缓存、插件、依赖等问题
3. 自动备份和恢复机制
4. 跨平台支持 (Windows/macOS/Linux)
"""

import json
import logging
import os
import platform
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent状态枚举"""

    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"
    NOT_INSTALLED = "not_installed"


class RepairType(Enum):
    """修复类型枚举"""

    CONFIG = "config"
    CACHE = "cache"
    PLUGINS = "plugins"
    DATA = "data"
    DEPS = "dependencies"


@dataclass
class AgentInfo:
    """Agent信息数据类"""

    id: str
    name: str
    status: AgentStatus
    install_path: Optional[Path]
    config_path: Optional[Path]
    version: Optional[str]
    last_check: Optional[str]
    issues: List[str]


@dataclass
class RepairResult:
    """修复结果数据类"""

    agent_id: str
    repair_type: RepairType
    success: bool
    message: str
    timestamp: str
    details: Optional[Dict] = None


class AIAgentRepairTool:
    """AI Agent智能修复工具主类"""

    # 支持的Agent配置
    AGENT_CONFIGS = {
        "opencode": {
            "name": "OpenCode",
            "paths": {
                "win": ["%USERPROFILE%/.opencode", "%APPDATA%/OpenCode"],
                "mac": [
                    "~/.opencode",
                    "~/Library/Application Support/OpenCode",
                ],
                "linux": ["~/.opencode", "~/.config/opencode"],
            },
            "config_files": ["settings.json", "config.yaml"],
            "cache_dirs": ["cache", "temp"],
            "plugin_dirs": ["plugins", "extensions"],
        },
        "hermes": {
            "name": "Hermes-Agent",
            "paths": {
                "win": ["%USERPROFILE%/.hermes", "%APPDATA%/Hermes"],
                "mac": ["~/.hermes", "~/Library/Application Support/Hermes"],
                "linux": ["~/.hermes", "~/.config/hermes"],
            },
            "config_files": ["config.json", "hermes.yaml"],
            "cache_dirs": ["cache", "logs"],
            "plugin_dirs": ["plugins"],
        },
        "claude": {
            "name": "Claude Code",
            "paths": {
                "win": ["%USERPROFILE%/.claude", "%APPDATA%/Claude"],
                "mac": ["~/.claude", "~/Library/Application Support/Claude"],
                "linux": ["~/.claude", "~/.config/claude"],
            },
            "config_files": ["settings.json", "claude.json"],
            "cache_dirs": ["cache", "conversations"],
            "plugin_dirs": ["skills", "extensions"],
        },
        "openclaw": {
            "name": "OpenClaw",
            "paths": {
                "win": ["%USERPROFILE%/.openclaw", "%APPDATA%/OpenClaw"],
                "mac": [
                    "~/.openclaw",
                    "~/Library/Application Support/OpenClaw",
                ],
                "linux": ["~/.openclaw", "~/.config/openclaw"],
            },
            "config_files": ["config.json"],
            "cache_dirs": ["cache"],
            "plugin_dirs": ["plugins"],
        },
        "cursor": {
            "name": "Cursor",
            "paths": {
                "win": ["%APPDATA%/Cursor", "%USERPROFILE%/.cursor"],
                "mac": ["~/Library/Application Support/Cursor", "~/.cursor"],
                "linux": ["~/.config/Cursor", "~/.cursor"],
            },
            "config_files": ["settings.json", "cursor.json"],
            "cache_dirs": ["Cache", "CachedData", "cache"],
            "plugin_dirs": ["extensions", "plugins"],
        },
        "windsurf": {
            "name": "Windsurf",
            "paths": {
                "win": ["%APPDATA%/Windsurf", "%USERPROFILE%/.windsurf"],
                "mac": [
                    "~/Library/Application Support/Windsurf",
                    "~/.windsurf",
                ],
                "linux": ["~/.config/Windsurf", "~/.windsurf"],
            },
            "config_files": ["settings.json"],
            "cache_dirs": ["cache", "CachedData"],
            "plugin_dirs": ["extensions"],
        },
    }

    def __init__(self, backup_dir: Optional[str] = None):
        """
        初始化修复工具

        Args:
            backup_dir: 备份目录路径，默认为用户主目录下的.ai_agent_backups
        """
        self.system = platform.system().lower()
        self.home = Path.home()

        if backup_dir:
            self.backup_dir = Path(backup_dir)
        else:
            self.backup_dir = self.home / ".ai_agent_backups"

        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[RepairResult] = []

        logger.info(
            f"修复工具初始化完成 - 系统: {platform.system()}, 备份目录: {self.backup_dir}"
        )

    def _expand_path(self, path: str) -> Path:
        """展开路径中的环境变量和~"""
        expanded = os.path.expandvars(os.path.expanduser(path))
        return Path(expanded)

    def _find_agent_path(self, agent_id: str) -> Optional[Path]:
        """查找Agent的安装路径"""
        if agent_id not in self.AGENT_CONFIGS:
            return None

        config = self.AGENT_CONFIGS[agent_id]
        system_key = (
            "win"
            if self.system == "windows"
            else ("mac" if self.system == "darwin" else "linux")
        )

        for path_template in config["paths"].get(system_key, []):
            path = self._expand_path(path_template)
            if path.exists():
                return path

        return None

    def scan_agent(self, agent_id: str) -> AgentInfo:
        """
        扫描指定Agent的状态

        Args:
            agent_id: Agent标识符

        Returns:
            AgentInfo对象包含扫描结果
        """
        logger.info(f"开始扫描Agent: {agent_id}")

        if agent_id not in self.AGENT_CONFIGS:
            return AgentInfo(
                id=agent_id,
                name=agent_id,
                status=AgentStatus.UNKNOWN,
                install_path=None,
                config_path=None,
                version=None,
                last_check=datetime.now().isoformat(),
                issues=["未知的Agent类型"],
            )

        config = self.AGENT_CONFIGS[agent_id]
        install_path = self._find_agent_path(agent_id)
        issues = []
        status = AgentStatus.HEALTHY

        if not install_path:
            return AgentInfo(
                id=agent_id,
                name=config["name"],
                status=AgentStatus.NOT_INSTALLED,
                install_path=None,
                config_path=None,
                version=None,
                last_check=datetime.now().isoformat(),
                issues=["Agent未安装"],
            )

        # 检查配置文件
        config_path = None
        for config_file in config["config_files"]:
            config_file_path = install_path / config_file
            if config_file_path.exists():
                config_path = config_file_path
                break

        if not config_path:
            issues.append("配置文件缺失")
            status = AgentStatus.ERROR
        else:
            # 验证配置文件JSON有效性
            if config_path.suffix == ".json":
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    issues.append(f"配置文件损坏: {e}")
                    status = AgentStatus.ERROR
                except Exception as e:
                    issues.append(f"配置文件读取错误: {e}")
                    status = AgentStatus.WARNING

        # 检查缓存目录大小
        for cache_dir_name in config["cache_dirs"]:
            cache_path = install_path / cache_dir_name
            if cache_path.exists():
                try:
                    total_size = sum(
                        f.stat().st_size
                        for f in cache_path.rglob("*")
                        if f.is_file()
                    )
                    size_mb = total_size / (1024 * 1024)
                    if size_mb > 500:  # 超过500MB警告
                        issues.append(f"缓存过大: {size_mb:.1f}MB")
                        if status == AgentStatus.HEALTHY:
                            status = AgentStatus.WARNING
                except Exception as e:
                    issues.append(f"缓存检查失败: {e}")

        # 检查插件目录
        for plugin_dir_name in config["plugin_dirs"]:
            plugin_path = install_path / plugin_dir_name
            if plugin_path.exists():
                try:
                    # 检查是否有损坏的插件
                    for item in plugin_path.iterdir():
                        if item.is_dir():
                            manifest = item / "package.json"
                            if manifest.exists():
                                try:
                                    with open(
                                        manifest, "r", encoding="utf-8"
                                    ) as f:
                                        json.load(f)
                                except json.JSONDecodeError:
                                    issues.append(f"插件损坏: {item.name}")
                                    if status == AgentStatus.HEALTHY:
                                        status = AgentStatus.WARNING
                except Exception as e:
                    issues.append(f"插件检查失败: {e}")

        # 获取版本信息
        version = None
        version_file = (
            install_path / "version"
            if (install_path / "version").exists()
            else None
        )
        if not version_file:
            version_file = (
                install_path / "package.json"
                if (install_path / "package.json").exists()
                else None
            )

        if version_file:
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    if version_file.suffix == ".json":
                        data = json.load(f)
                        version = data.get("version", "unknown")
                    else:
                        version = f.read().strip()
            except:
                pass

        if not issues:
            issues.append("运行正常")

        return AgentInfo(
            id=agent_id,
            name=config["name"],
            status=status,
            install_path=install_path,
            config_path=config_path,
            version=version,
            last_check=datetime.now().isoformat(),
            issues=issues,
        )

    def scan_all_agents(self) -> List[AgentInfo]:
        """扫描所有支持的Agent"""
        results = []
        for agent_id in self.AGENT_CONFIGS.keys():
            info = self.scan_agent(agent_id)
            results.append(info)
        return results

    def create_backup(
        self, agent_id: str, backup_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        为指定Agent创建备份

        Args:
            agent_id: Agent标识符
            backup_name: 备份名称，默认为时间戳

        Returns:
            (成功状态, 消息)
        """
        agent_info = self.scan_agent(agent_id)

        if agent_info.status == AgentStatus.NOT_INSTALLED:
            return False, f"Agent {agent_id} 未安装"

        if not agent_info.install_path:
            return False, f"无法找到 {agent_id} 的安装路径"

        if not backup_name:
            backup_name = (
                f"{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

        backup_path = self.backup_dir / backup_name

        try:
            # 创建备份目录
            backup_path.mkdir(parents=True, exist_ok=True)

            # 复制配置文件
            if agent_info.config_path and agent_info.config_path.exists():
                shutil.copy2(
                    agent_info.config_path,
                    backup_path / agent_info.config_path.name,
                )

            # 复制整个配置目录
            shutil.copytree(
                agent_info.install_path,
                backup_path / "full_backup",
                ignore=shutil.ignore_patterns(
                    "cache", "Cache", "temp", "Temp", "*.log"
                ),
                dirs_exist_ok=True,
            )

            # 创建备份元数据
            metadata = {
                "agent_id": agent_id,
                "agent_name": agent_info.name,
                "backup_time": datetime.now().isoformat(),
                "version": agent_info.version,
                "original_path": str(agent_info.install_path),
            }

            with open(
                backup_path / "backup_metadata.json", "w", encoding="utf-8"
            ) as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"备份创建成功: {backup_path}")
            return True, f"备份已创建: {backup_name}"

        except Exception as e:
            logger.error(f"备份创建失败: {e}")
            return False, f"备份失败: {str(e)}"

    def restore_backup(self, backup_name: str) -> Tuple[bool, str]:
        """
        从备份恢复Agent

        Args:
            backup_name: 备份名称

        Returns:
            (成功状态, 消息)
        """
        backup_path = self.backup_dir / backup_name

        if not backup_path.exists():
            return False, f"备份不存在: {backup_name}"

        metadata_path = backup_path / "backup_metadata.json"
        if not metadata_path.exists():
            return False, "备份元数据缺失"

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            agent_id = metadata["agent_id"]
            original_path = Path(metadata["original_path"])

            # 检查当前Agent状态
            current_info = self.scan_agent(agent_id)

            # 先创建当前状态的备份（以防万一）
            if current_info.status != AgentStatus.NOT_INSTALLED:
                self.create_backup(
                    agent_id,
                    f"{agent_id}_pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                )

            # 恢复备份
            full_backup_path = backup_path / "full_backup"
            if full_backup_path.exists():
                if original_path.exists():
                    # 重命名当前目录
                    backup_current = original_path.with_suffix(".backup")
                    original_path.rename(backup_current)

                # 复制备份到原位置
                shutil.copytree(
                    full_backup_path, original_path, dirs_exist_ok=True
                )

                logger.info(f"恢复完成: {agent_id}")
                return True, f"{metadata['agent_name']} 已成功恢复"
            else:
                return False, "备份数据不完整"

        except Exception as e:
            logger.error(f"恢复失败: {e}")
            return False, f"恢复失败: {str(e)}"

    def list_backups(self) -> List[Dict]:
        """列出所有备份"""
        backups = []

        if not self.backup_dir.exists():
            return backups

        for backup_path in self.backup_dir.iterdir():
            if backup_path.is_dir():
                metadata_path = backup_path / "backup_metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            metadata = json.load(f)

                        # 计算备份大小
                        total_size = sum(
                            f.stat().st_size
                            for f in backup_path.rglob("*")
                            if f.is_file()
                        )

                        backups.append(
                            {
                                "name": backup_path.name,
                                "agent_id": metadata.get("agent_id"),
                                "agent_name": metadata.get("agent_name"),
                                "backup_time": metadata.get("backup_time"),
                                "version": metadata.get("version"),
                                "size_mb": round(
                                    total_size / (1024 * 1024), 2
                                ),
                            }
                        )
                    except Exception as e:
                        logger.warning(
                            f"读取备份元数据失败: {backup_path.name}, {e}"
                        )

        # 按时间排序
        backups.sort(key=lambda x: x.get("backup_time", ""), reverse=True)
        return backups

    def repair_config(self, agent_id: str) -> RepairResult:
        """修复配置文件"""
        logger.info(f"修复 {agent_id} 的配置文件")

        agent_info = self.scan_agent(agent_id)

        if agent_info.status == AgentStatus.NOT_INSTALLED:
            return RepairResult(
                agent_id=agent_id,
                repair_type=RepairType.CONFIG,
                success=False,
                message="Agent未安装",
                timestamp=datetime.now().isoformat(),
            )

        config = self.AGENT_CONFIGS[agent_id]
        fixed_issues = []

        try:
            # 检查并修复配置文件
            for config_file in config["config_files"]:
                config_path = agent_info.install_path / config_file

                if not config_path.exists():
                    # 创建默认配置
                    default_config = self._get_default_config(agent_id)
                    with open(config_path, "w", encoding="utf-8") as f:
                        json.dump(default_config, f, indent=2)
                    fixed_issues.append(f"创建默认配置: {config_file}")
                else:
                    # 验证并修复JSON
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            json.load(f)
                    except json.JSONDecodeError:
                        # 备份损坏的文件
                        backup_file = config_path.with_suffix(".json.broken")
                        shutil.copy2(config_path, backup_file)

                        # 创建新的默认配置
                        default_config = self._get_default_config(agent_id)
                        with open(config_path, "w", encoding="utf-8") as f:
                            json.dump(default_config, f, indent=2)
                        fixed_issues.append(f"修复损坏配置: {config_file}")

            return RepairResult(
                agent_id=agent_id,
                repair_type=RepairType.CONFIG,
                success=True,
                message=(
                    "; ".join(fixed_issues) if fixed_issues else "配置文件正常"
                ),
                timestamp=datetime.now().isoformat(),
                details={"fixed": fixed_issues},
            )

        except Exception as e:
            return RepairResult(
                agent_id=agent_id,
                repair_type=RepairType.CONFIG,
                success=False,
                message=f"修复失败: {str(e)}",
                timestamp=datetime.now().isoformat(),
            )

    def repair_cache(self, agent_id: str) -> RepairResult:
        """清理缓存"""
        logger.info(f"清理 {agent_id} 的缓存")

        agent_info = self.scan_agent(agent_id)

        if agent_info.status == AgentStatus.NOT_INSTALLED:
            return RepairResult(
                agent_id=agent_id,
                repair_type=RepairType.CACHE,
                success=False,
                message="Agent未安装",
                timestamp=datetime.now().isoformat(),
            )

        config = self.AGENT_CONFIGS[agent_id]
        cleaned_dirs = []
        freed_space = 0

        try:
            for cache_dir_name in config["cache_dirs"]:
                cache_path = agent_info.install_path / cache_dir_name

                if cache_path.exists():
                    # 计算清理前大小
                    size_before = sum(
                        f.stat().st_size
                        for f in cache_path.rglob("*")
                        if f.is_file()
                    )

                    # 清理缓存目录
                    for item in cache_path.iterdir():
                        try:
                            if item.is_file():
                                item.unlink()
                            elif item.is_dir():
                                shutil.rmtree(item)
                        except Exception as e:
                            logger.warning(f"无法删除 {item}: {e}")

                    # 计算释放空间
                    size_after = sum(
                        f.stat().st_size
                        for f in cache_path.rglob("*")
                        if f.is_file()
                    )
                    freed = (size_before - size_after) / (1024 * 1024)

                    if freed > 0:
                        cleaned_dirs.append(
                            f"{cache_dir_name} ({freed:.1f}MB)"
                        )
                        freed_space += freed

            return RepairResult(
                agent_id=agent_id,
                repair_type=RepairType.CACHE,
                success=True,
                message=(
                    f"清理完成，释放 {freed_space:.1f}MB"
                    if freed_space > 0
                    else "缓存已清理"
                ),
                timestamp=datetime.now().isoformat(),
                details={"cleaned": cleaned_dirs, "freed_mb": freed_space},
            )

        except Exception as e:
            return RepairResult(
                agent_id=agent_id,
                repair_type=RepairType.CACHE,
                success=False,
                message=f"清理失败: {str(e)}",
                timestamp=datetime.now().isoformat(),
            )

    def repair_plugins(self, agent_id: str) -> RepairResult:
        """修复插件"""
        logger.info(f"修复 {agent_id} 的插件")

        agent_info = self.scan_agent(agent_id)

        if agent_info.status == AgentStatus.NOT_INSTALLED:
            return RepairResult(
                agent_id=agent_id,
                repair_type=RepairType.PLUGINS,
                success=False,
                message="Agent未安装",
                timestamp=datetime.now().isoformat(),
            )

        config = self.AGENT_CONFIGS[agent_id]
        fixed_plugins = []
        removed_plugins = []

        try:
            for plugin_dir_name in config["plugin_dirs"]:
                plugin_path = agent_info.install_path / plugin_dir_name

                if plugin_path.exists():
                    for item in plugin_path.iterdir():
                        if item.is_dir():
                            manifest = item / "package.json"
                            if manifest.exists():
                                try:
                                    with open(
                                        manifest, "r", encoding="utf-8"
                                    ) as f:
                                        json.load(f)
                                except json.JSONDecodeError:
                                    # 备份并移除损坏的插件
                                    broken_dir = item.with_suffix(".broken")
                                    item.rename(broken_dir)
                                    removed_plugins.append(item.name)
                            else:
                                # 没有manifest的插件目录
                                fixed_plugins.append(f"检查: {item.name}")

            return RepairResult(
                agent_id=agent_id,
                repair_type=RepairType.PLUGINS,
                success=True,
                message=(
                    f"移除 {len(removed_plugins)} 个损坏插件"
                    if removed_plugins
                    else "插件检查完成"
                ),
                timestamp=datetime.now().isoformat(),
                details={"removed": removed_plugins, "checked": fixed_plugins},
            )

        except Exception as e:
            return RepairResult(
                agent_id=agent_id,
                repair_type=RepairType.PLUGINS,
                success=False,
                message=f"修复失败: {str(e)}",
                timestamp=datetime.now().isoformat(),
            )

    def _get_default_config(self, agent_id: str) -> Dict:
        """获取默认配置"""
        defaults = {
            "opencode": {
                "version": "1.0.0",
                "settings": {"auto_update": True, "telemetry": False},
            },
            "hermes": {
                "version": "1.0.0",
                "config": {"debug": False, "log_level": "info"},
            },
            "claude": {
                "version": "1.0.0",
                "settings": {"theme": "dark", "auto_save": True},
            },
            "openclaw": {"version": "1.0.0", "config": {}},
            "cursor": {
                "version": "1.0.0",
                "settings": {"workbench.colorTheme": "Dark Modern"},
            },
            "windsurf": {"version": "1.0.0", "settings": {}},
        }
        return defaults.get(agent_id, {"version": "1.0.0"})

    def full_repair(
        self, agent_id: str, repair_types: List[RepairType] = None
    ) -> List[RepairResult]:
        """
        执行完整修复流程

        Args:
            agent_id: Agent标识符
            repair_types: 要执行的修复类型列表，默认为全部

        Returns:
            修复结果列表
        """
        if repair_types is None:
            repair_types = [
                RepairType.CONFIG,
                RepairType.CACHE,
                RepairType.PLUGINS,
            ]

        results = []

        # 先创建备份
        success, msg = self.create_backup(agent_id)
        logger.info(f"修复前备份: {msg}")

        # 执行各项修复
        for repair_type in repair_types:
            if repair_type == RepairType.CONFIG:
                result = self.repair_config(agent_id)
            elif repair_type == RepairType.CACHE:
                result = self.repair_cache(agent_id)
            elif repair_type == RepairType.PLUGINS:
                result = self.repair_plugins(agent_id)
            else:
                continue

            results.append(result)
            self.results.append(result)

        return results

    def generate_report(self) -> Dict:
        """生成修复报告"""
        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "platform": platform.system(),
                "version": platform.version(),
                "machine": platform.machine(),
            },
            "backup_dir": str(self.backup_dir),
            "results": [asdict(r) for r in self.results],
            "summary": {
                "total_repairs": len(self.results),
                "successful": sum(1 for r in self.results if r.success),
                "failed": sum(1 for r in self.results if not r.success),
            },
        }


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="AI Agent 智能修复工具")
    parser.add_argument(
        "--scan", action="store_true", help="扫描所有Agent状态"
    )
    parser.add_argument("--repair", type=str, help="修复指定Agent")
    parser.add_argument("--backup", type=str, help="备份指定Agent")
    parser.add_argument("--restore", type=str, help="从备份恢复")
    parser.add_argument(
        "--list-backups", action="store_true", help="列出所有备份"
    )
    parser.add_argument("--backup-dir", type=str, help="指定备份目录")

    args = parser.parse_args()

    tool = AIAgentRepairTool(backup_dir=args.backup_dir)

    if args.scan:
        print("=" * 60)
        print("AI Agent 系统扫描报告")
        print("=" * 60)

        for agent_info in tool.scan_all_agents():
            print(f"\n【{agent_info.name}】")
            print(f"  状态: {agent_info.status.value}")
            print(f"  路径: {agent_info.install_path or '未安装'}")
            print(f"  版本: {agent_info.version or '未知'}")
            print(f"  问题: {', '.join(agent_info.issues)}")

    elif args.repair:
        print(f"开始修复: {args.repair}")
        results = tool.full_repair(args.repair)

        for result in results:
            status = "✓" if result.success else "✗"
            print(f"{status} [{result.repair_type.value}] {result.message}")

    elif args.backup:
        success, msg = tool.create_backup(args.backup)
        print(msg)

    elif args.restore:
        success, msg = tool.restore_backup(args.restore)
        print(msg)

    elif args.list_backups:
        backups = tool.list_backups()
        print("=" * 60)
        print("备份列表")
        print("=" * 60)

        for backup in backups:
            print(f"\n{backup['name']}")
            print(f"  Agent: {backup['agent_name']}")
            print(f"  时间: {backup['backup_time']}")
            print(f"  大小: {backup['size_mb']}MB")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
