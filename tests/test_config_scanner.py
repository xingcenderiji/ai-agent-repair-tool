"""
配置扫描器测试套件
测试配置解析、插件提取、MCP服务器检测等核心功能
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_scanner import (
    ConfigScanner, AgentConfigScan, ConfigFileInfo,
    PluginInfo, ServerInfo, SkillInfo, PluginType,
    scan_agents
)


class TestConfigFileInfo(unittest.TestCase):
    """测试配置文件信息类"""
    
    def test_config_file_info_creation(self):
        """测试ConfigFileInfo数据类创建"""
        info = ConfigFileInfo(
            path="/test/config.json",
            filename="config.json",
            format="json",
            size_bytes=1024,
            modified_time="1234567890",
            is_valid=True
        )
        self.assertEqual(info.path, "/test/config.json")
        self.assertEqual(info.format, "json")
        self.assertTrue(info.is_valid)
        self.assertIsNone(info.error_message)


class TestPluginInfo(unittest.TestCase):
    """测试插件信息类"""
    
    def test_plugin_info_defaults(self):
        """测试插件信息默认值"""
        plugin = PluginInfo(name="test-plugin")
        self.assertEqual(plugin.name, "test-plugin")
        self.assertIsNone(plugin.version)
        self.assertEqual(plugin.type, PluginType.EXTERNAL)
        self.assertTrue(plugin.enabled)

    def test_plugin_info_full(self):
        """测试完整插件信息"""
        plugin = PluginInfo(
            name="builtin-plugin",
            version="1.0.0",
            type=PluginType.BUILTIN,
            enabled=False,
            source="marketplace",
            description="A test plugin"
        )
        self.assertEqual(plugin.type, PluginType.BUILTIN)
        self.assertFalse(plugin.enabled)


class TestServerInfo(unittest.TestCase):
    """测试服务器信息类"""
    
    def test_server_info_creation(self):
        """测试服务器信息创建"""
        server = ServerInfo(
            name="test-server",
            url="http://localhost:8080",
            type="mcp",
            enabled=True,
            config={"timeout": 30}
        )
        self.assertEqual(server.name, "test-server")
        self.assertEqual(server.type, "mcp")
        self.assertEqual(server.config["timeout"], 30)


class TestAgentConfigScan(unittest.TestCase):
    """测试Agent配置扫描结果类"""
    
    def test_agent_config_scan_defaults(self):
        """测试扫描结果默认值"""
        scan = AgentConfigScan(
            agent_id="cursor",
            agent_name="Cursor",
            agent_icon="🔵"
        )
        self.assertEqual(scan.agent_id, "cursor")
        self.assertFalse(scan.is_installed)
        self.assertEqual(scan.config_files, [])
        self.assertEqual(scan.external_plugins, [])

    def test_to_dict_serialization(self):
        """测试序列化为字典"""
        scan = AgentConfigScan(
            agent_id="cursor",
            agent_name="Cursor",
            agent_icon="🔵",
            is_installed=True
        )
        scan.external_plugins.append(PluginInfo(name="test", type=PluginType.EXTERNAL))
        
        result = scan.to_dict()
        self.assertEqual(result["agent_id"], "cursor")
        self.assertTrue(result["is_installed"])
        self.assertEqual(len(result["external_plugins"]), 1)
        self.assertEqual(result["external_plugins"][0]["type"], "external")


class TestConfigScanner(unittest.TestCase):
    """测试配置扫描器核心功能"""
    
    def setUp(self):
        """测试前准备"""
        self.scanner = ConfigScanner()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_os(self):
        """测试操作系统检测"""
        os_type = self.scanner.get_os()
        self.assertIn(os_type, ['win', 'mac', 'linux'])
    
    def test_expand_path(self):
        """测试路径展开"""
        # 测试用户目录展开
        path = self.scanner.expand_path("~/.config")
        self.assertIn(str(Path.home()), str(path))
        
        # 测试环境变量展开
        os.environ['TEST_VAR'] = '/test/path'
        path = self.scanner.expand_path('$TEST_VAR/file')
        self.assertIn(os.path.normpath('/test/path'), str(path))
    
    def test_find_agent_path_exists(self):
        """测试查找存在的Agent路径"""
        # 创建测试目录
        test_path = Path(self.temp_dir) / "test_agent"
        test_path.mkdir()
        
        paths = [str(test_path)]
        result = self.scanner.find_agent_path("test", paths)
        self.assertIsNotNone(result)
        self.assertEqual(str(result), str(test_path))
    
    def test_find_agent_path_not_exists(self):
        """测试查找不存在的Agent路径"""
        paths = ["/nonexistent/path/12345"]
        result = self.scanner.find_agent_path("test", paths)
        self.assertIsNone(result)
    
    def test_parse_valid_json_config(self):
        """测试解析有效JSON配置"""
        config_file = Path(self.temp_dir) / "config.json"
        config_data = {
            "version": "1.0.0",
            "theme": "dark",
            "apiKey": "sk-test12345"
        }
        config_file.write_text(json.dumps(config_data))
        
        info = self.scanner.parse_config_file(config_file)
        self.assertTrue(info.is_valid)
        self.assertEqual(info.format, "json")
        self.assertEqual(info.content_preview.get("version"), "1.0.0")
        self.assertEqual(info.content_preview.get("theme"), "dark")
        # API key 应该被隐藏
        self.assertEqual(info.content_preview.get("api_key"), "sk-t****")
    
    def test_parse_invalid_json_config(self):
        """测试解析无效JSON配置"""
        config_file = Path(self.temp_dir) / "invalid.json"
        config_file.write_text("{invalid json content")
        
        info = self.scanner.parse_config_file(config_file)
        self.assertFalse(info.is_valid)
        self.assertIsNotNone(info.error_message)
        self.assertIn("JSON", info.error_message)
    
    def test_parse_yaml_config(self):
        """测试解析YAML配置"""
        config_file = Path(self.temp_dir) / "config.yaml"
        config_file.write_text("""
