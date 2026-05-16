"""
AI Agent 配置扫描器
扫描各AI工具的配置信息、插件、服务器、技能等详细内容
"""

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class PluginType(Enum):
    BUILTIN = "builtin"  # 内置插件
    EXTERNAL = "external"  # 外部插件/扩展
    MARKETPLACE = "marketplace"  # 应用市场插件


@dataclass
class PluginInfo:
    """插件信息"""

    name: str
    version: Optional[str] = None
    type: PluginType = PluginType.EXTERNAL
    enabled: bool = True
    source: Optional[str] = None  # 来源（应用商店/本地等）
    description: Optional[str] = None


@dataclass
class ServerInfo:
    """服务器/MCP配置信息"""

    name: str
    url: Optional[str] = None
    type: str = "unknown"  # mcp, api, local等
    enabled: bool = True
    config: Dict = field(default_factory=dict)


@dataclass
class SkillInfo:
    """技能/功能开关信息"""

    name: str
    enabled: bool = True
    category: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ConfigFileInfo:
    """配置文件信息"""

    path: str
    filename: str
    format: str  # json, yaml, xml等
    size_bytes: int
    modified_time: str
    is_valid: bool
    error_message: Optional[str] = None
    content_preview: Optional[Dict] = None  # 关键配置预览


@dataclass
class AgentConfigScan:
    """单个Agent的完整扫描结果"""

    agent_id: str
    agent_name: str
    agent_icon: str
    install_path: Optional[str] = None
    is_installed: bool = False

    # 配置文件
    config_files: List[ConfigFileInfo] = field(default_factory=list)

    # 插件信息
    builtin_plugins: List[PluginInfo] = field(default_factory=list)
    external_plugins: List[PluginInfo] = field(default_factory=list)
    total_plugins: int = 0
    enabled_plugins: int = 0

    # 服务器/MCP
    servers: List[ServerInfo] = field(default_factory=list)
    mcp_servers: List[ServerInfo] = field(default_factory=list)

    # 技能/功能
    skills: List[SkillInfo] = field(default_factory=list)

    # 关键设置
    key_settings: Dict[str, Any] = field(default_factory=dict)

    # 扫描元数据
    scan_time: str = ""
    scan_duration_ms: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """转换为字典（用于JSON序列化）"""
        result = asdict(self)
        # 转换枚举类型
        for plugin in result.get("builtin_plugins", []):
            if isinstance(plugin.get("type"), PluginType):
                plugin["type"] = plugin["type"].value
        for plugin in result.get("external_plugins", []):
            if isinstance(plugin.get("type"), PluginType):
                plugin["type"] = plugin["type"].value
        return result


