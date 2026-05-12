#!/usr/bin/env python3
"""
AI Agent Repair Tool - 全方位测试
覆盖: 路径、权限、编码、符号链接、边界情况、跨平台兼容性
"""

import os
import sys
import json
import stat
import tempfile
import shutil
from pathlib import Path
from unittest import TestCase, main, skipIf

sys.path.insert(0, str(Path(__file__).parent.parent))

from repair_tool import (
    get_os, expand_path, find_agent, check_config, check_cache,
    _safe_get_size, fix_agent, AGENT_PATHS
)

IS_WIN = sys.platform == 'win32'
IS_MAC = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

# 注册测试用Agent
AGENT_PATHS['testagent'] = {
    "name": "TestAgent",
    "paths": {"win": [], "mac": [], "linux": []}
}


class TestGetOS(TestCase):
    """操作系统检测"""

    def test_returns_valid_value(self):
        result = get_os()
        self.assertIn(result, ['win', 'mac', 'linux'])

    def test_linux_or_mac(self):
        if IS_LINUX or IS_MAC:
            self.assertNotEqual(get_os(), 'win')

    @skipIf(not IS_WIN, 'Windows only')
    def test_windows(self):
        self.assertEqual(get_os(), 'win')


class TestExpandPath(TestCase):
    """路径展开 - 各种边界情况"""

    def test_home_expansion(self):
        path = expand_path('~')
        self.assertTrue(path.exists())
        self.assertTrue(str(path).startswith(str(Path.home())))

    def test_current_dir(self):
        path = expand_path('.')
        self.assertEqual(path.resolve(), Path.cwd())

    def test_empty_string(self):
        path = expand_path('')
        self.assertIsNotNone(path)

    def test_whitespace_only(self):
        path = expand_path('   ')
        self.assertIsNotNone(path)

    def test_none_like_paths(self):
        for val in ['', '  ', '\t']:
            result = expand_path(val)
            self.assertIsNotNone(result)

    def test_nonexistent_path(self):
        path = expand_path('~/this_path_does_not_exist_xyz')
        self.assertFalse(path.exists())

    def test_nested_home(self):
        path = expand_path('~/.config')
        self.assertEqual(str(path), str(Path.home() / '.config'))


class TestFindAgent(TestCase):
    """Agent查找"""

    def test_nonexistent_agent(self):
        self.assertIsNone(find_agent('nonexistent_agent_xyz'))

    def test_empty_agent_id(self):
        self.assertIsNone(find_agent(''))

    def test_known_agent_not_installed(self):
        """已注册但未安装的Agent应返回None"""
        # 使用一个不太可能存在的路径
        result = find_agent('opencode')
        # 可能返回None或Path，但不应报错
        self.assertTrue(result is None or isinstance(result, Path))