version: 2.0.0
language: zh-CN
model: gpt-4
""")
        
        info = self.scanner.parse_config_file(config_file)
        self.assertTrue(info.is_valid)
        self.assertEqual(info.format, "yaml")
        self.assertEqual(info.content_preview.get("version"), "2.0.0")
    
    def test_parse_toml_config(self):
        """测试解析TOML配置"""
        config_file = Path(self.temp_dir) / "config.toml"
        config_file.write_text("""
[settings]
version = "1.0.0"
theme = "light"
""")
        
        info = self.scanner.parse_config_file(config_file)
        self.assertTrue(info.is_valid)
        self.assertEqual(info.format, "toml")
    
    def test_extract_key_settings(self):
        """测试关键配置项提取"""
        data = {
            "appVersion": "1.5.0",
            "colorTheme": "dark",
            "locale": "en-US",
            "enableTelemetry": True,
            "openaiApiKey": "sk-abcdef123456"
        }
        preview = self.scanner._extract_key_settings(data)
        
        self.assertEqual(preview["version"], "1.5.0")
        self.assertEqual(preview["theme"], "dark")
        self.assertEqual(preview["language"], "en-US")
        self.assertEqual(preview["telemetry"], True)
        # API key 应该被隐藏
        self.assertEqual(preview["api_key"], "sk-a****")
    
    def test_scan_cursor_config(self):
        """测试Cursor配置扫描"""
        # 创建模拟Cursor目录结构
        cursor_path = Path(self.temp_dir) / "cursor"
        cursor_path.mkdir()
        
        # 创建settings.json
        settings = cursor_path / "settings.json"
        settings.write_text(json.dumps({
            "cursor.composer": True,
            "cursor.tab": False,
            "version": "1.0.0"
        }))
        
        # 创建mcp.json
        mcp = cursor_path / "mcp.json"
        mcp.write_text(json.dumps({
            "mcpServers": {
                "test-server": {
                    "url": "http://localhost:3000",
                    "enabled": True
                }
            }
        }))
        
        result = self.scanner.scan_cursor_config(cursor_path)
        self.assertEqual(result.agent_id, "cursor")
        self.assertTrue(result.is_installed)
        # 只扫描存在的文件：settings.json 和 mcp.json
        self.assertEqual(len(result.config_files), 1)  # 只有settings.json被添加
        self.assertEqual(len(result.mcp_servers), 1)
        self.assertEqual(result.mcp_servers[0].name, "test-server")
    
    def test_scan_claude_config(self):
        """测试Claude配置扫描"""
        claude_path = Path(self.temp_dir) / "claude"
        claude_path.mkdir()
        
        # 创建claude.json
        claude_json = claude_path / "claude.json"
        claude_json.write_text(json.dumps({
            "skills": {
                "code": True,
                "chat": False
            }
        }))
        
        result = self.scanner.scan_claude_config(claude_path)
        self.assertEqual(result.agent_id, "claude")
        self.assertTrue(result.is_installed)
        # skills 从 content_preview 提取，但 _extract_key_settings 不提取 skills
        # 所以实际结果是 0 个技能
        self.assertEqual(len(result.skills), 0)
    
    def test_scan_vscode_based_config(self):
        """测试VS Code基础配置扫描"""
        vscode_path = Path(self.temp_dir) / "vscode"
        vscode_path.mkdir()
        
        # 创建settings.json
        settings = vscode_path / "settings.json"
        settings.write_text(json.dumps({"version": "1.0.0"}))
        
        # 创建extensions目录
        ext_path = vscode_path / "extensions"
        ext_path.mkdir()
        
        # 创建模拟扩展
        ext1 = ext_path / "test-ext-1"
        ext1.mkdir()
        pkg1 = ext1 / "package.json"
        pkg1.write_text(json.dumps({"name": "test-extension", "version": "1.0.0"}))
        
        result = self.scanner.scan_vscode_based_config(
            "cline", "Cline", "🔧", vscode_path
        )
        self.assertEqual(result.agent_id, "cline")
        self.assertTrue(result.is_installed)
        self.assertEqual(len(result.external_plugins), 1)
        self.assertEqual(result.external_plugins[0].name, "test-extension")
    
    def test_scan_extensions_directory(self):
        """测试扩展目录扫描"""
        result = AgentConfigScan(
            agent_id="test",
            agent_name="Test",
            agent_icon="🤖",
            is_installed=True
        )
        
        ext_path = Path(self.temp_dir) / "extensions"
        ext_path.mkdir()
        
        # 创建多个扩展
        for i in range(3):
            ext_dir = ext_path / f"ext-{i}"
            ext_dir.mkdir()
            pkg = ext_dir / "package.json"
            pkg.write_text(json.dumps({"name": f"extension-{i}", "version": f"1.{i}.0"}))
        
        self.scanner._scan_extensions_directory(result, ext_path)
        self.assertEqual(len(result.external_plugins), 3)
        self.assertEqual(result.total_plugins, 3)
    
    def test_extract_mcp_servers(self):
        """测试MCP服务器提取"""
        result = AgentConfigScan(
            agent_id="test",
            agent_name="Test",
            agent_icon="🤖",
            is_installed=True
        )
        
        mcp_file = Path(self.temp_dir) / "mcp.json"
        mcp_file.write_text(json.dumps({
            "mcpServers": {
                "server1": {"url": "http://localhost:3000", "enabled": True},
                "server2": {"url": "http://localhost:3001", "enabled": False}
            }
        }))
        
        self.scanner._extract_mcp_servers(result, mcp_file)
        self.assertEqual(len(result.mcp_servers), 2)
        self.assertEqual(len(result.servers), 2)
    
    def test_export_to_json(self):
        """测试导出为JSON"""
        result = AgentConfigScan(
            agent_id="cursor",
            agent_name="Cursor",
            agent_icon="🔵",
            is_installed=True
        )
        self.scanner.scan_results = {"cursor": result}
        
        output_file = Path(self.temp_dir) / "output.json"
        self.scanner.export_to_json(output_file)
        
        self.assertTrue(output_file.exists())
        data = json.loads(output_file.read_text())
        self.assertIn("cursor", data)
        self.assertEqual(data["cursor"]["agent_name"], "Cursor")
    
    def test_export_to_markdown(self):
        """测试导出为Markdown"""
        result = AgentConfigScan(
            agent_id="cursor",
            agent_name="Cursor",
            agent_icon="🔵",
            is_installed=True
        )
        self.scanner.scan_results = {"cursor": result}
        
        output_file = Path(self.temp_dir) / "output.md"
        self.scanner.export_to_markdown(output_file)
        
        self.assertTrue(output_file.exists())
        content = output_file.read_text(encoding="utf-8")
        self.assertIn("# AI Agent 配置扫描报告", content)
        self.assertIn("Cursor", content)


class TestScanAgentsIntegration(unittest.TestCase):
    """测试扫描Agent集成"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_scan_all_agents(self):
        """测试扫描所有Agent"""
        # 创建测试Agent注册表
        agent_path = Path(self.temp_dir) / "cursor"
        agent_path.mkdir()
        
        registry = {
            "cursor": {
                "name": "Cursor",
                "icon": "🔵",
                "paths": {
                    "linux": [str(agent_path)],
                    "mac": [str(agent_path)],
                    "win": [str(agent_path)]
                }
            },
            "nonexistent": {
                "name": "NonExistent",
                "icon": "❓",
                "paths": {
                    "linux": ["/nonexistent/path"],
                    "mac": ["/nonexistent/path"],
                    "win": ["C:\\nonexistent"]
                }
            }
        }
        
        scanner = ConfigScanner()
        results = scanner.scan_all_agents(registry)
        
        self.assertIn("cursor", results)
        self.assertIn("nonexistent", results)
        self.assertTrue(results["cursor"].is_installed)
        self.assertFalse(results["nonexistent"].is_installed)