class ConfigScanner:
    """配置扫描器主类"""

    def __init__(self):
        self.scan_results: Dict[str, AgentConfigScan] = {}

    def get_os(self) -> str:
        """获取操作系统类型"""
        system = os.name
        if system == "nt":
            return "win"
        import platform

        if platform.system() == "Darwin":
            return "mac"
        return "linux"

    def expand_path(self, path: str) -> Path:
        """展开路径中的环境变量"""
        return Path(os.path.expandvars(os.path.expanduser(path)))

    def find_agent_path(
        self, agent_id: str, paths_config: List[str]
    ) -> Optional[Path]:
        """查找Agent安装路径"""
        for path_template in paths_config:
            try:
                path = self.expand_path(path_template)
                if path.exists():
                    return path
            except (OSError, ValueError):
                continue
        return None

    def parse_config_file(self, file_path: Path) -> ConfigFileInfo:
        """解析配置文件"""
        info = ConfigFileInfo(
            path=str(file_path),
            filename=file_path.name,
            format=file_path.suffix.lstrip("."),
            size_bytes=0,
            modified_time="",
            is_valid=False,
        )

        try:
            stat = file_path.stat()
            info.size_bytes = stat.st_size
            info.modified_time = str(stat.st_mtime)

            # 尝试解析内容
            content = file_path.read_text(encoding="utf-8", errors="ignore")

            if file_path.suffix == ".json":
                data = json.loads(content)
                info.is_valid = True
                info.content_preview = self._extract_key_settings(data)
            elif file_path.suffix in (".yaml", ".yml"):
                data = yaml.safe_load(content)
                info.is_valid = True
                info.content_preview = self._extract_key_settings(data)
            elif file_path.suffix == ".toml":
                # TOML简单处理
                info.is_valid = True
                info.content_preview = {"format": "toml"}
            else:
                info.is_valid = True

        except json.JSONDecodeError as e:
            info.error_message = f"JSON解析错误: {e}"
        except yaml.YAMLError as e:
            info.error_message = f"YAML解析错误: {e}"
        except Exception as e:
            info.error_message = str(e)

        return info

    def _extract_key_settings(self, data: Dict) -> Dict:
        """提取关键配置项预览"""
        preview = {}

        # 常见配置键
        key_mappings = {
            "version": ["version", "appVersion", "pluginVersion"],
            "theme": ["theme", "colorTheme", "appearance"],
            "language": ["language", "locale", "lang"],
            "auto_update": ["autoUpdate", "automaticUpdates", "updateMode"],
            "telemetry": ["telemetry", "enableTelemetry", "crashReporter"],
            "api_key": ["apiKey", "openaiApiKey", "anthropicApiKey"],
            "model": ["model", "defaultModel", "preferredModel"],
        }

        for key, possible_names in key_mappings.items():
            for name in possible_names:
                if name in data:
                    value = data[name]
                    # 隐藏敏感信息
                    if "key" in key.lower() and isinstance(value, str):
                        preview[key] = (
                            value[:4] + "****" if len(value) > 4 else "****"
                        )
                    else:
                        preview[key] = value
                    break

        return preview

    def scan_cursor_config(self, agent_path: Path) -> AgentConfigScan:
        """扫描 Cursor 配置"""
        result = AgentConfigScan(
            agent_id="cursor",
            agent_name="Cursor",
            agent_icon="🔵",
            install_path=str(agent_path),
            is_installed=True,
        )

        try:
            # 配置文件
            config_files = [
                agent_path / "settings.json",
                agent_path / "config.json",
                agent_path / "cursor.toml",
            ]

            for cf in config_files:
                if cf.exists():
                    info = self.parse_config_file(cf)
                    result.config_files.append(info)

                    # 从settings.json提取插件信息
                    if (
                        cf.name == "settings.json"
                        and info.is_valid
                        and info.content_preview
                    ):
                        self._extract_cursor_plugins(
                            result, info.content_preview
                        )

            # 扩展目录
            extensions_path = agent_path / "extensions"
            if extensions_path.exists():
                self._scan_extensions_directory(result, extensions_path)

            # MCP配置
            mcp_path = agent_path / "mcp.json"
            if mcp_path.exists():
                self._extract_mcp_servers(result, mcp_path)

        except Exception as e:
            result.errors.append(f"扫描失败: {e}")

        return result

    def _extract_cursor_plugins(self, result: AgentConfigScan, settings: Dict):
        """从Cursor设置中提取插件信息"""
        # 内置功能作为技能
        builtin_features = [
            "cursor.composer",
            "cursor.tab",
            "cursor.cmdK",
            "cursor.predictions",
            "cursor.autoImport",
        ]
        for feature in builtin_features:
            enabled = settings.get(feature, True)
            result.skills.append(
                SkillInfo(name=feature, enabled=enabled, category="core")
            )

    def _scan_extensions_directory(
        self, result: AgentConfigScan, ext_path: Path
    ):
        """扫描扩展目录"""
        try:
            for item in ext_path.iterdir():
                if item.is_dir():
                    # 检查package.json
                    pkg_file = item / "package.json"
                    if pkg_file.exists():
                        try:
                            pkg = json.loads(pkg_file.read_text())
                            plugin = PluginInfo(
                                name=pkg.get("name", item.name),
                                version=pkg.get("version"),
                                type=PluginType.EXTERNAL,
                                enabled=True,
                                source=str(item),
                            )
                            result.external_plugins.append(plugin)
                        except:
                            pass
        except:
            pass

        result.total_plugins = len(result.external_plugins)
        result.enabled_plugins = sum(
            1 for p in result.external_plugins if p.enabled
        )

    def _extract_mcp_servers(self, result: AgentConfigScan, mcp_path: Path):
        """提取MCP服务器配置"""
        try:
            data = json.loads(mcp_path.read_text())
            servers = data.get("mcpServers", {})
            for name, config in servers.items():
                server = ServerInfo(
                    name=name,
                    url=config.get("url"),
                    type="mcp",
                    enabled=config.get("enabled", True),
                    config={
                        k: v
                        for k, v in config.items()
                        if k not in ["url", "enabled"]
                    },
                )
                result.mcp_servers.append(server)
                result.servers.append(server)
        except:
            pass

    def scan_claude_config(self, agent_path: Path) -> AgentConfigScan:
        """扫描 Claude Code 配置"""
        result = AgentConfigScan(
            agent_id="claude",
            agent_name="Claude Code",
            agent_icon="🟠",
            install_path=str(agent_path),
            is_installed=True,
        )

        try:
            # 配置文件
            config_files = [
                agent_path / "settings.json",
                agent_path / "settings.local.json",
                agent_path / "config.json",
                agent_path / "claude.json",
            ]

            for cf in config_files:
                if cf.exists():
                    info = self.parse_config_file(cf)
                    result.config_files.append(info)

            # 从 settings.json 提取启用的插件
            settings_json = agent_path / "settings.json"
            if settings_json.exists():
                try:
                    settings_data = json.loads(
                        settings_json.read_text(encoding="utf-8")
                    )
                    enabled_plugins = settings_data.get("enabledPlugins", {})
                    for plugin_id, enabled in enabled_plugins.items():
                        plugin_name = (
                            plugin_id.split("@")[0]
                            if "@" in plugin_id
                            else plugin_id
                        )
                        result.external_plugins.append(
                            PluginInfo(
                                name=plugin_name,
                                version=None,
                                type=PluginType.MARKETPLACE,
                                enabled=enabled,
                                source=plugin_id,
                            )
                        )
                except Exception:
                    pass

            # 从 settings.local.json 提取 MCP 服务器
            settings_local = agent_path / "settings.local.json"
            if settings_local.exists():
                try:
                    local_data = json.loads(
                        settings_local.read_text(encoding="utf-8")
                    )
                    mcp_servers = local_data.get("mcpServers", {})
                    for name, config in mcp_servers.items():
                        cmd = config.get("command", "")
                        args = config.get("args", [])
                        url = config.get("url")
                        if not url and cmd:
                            url = f"{cmd} {' '.join(str(a) for a in args[:2])}"
                        server = ServerInfo(
                            name=name,
                            url=url,
                            type="mcp",
                            enabled=config.get("enabled", True),
                            config={
                                k: v
                                for k, v in config.items()
                                if k not in ["enabled"]
                            },
                        )
                        result.mcp_servers.append(server)
                        result.servers.append(server)
                except Exception:
                    pass

            # 独立 mcp.json 文件
            mcp_config = agent_path / "mcp.json"
            if mcp_config.exists():
                self._extract_mcp_servers(result, mcp_config)

            # 扫描已安装插件目录
            plugins_dir = agent_path / "plugins"
            if plugins_dir.exists():
                self._scan_claude_plugins(result, plugins_dir)

            # 扫描命令/技能目录
            commands_dir = agent_path / "commands"
            if commands_dir.exists():
                self._scan_claude_commands(result, commands_dir)

            # 扫描 skills 目录
            skills_dir = agent_path / "skills"
            if skills_dir.exists():
                self._scan_claude_commands(
                    result, skills_dir, category="skill"
                )

        except Exception as e:
            result.errors.append(f"扫描失败: {e}")

        return result

    def _scan_claude_plugins(self, result: AgentConfigScan, plugins_dir: Path):
        """扫描 Claude Code 插件目录"""
        try:
            # 读取 installed_plugins.json
            installed_file = plugins_dir / "installed_plugins.json"
            if installed_file.exists():
                data = json.loads(installed_file.read_text(encoding="utf-8"))
                plugins = data.get("plugins", {})
                for plugin_id, installations in plugins.items():
                    plugin_name = (
                        plugin_id.split("@")[0]
                        if "@" in plugin_id
                        else plugin_id
                    )
                    latest = installations[-1] if installations else {}
                    result.external_plugins.append(
                        PluginInfo(
                            name=plugin_name,
                            version=latest.get("version"),
                            type=PluginType.MARKETPLACE,
                            enabled=True,
                            source=plugin_id,
                            description=latest.get("installPath"),
                        )
                    )

            # 扫描 cache 目录中的实际插件
            cache_dir = plugins_dir / "cache"
            if cache_dir.exists():
                for marketplace_dir in cache_dir.iterdir():
                    if marketplace_dir.is_dir():
                        for plugin_dir in marketplace_dir.iterdir():
                            if plugin_dir.is_dir():
                                # 查找 plugin.json 或 package.json
                                for manifest_name in [
                                    "plugin.json",
                                    "package.json",
                                ]:
                                    manifest = plugin_dir / manifest_name
                                    if manifest.exists():
                                        try:
                                            pkg = json.loads(
                                                manifest.read_text(
                                                    encoding="utf-8"
                                                )
                                            )
                                            # 避免重复（已从 installed_plugins.json 添加）
                                            existing = {
                                                p.name
                                                for p in result.external_plugins
                                            }
                                            name = pkg.get(
                                                "name", plugin_dir.name
                                            )
                                            if name not in existing:
                                                result.external_plugins.append(
                                                    PluginInfo(
                                                        name=name,
                                                        version=pkg.get(
                                                            "version"
                                                        ),
                                                        type=PluginType.EXTERNAL,
                                                        enabled=True,
                                                        source=str(plugin_dir),
                                                    )
                                                )
                                        except Exception:
                                            pass
                                        break
        except Exception:
            pass

        result.total_plugins = len(result.external_plugins)
        result.enabled_plugins = sum(
            1 for p in result.external_plugins if p.enabled
        )

    def _scan_claude_commands(
        self,
        result: AgentConfigScan,
        commands_dir: Path,
        category: str = "command",
    ):
        """扫描 Claude Code 命令/技能目录"""
        try:
            for item in commands_dir.iterdir():
                if item.is_file() and item.suffix == ".md":
                    result.skills.append(
                        SkillInfo(
                            name=item.stem,
                            enabled=True,
                            category=category,
                            description=f"{category}: {item.name}",
                        )
                    )
                elif item.is_dir():
                    # 子目录中的命令
                    for sub_item in item.iterdir():
                        if sub_item.is_file() and sub_item.suffix == ".md":
                            result.skills.append(
                                SkillInfo(
                                    name=f"{item.name}/{sub_item.stem}",
                                    enabled=True,
                                    category=category,
                                    description=f"{category}: {item.name}/{sub_item.name}",
                                )
                            )
        except Exception:
            pass

    def scan_vscode_based_config(
        self, agent_id: str, agent_name: str, agent_icon: str, agent_path: Path
    ) -> AgentConfigScan:
        """扫描基于VS Code的Agent配置（Cline, Continue等）"""
        result = AgentConfigScan(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_icon=agent_icon,
            install_path=str(agent_path),
            is_installed=True,
        )

        try:
            # 配置文件
            config_files = [
                agent_path / "settings.json",
                agent_path / "config.json",
                agent_path / "config.yaml",
            ]

            for cf in config_files:
                if cf.exists():
                    info = self.parse_config_file(cf)
                    result.config_files.append(info)

                    # 从 settings.json 提取 MCP 服务器配置
                    if cf.name == "settings.json" and info.is_valid:
                        try:
                            settings_data = json.loads(
                                cf.read_text(encoding="utf-8")
                            )
                            mcp_servers = settings_data.get("mcpServers", {})
                            for name, config in mcp_servers.items():
                                if isinstance(config, dict):
                                    server = ServerInfo(
                                        name=name,
                                        url=config.get("url"),
                                        type="mcp",
                                        enabled=config.get("enabled", True),
                                        config={
                                            k: v
                                            for k, v in config.items()
                                            if k not in ["url", "enabled"]
                                        },
                                    )
                                    result.mcp_servers.append(server)
                                    result.servers.append(server)
                        except Exception:
                            pass

            # 扩展目录（Agent 本地）
            extensions_path = agent_path / "extensions"
            if extensions_path.exists():
                self._scan_extensions_directory(result, extensions_path)

            # 全局 VS Code 扩展目录
            vscode_extensions = self._find_vscode_extensions()
            if vscode_extensions and vscode_extensions.exists():
                self._scan_vscode_global_extensions(
                    result, vscode_extensions, agent_id
                )

            # 全局存储
            global_storage = agent_path / "globalStorage"
            if global_storage.exists():
                self._scan_global_storage(result, global_storage)

        except Exception as e:
            result.errors.append(f"扫描失败: {e}")

        return result

    def _find_vscode_extensions(self) -> Optional[Path]:
        """查找全局 VS Code 扩展目录"""
        os_type = self.get_os()
        candidates = []
        if os_type == "win":
            candidates = [
                Path(os.path.expandvars(r"%USERPROFILE%\.vscode\extensions")),
                Path(os.path.expandvars(r"%APPDATA%\Code\User\extensions")),
            ]
        elif os_type == "mac":
            candidates = [
                Path.home() / ".vscode" / "extensions",
            ]
        else:
            candidates = [
                Path.home() / ".vscode" / "extensions",
            ]
        for path in candidates:
            if path.exists():
                return path
        return None

    def _scan_vscode_global_extensions(
        self, result: AgentConfigScan, ext_path: Path, agent_id: str
    ):
        """扫描全局 VS Code 扩展目录中与 Agent 相关的扩展"""
        agent_keywords = {
            "cline": ["cline", "claude-dev"],
            "continue": ["continue"],
            "copilot": ["copilot", "github-copilot"],
            "windsurf": ["windsurf", "codeium"],
        }
        keywords = agent_keywords.get(agent_id, [agent_id])

        try:
            for item in ext_path.iterdir():
                if not item.is_dir():
                    continue
                item_lower = item.name.lower()
                if any(kw in item_lower for kw in keywords):
                    pkg_file = item / "package.json"
                    if pkg_file.exists():
                        try:
                            pkg = json.loads(
                                pkg_file.read_text(encoding="utf-8")
                            )
                            result.external_plugins.append(
                                PluginInfo(
                                    name=pkg.get(
                                        "displayName",
                                        pkg.get("name", item.name),
                                    ),
                                    version=pkg.get("version"),
                                    type=PluginType.EXTERNAL,
                                    enabled=True,
                                    source=str(item),
                                )
                            )
                        except Exception:
                            pass
        except Exception:
            pass

        result.total_plugins = len(result.external_plugins)
        result.enabled_plugins = sum(
            1 for p in result.external_plugins if p.enabled
        )

    def _scan_global_storage(
        self, result: AgentConfigScan, storage_path: Path
    ):
        """扫描全局存储中的配置"""
        try:
            for item in storage_path.iterdir():
                if item.is_dir():
                    # 查找特定扩展的配置
                    state_db = item / "state.vscdb"
                    if state_db.exists():
                        try:
                            content = state_db.read_text()
                            # 简单提取关键信息
                            if (
                                '"mcpServers"' in content
                                or '"servers"' in content
                            ):
                                result.warnings.append(
                                    f"发现服务器配置: {item.name}"
                                )
                        except:
                            pass
        except:
            pass

    def scan_all_agents(
        self, agent_registry: Dict
    ) -> Dict[str, AgentConfigScan]:
        """扫描所有已安装的Agent"""
        import time
        from datetime import datetime

        os_type = self.get_os()
        results = {}

        for agent_id, config in agent_registry.items():
            start_time = time.time()

            # 查找安装路径
            paths = config.get("paths", {}).get(os_type, [])
            agent_path = self.find_agent_path(agent_id, paths)

            if not agent_path:
                # 未安装，创建空结果
                result = AgentConfigScan(
                    agent_id=agent_id,
                    agent_name=config.get("name", agent_id),
                    agent_icon=config.get("icon", "🤖"),
                    is_installed=False,
                )
            else:
                # 根据Agent类型选择扫描方法
                if agent_id == "cursor":
                    result = self.scan_cursor_config(agent_path)
                elif agent_id == "claude":
                    result = self.scan_claude_config(agent_path)
                elif agent_id in ["cline", "continue", "copilot", "windsurf"]:
                    result = self.scan_vscode_based_config(
                        agent_id,
                        config.get("name", agent_id),
                        config.get("icon", "🤖"),
                        agent_path,
                    )
                else:
                    # 通用扫描
                    result = self.scan_vscode_based_config(
                        agent_id,
                        config.get("name", agent_id),
                        config.get("icon", "🤖"),
                        agent_path,
                    )

            result.scan_time = datetime.now().isoformat()
            result.scan_duration_ms = int((time.time() - start_time) * 1000)
            results[agent_id] = result

        self.scan_results = results
        return results

    def export_to_json(self, output_path: Path):
        """导出扫描结果为JSON"""
        data = {
            agent_id: result.to_dict()
            for agent_id, result in self.scan_results.items()
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def export_to_markdown(self, output_path: Path):
        """导出扫描结果为Markdown报告"""
        lines = [
            "# AI Agent 配置扫描报告\n",
            f"生成时间: {datetime.now().isoformat()}\n\n",
        ]

        for agent_id, result in self.scan_results.items():
            if not result.is_installed:
                lines.append(f"## {result.agent_icon} {result.agent_name}\n\n")
                lines.append("- **状态**: 未安装\n\n")
                continue

            lines.append(f"## {result.agent_icon} {result.agent_name}\n\n")
            lines.append(f"- **安装路径**: `{result.install_path}`\n")
            lines.append(f"- **扫描耗时**: {result.scan_duration_ms}ms\n\n")

            # 配置文件
            if result.config_files:
                lines.append("### 配置文件\n\n")
                for cf in result.config_files:
                    status = "✅" if cf.is_valid else "❌"
                    lines.append(
                        f"- {status} `{cf.filename}` ({cf.size_bytes} bytes)\n"
                    )
                lines.append("\n")

            # 插件
            if result.external_plugins:
                lines.append(f"### 插件 ({result.total_plugins}个)\n\n")
                for plugin in result.external_plugins[:10]:  # 最多显示10个
                    enabled = "✅" if plugin.enabled else "❌"
                    lines.append(
                        f"- {enabled} **{plugin.name}** v{plugin.version or '?'}\n"
                    )
                if len(result.external_plugins) > 10:
                    lines.append(
                        f"- ... 还有 {len(result.external_plugins) - 10} 个插件\n"
                    )
                lines.append("\n")

            # MCP服务器
            if result.mcp_servers:
                lines.append(
                    f"### MCP服务器 ({len(result.mcp_servers)}个)\n\n"
                )
                for server in result.mcp_servers:
                    enabled = "✅" if server.enabled else "❌"
                    lines.append(
                        f"- {enabled} **{server.name}** ({server.type})\n"
                    )
                lines.append("\n")

            # 技能/功能
            if result.skills:
                lines.append(f"### 技能/功能 ({len(result.skills)}个)\n\n")
                for skill in result.skills[:10]:
                    enabled = "✅" if skill.enabled else "❌"
                    lines.append(f"- {enabled} {skill.name}\n")
                lines.append("\n")

            # 错误和警告
            if result.errors:
                lines.append("### ❌ 错误\n\n")
                for error in result.errors:
                    lines.append(f"- {error}\n")
                lines.append("\n")

            if result.warnings:
                lines.append("### ⚠️ 警告\n\n")
                for warning in result.warnings:
                    lines.append(f"- {warning}\n")
                lines.append("\n")

            lines.append("---\n\n")

        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(lines)


# 便捷函数
def scan_agents(agent_registry: Dict) -> Dict[str, AgentConfigScan]:
    """便捷函数：扫描所有Agent配置"""
    scanner = ConfigScanner()
    return scanner.scan_all_agents(agent_registry)