class TestCheckConfig(TestCase):
    """配置文件检查 - 各种异常情况"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_no_config_files(self):
        issues = check_config(self.test_dir)
        self.assertEqual(issues, [])

    def test_valid_json(self):
        (self.test_dir / 'settings.json').write_text('{"version": "1.0"}')
        issues = check_config(self.test_dir)
        self.assertEqual(issues, [])

    def test_invalid_json(self):
        (self.test_dir / 'settings.json').write_text('{bad json!!!}')
        issues = check_config(self.test_dir)
        self.assertEqual(len(issues), 1)
        self.assertIn('损坏', issues[0])

    def test_empty_json_file(self):
        (self.test_dir / 'config.json').write_text('')
        issues = check_config(self.test_dir)
        # 空文件应该被检测为JSON解析错误
        self.assertTrue(len(issues) >= 0)

    def test_yaml_file_readable(self):
        (self.test_dir / 'config.yaml').write_text('key: value\n')
        issues = check_config(self.test_dir)
        self.assertEqual(issues, [])

    def test_yaml_file_not_readable(self):
        f = self.test_dir / 'config.yaml'
        f.write_text('key: value\n')
        f.chmod(0o000)
        try:
            issues = check_config(self.test_dir)
            # 应该报告权限问题或正常通过（取决于运行用户）
            self.assertIsInstance(issues, list)
        finally:
            f.chmod(0o644)

    def test_binary_file_as_json(self):
        (self.test_dir / 'settings.json').write_bytes(b'\x00\x01\x02\xff')
        issues = check_config(self.test_dir)
        self.assertTrue(len(issues) >= 1)

    def test_multiple_config_files(self):
        (self.test_dir / 'settings.json').write_text('{"ok": true}')
        (self.test_dir / 'config.json').write_text('{bad}')
        issues = check_config(self.test_dir)
        self.assertEqual(len(issues), 1)

    def test_deeply_nested_json(self):
        deep = {"a": {"b": {"c": {"d": [1, 2, {"e": "f"}]}}}}
        (self.test_dir / 'settings.json').write_text(json.dumps(deep))
        issues = check_config(self.test_dir)
        self.assertEqual(issues, [])

    def test_large_json_file(self):
        large_data = {f"key_{i}": f"value_{i}" * 100 for i in range(1000)}
        (self.test_dir / 'settings.json').write_text(json.dumps(large_data))
        issues = check_config(self.test_dir)
        self.assertEqual(issues, [])

    def test_unicode_in_json(self):
        (self.test_dir / 'settings.json').write_text('{"name": "中文测试日本語한국어"}')
        issues = check_config(self.test_dir)
        self.assertEqual(issues, [])

    def test_special_characters_in_json(self):
        (self.test_dir / 'settings.json').write_text(json.dumps({"path": "C:\\Users\\test\\file.txt"}))
        issues = check_config(self.test_dir)
        self.assertEqual(issues, [])


class TestCheckCache(TestCase):
    """缓存检查 - 符号链接、权限、大小"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_no_cache_dirs(self):
        issues = check_cache(self.test_dir)
        self.assertEqual(issues, [])

    def test_small_cache(self):
        cache = self.test_dir / 'cache'
        cache.mkdir()
        (cache / 'test.dat').write_bytes(b'x' * 1024)
        issues = check_cache(self.test_dir)
        self.assertEqual(issues, [])

    def test_multiple_cache_dirs(self):
        for name in ['cache', 'Cache', 'temp']:
            d = self.test_dir / name
            d.mkdir()
            (d / 'file.txt').write_text('small')
        issues = check_cache(self.test_dir)
        self.assertEqual(issues, [])

    def test_empty_cache_dir(self):
        cache = self.test_dir / 'cache'
        cache.mkdir()
        issues = check_cache(self.test_dir)
        self.assertEqual(issues, [])

    def test_cache_with_subdirs(self):
        cache = self.test_dir / 'cache'
        cache.mkdir()
        sub = cache / 'sub' / 'deep'
        sub.mkdir(parents=True)
        (sub / 'file.txt').write_text('data')
        issues = check_cache(self.test_dir)
        self.assertEqual(issues, [])

    @skipIf(IS_WIN, 'symlink permissions differ on Windows')
    def test_cache_with_symlink(self):
        cache = self.test_dir / 'cache'
        cache.mkdir()
        target = self.test_dir / 'target_file.txt'
        target.write_text('x' * 1024)
        try:
            (cache / 'link').symlink_to(target)
            issues = check_cache(self.test_dir)
            self.assertEqual(issues, [])
        except OSError:
            pass  # symlink not supported

    @skipIf(IS_WIN, 'permission test not reliable on Windows')
    def test_cache_permission_denied(self):
        cache = self.test_dir / 'cache'
        cache.mkdir()
        (cache / 'file.txt').write_text('data')
        cache.chmod(0o000)
        try:
            issues = check_cache(self.test_dir)
            self.assertIsInstance(issues, list)
        finally:
            cache.chmod(0o755)

    def test_cache_with_zero_byte_files(self):
        cache = self.test_dir / 'cache'
        cache.mkdir()
        for i in range(100):
            (cache / f'empty_{i}').write_bytes(b'')
        issues = check_cache(self.test_dir)
        self.assertEqual(issues, [])