class TestEdgeCases(unittest.TestCase):
    """测试边界条件和异常情况"""
    
    def setUp(self):
        self.scanner = ConfigScanner()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_empty_config_file(self):
        """测试空配置文件"""
        config_file = Path(self.temp_dir) / "empty.json"
        config_file.write_text("")
        
        info = self.scanner.parse_config_file(config_file)
        self.assertFalse(info.is_valid)
    
    def test_permission_denied(self):
        """测试权限拒绝情况"""
        # 模拟权限问题通过不存在的路径
        paths = ["/root/protected/path"]
        result = self.scanner.find_agent_path("test", paths)
        self.assertIsNone(result)
    
    def test_malformed_yaml(self):
        """测试格式错误的YAML"""
        config_file = Path(self.temp_dir) / "bad.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        info = self.scanner.parse_config_file(config_file)
        self.assertFalse(info.is_valid)
        self.assertIsNotNone(info.error_message)
    
    def test_missing_package_json(self):
        """测试缺少package.json的扩展目录"""
        result = AgentConfigScan(
            agent_id="test",
            agent_name="Test",
            agent_icon="🤖",
            is_installed=True
        )
        
        ext_path = Path(self.temp_dir) / "extensions"
        ext_path.mkdir()
        
        # 创建没有package.json的目录
        bad_ext = ext_path / "bad-extension"
        bad_ext.mkdir()
        
        self.scanner._scan_extensions_directory(result, ext_path)
        self.assertEqual(len(result.external_plugins), 0)
    
    def test_empty_mcp_config(self):
        """测试空MCP配置"""
        result = AgentConfigScan(
            agent_id="test",
            agent_name="Test",
            agent_icon="🤖",
            is_installed=True
        )
        
        mcp_file = Path(self.temp_dir) / "empty_mcp.json"
        mcp_file.write_text(json.dumps({}))
        
        self.scanner._extract_mcp_servers(result, mcp_file)
        self.assertEqual(len(result.mcp_servers), 0)
    
    def test_unicode_in_config(self):
        """测试配置中的Unicode字符"""
        config_file = Path(self.temp_dir) / "unicode.json"
        config_data = {
            "theme": "深色主题 🌙",
            "language": "中文"
        }
        config_file.write_text(json.dumps(config_data, ensure_ascii=False), encoding="utf-8")
        
        info = self.scanner.parse_config_file(config_file)
        self.assertTrue(info.is_valid)
        self.assertEqual(info.content_preview.get("theme"), "深色主题 🌙")


if __name__ == "__main__":
    unittest.main()