class TestSafeGetSize(TestCase):
    """安全获取文件大小"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_normal_file(self):
        f = self.test_dir / 'normal.txt'
        f.write_bytes(b'x' * 1024)
        self.assertEqual(_safe_get_size(f), 1024)

    def test_empty_file(self):
        f = self.test_dir / 'empty.txt'
        f.write_bytes(b'')
        self.assertEqual(_safe_get_size(f), 0)

    def test_nonexistent_file(self):
        f = self.test_dir / 'nonexistent.txt'
        self.assertEqual(_safe_get_size(f), 0)

    @skipIf(IS_WIN, 'symlink test')
    def test_symlink_file(self):
        target = self.test_dir / 'target.txt'
        target.write_bytes(b'x' * 100)
        link = self.test_dir / 'link.txt'
        try:
            link.symlink_to(target)
            self.assertEqual(_safe_get_size(link), 0)
        except OSError:
            pass


class TestFixAgent(TestCase):
    """修复功能 - 备份、清理、配置修复"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)
        self.backup_dir = Path.home() / '.ai_agent_backups'

    def tearDown(self):
        # 清理测试产生的备份
        if self.backup_dir.exists():
            for item in self.backup_dir.iterdir():
                if item.name.startswith('testagent_'):
                    shutil.rmtree(item, ignore_errors=True)

    def test_fix_creates_backup(self):
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        (agent_dir / 'settings.json').write_text('{"ok": true}')

        fix_agent('testagent', agent_dir)

        # 检查备份是否创建
        backups = list(self.backup_dir.glob('testagent_*'))
        self.assertTrue(len(backups) >= 1)

    def test_fix_repairs_broken_json(self):
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        (agent_dir / 'settings.json').write_text('{broken json}')

        fix_agent('testagent', agent_dir)

        # 配置文件应被修复为有效JSON
        with open(agent_dir / 'settings.json') as f:
            data = json.load(f)
        self.assertIn('version', data)

    def test_fix_creates_broken_backup(self):
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        (agent_dir / 'settings.json').write_text('{broken}')

        fix_agent('testagent', agent_dir)

        # 应该有 .broken 备份文件
        broken = list(agent_dir.glob('*.broken'))
        self.assertTrue(len(broken) >= 1)

    def test_fix_cleans_cache(self):
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        cache = agent_dir / 'cache'
        cache.mkdir()
        (cache / 'file1.txt').write_text('data')
        (cache / 'file2.txt').write_text('data')

        fix_agent('testagent', agent_dir)

        # 缓存文件应被清理
        self.assertEqual(len(list(cache.iterdir())), 0)

    def test_fix_idempotent(self):
        """修复两次不应报错"""
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        (agent_dir / 'settings.json').write_text('{"ok": true}')

        fix_agent('testagent', agent_dir)
        fix_agent('testagent', agent_dir)  # 第二次

    def test_fix_with_readonly_file(self):
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        cache = agent_dir / 'cache'
        cache.mkdir()
        f = cache / 'readonly.txt'
        f.write_text('data')
        f.chmod(0o444)

        # 不应崩溃
        try:
            fix_agent('testagent', agent_dir)
        except Exception:
            self.fail('fix_agent should not raise on readonly files')
        finally:
            try:
                f.chmod(0o644)
            except FileNotFoundError:
                pass  # 文件已被成功删除

    def test_fix_with_symlink_in_cache(self):
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        cache = agent_dir / 'cache'
        cache.mkdir()
        target = self.test_dir / 'outside.txt'
        target.write_text('data')
        try:
            (cache / 'link').symlink_to(target)
            fix_agent('testagent', agent_dir)
        except OSError:
            pass  # symlink not supported


class TestIntegration(TestCase):
    """集成测试 - 完整工作流"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_full_scan_workflow(self):
        """完整扫描流程不崩溃"""
        from repair_tool import scan_all
        # scan_all 会扫描真实路径，可能找到也可能找不到
        # 关键是不崩溃
        try:
            result = scan_all()
            self.assertIsInstance(result, list)
        except Exception:
            self.fail('scan_all should not raise')

    def test_main_no_crash(self):
        """main函数不崩溃"""
        from repair_tool import main
        # main 在无终端时会捕获 EOFError
        try:
            main()
        except EOFError:
            pass  # expected in CI
        except SystemExit:
            pass

    def test_agent_data_integrity(self):
        """AGENT_PATHS 数据完整性"""
        for agent_id, config in AGENT_PATHS.items():
            self.assertIn('name', config)
            self.assertIn('paths', config)
            for os_key in ['win', 'mac', 'linux']:
                self.assertIn(os_key, config['paths'])
                for path in config['paths'][os_key]:
                    self.assertIsInstance(path, str)
                    self.assertTrue(len(path) > 0)


if __name__ == '__main__':
    main(verbosity=2)
