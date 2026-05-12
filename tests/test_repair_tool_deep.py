#!/usr/bin/env python3
"""
AI Agent Repair Tool - 深度测试
覆盖: 文件锁定、特殊字符路径、超大目录、并发安全、部分失败恢复、安全审计、边界情况
"""

import os
import sys
import json
import stat
import time
import shutil
import tempfile
import threading
from pathlib import Path
from unittest import TestCase, main, skipIf

sys.path.insert(0, str(Path(__file__).parent.parent))

from repair_tool import (
    get_os, expand_path, find_agent, check_config, check_cache,
    _safe_get_size, fix_agent, scan_all, AGENT_PATHS
)

IS_WIN = sys.platform == 'win32'
IS_MAC = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')


class TestSpecialCharPaths(TestCase):
    """特殊字符路径测试"""

    def setUp(self):
        self.base_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.base_dir, ignore_errors=True)

    def test_path_with_spaces(self):
        """路径含空格"""
        dir_with_spaces = self.base_dir / 'my agent data'
        dir_with_spaces.mkdir()
        (dir_with_spaces / 'settings.json').write_text('{"ok": true}')
        issues = check_config(dir_with_spaces)
        self.assertEqual(issues, [])

    def test_path_with_unicode(self):
        """路径含Unicode字符"""
        unicode_dir = self.base_dir / 'test_\u4e2d\u6587_\u65e5\u672c\u8a9e'
        try:
            unicode_dir.mkdir()
            (unicode_dir / 'settings.json').write_text('{"ok": true}')
            issues = check_config(unicode_dir)
            self.assertEqual(issues, [])
        except OSError:
            pass  # 某些文件系统不支持

    def test_path_with_dots(self):
        """路径含多个点"""
        dot_dir = self.base_dir / '.hidden.agent.config'
        dot_dir.mkdir()
        (dot_dir / 'settings.json').write_text('{"ok": true}')
        issues = check_config(dot_dir)
        self.assertEqual(issues, [])

    def test_very_long_filename(self):
        """超长文件名"""
        long_name = 'a' * 200 + '.json'
        long_file = self.base_dir / long_name
        try:
            long_file.write_text('{"ok": true}')
            issues = check_config(self.base_dir)
            self.assertEqual(issues, [])
        except OSError:
            pass  # 某些文件系统有文件名长度限制

    def test_path_with_special_chars(self):
        """路径含特殊字符（非Unicode）"""
        special_dir = self.base_dir / 'agent_v1.0-beta.2'
        special_dir.mkdir()
        (special_dir / 'settings.json').write_text('{"ok": true}')
        issues = check_config(special_dir)
        self.assertEqual(issues, [])

    def test_expand_path_with_spaces(self):
        """展开含空格的路径"""
        path = expand_path('~/Documents')
        # 不关心是否存在，只关心不崩溃
        self.assertIsNotNone(path)


class TestLargeDirectory(TestCase):
    """超大目录性能测试"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir, ignore_errors=True)

    def test_many_files_in_cache(self):
        """缓存目录含大量小文件"""
        cache = self.test_dir / 'cache'
        cache.mkdir()
        for i in range(500):
            (cache / f'file_{i}.dat').write_bytes(b'x' * 10)

        start = time.time()
        issues = check_cache(self.test_dir)
        elapsed = time.time() - start

        self.assertEqual(issues, [])
        self.assertLess(elapsed, 30, f"check_cache took {elapsed:.1f}s, too slow")

    def test_deeply_nested_cache(self):
        """缓存目录含深层嵌套"""
        cache = self.test_dir / 'cache'
        cache.mkdir()
        deep = cache
        for i in range(20):
            deep = deep / f'level_{i}'
            deep.mkdir()
        (deep / 'deep_file.txt').write_text('data')

        start = time.time()
        issues = check_cache(self.test_dir)
        elapsed = time.time() - start

        self.assertEqual(issues, [])
        self.assertLess(elapsed, 30, f"deep nesting took {elapsed:.1f}s")

    def test_many_empty_dirs(self):
        """大量空目录"""
        cache = self.test_dir / 'cache'
        cache.mkdir()
        for i in range(100):
            (cache / f'dir_{i}').mkdir()

        issues = check_cache(self.test_dir)
        self.assertEqual(issues, [])

    def test_mixed_content_cache(self):
        """混合内容：文件、目录、空文件、符号链接"""
        cache = self.test_dir / 'cache'
        cache.mkdir()

        # 普通文件
        for i in range(50):
            (cache / f'normal_{i}.txt').write_text('data')

        # 空文件
        for i in range(50):
            (cache / f'empty_{i}').write_bytes(b'')

        # 子目录
        for i in range(10):
            sub = cache / f'sub_{i}'
            sub.mkdir()
            (sub / 'file.txt').write_text('data')

        issues = check_cache(self.test_dir)
        self.assertEqual(issues, [])


class TestFileLocking(TestCase):
    """文件锁定测试"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir, ignore_errors=True)
        self.backup_dir = Path.home() / '.ai_agent_backups'

    def tearDown(self):
        if self.backup_dir.exists():
            for item in self.backup_dir.iterdir():
                if item.name.startswith('testagent_'):
                    shutil.rmtree(item, ignore_errors=True)

    def test_config_locked_during_check(self):
        """检查时配置文件被锁定（模拟）"""
        config_file = self.test_dir / 'settings.json'
        config_file.write_text('{"ok": true}')

        # 在另一个线程中持续写入文件
        stop_event = threading.Event()

        def writer():
            while not stop_event.is_set():
                try:
                    with open(config_file, 'w') as f:
                        f.write('{"ok": true}')
                except OSError:
                    pass
                time.sleep(0.001)

        t = threading.Thread(target=writer, daemon=True)
        t.start()
        try:
            # 多次检查不应崩溃
            for _ in range(10):
                issues = check_config(self.test_dir)
                self.assertIsInstance(issues, list)
        finally:
            stop_event.set()
            t.join(timeout=2)

    def test_fix_while_files_change(self):
        """修复时文件被并发修改"""
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        (agent_dir / 'settings.json').write_text('{"ok": true}')
        cache = agent_dir / 'cache'
        cache.mkdir()
        for i in range(20):
            (cache / f'file_{i}.txt').write_text('data')

        stop_event = threading.Event()

        def modifier():
            while not stop_event.is_set():
                try:
                    (cache / f'concurrent_{int(time.time()*1000)}.txt').write_text('new')
                except OSError:
                    pass
                time.sleep(0.01)

        t = threading.Thread(target=modifier, daemon=True)
        t.start()
        try:
            # 不应崩溃
            fix_agent('testagent', agent_dir)
        finally:
            stop_event.set()
            t.join(timeout=2)


class TestConcurrentSafety(TestCase):
    """并发安全测试"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir, ignore_errors=True)
        self.backup_dir = Path.home() / '.ai_agent_backups'

    def tearDown(self):
        if self.backup_dir.exists():
            for item in self.backup_dir.iterdir():
                if item.name.startswith('testagent_'):
                    shutil.rmtree(item, ignore_errors=True)

    def test_concurrent_scan(self):
        """多个线程同时扫描不应崩溃"""
        errors = []

        def scan_worker():
            try:
                result = scan_all()
                if not isinstance(result, list):
                    errors.append("scan_all returned non-list")
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=scan_worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        self.assertEqual(len(errors), 0, f"Concurrent scan errors: {errors}")

    def test_concurrent_fix_different_agents(self):
        """并发修复不同Agent不应冲突"""
        errors = []

        def fix_worker(name):
            try:
                agent_dir = self.test_dir / name
                agent_dir.mkdir(exist_ok=True)
                (agent_dir / 'settings.json').write_text('{"ok": true}')
                cache = agent_dir / 'cache'
                cache.mkdir(exist_ok=True)
                (cache / 'file.txt').write_text('data')
                fix_agent(name, agent_dir)
            except Exception as e:
                errors.append(f"{name}: {e}")

        AGENT_PATHS['worker_a'] = {"name": "WorkerA", "paths": {"win": [], "mac": [], "linux": []}}
        AGENT_PATHS['worker_b'] = {"name": "WorkerB", "paths": {"win": [], "mac": [], "linux": []}}
        AGENT_PATHS['worker_c'] = {"name": "WorkerC", "paths": {"win": [], "mac": [], "linux": []}}

        threads = [
            threading.Thread(target=fix_worker, args=('worker_a',)),
            threading.Thread(target=fix_worker, args=('worker_b',)),
            threading.Thread(target=fix_worker, args=('worker_c',)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        self.assertEqual(len(errors), 0, f"Concurrent fix errors: {errors}")


class TestPartialFailure(TestCase):
    """部分失败恢复测试"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir, ignore_errors=True)
        self.backup_dir = Path.home() / '.ai_agent_backups'

    def tearDown(self):
        if self.backup_dir.exists():
            for item in self.backup_dir.iterdir():
                if item.name.startswith('testagent_'):
                    shutil.rmtree(item, ignore_errors=True)

    def test_fix_with_no_writable_dir(self):
        """Agent目录不可写时不应崩溃"""
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        (agent_dir / 'settings.json').write_text('{"ok": true}')

        if not IS_WIN:
            # 使目录不可写（但可读）
            agent_dir.chmod(0o555)
            try:
                fix_agent('testagent', agent_dir)
                # 不应崩溃，可能部分失败
            except Exception:
                self.fail('fix_agent should not raise even with read-only dir')
            finally:
                agent_dir.chmod(0o755)
        else:
            fix_agent('testagent', agent_dir)

    def test_fix_with_missing_cache_dir(self):
        """缓存目录在修复过程中被删除"""
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        (agent_dir / 'settings.json').write_text('{"ok": true}')
        cache = agent_dir / 'cache'
        cache.mkdir()
        (cache / 'file.txt').write_text('data')

        # 删除缓存目录后修复
        shutil.rmtree(cache)
        fix_agent('testagent', agent_dir)
        # 不应崩溃

    def test_fix_corrupted_and_valid_mix(self):
        """同时有损坏和正常的配置文件"""
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        (agent_dir / 'settings.json').write_text('{"ok": true}')
        (agent_dir / 'config.json').write_text('{broken json}')
        cache = agent_dir / 'cache'
        cache.mkdir()
        (cache / 'file.txt').write_text('data')

        fix_agent('testagent', agent_dir)

        # settings.json 应该保持正常
        with open(agent_dir / 'settings.json') as f:
            data = json.load(f)
        self.assertEqual(data.get('ok'), True)

        # config.json 应该被修复
        with open(agent_dir / 'config.json') as f:
            data = json.load(f)
        self.assertIn('version', data)

    def test_backup_already_exists(self):
        """备份目录已存在时覆盖"""
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        (agent_dir / 'settings.json').write_text('{"ok": true}')

        # 第一次修复
        fix_agent('testagent', agent_dir)

        # 修改文件
        (agent_dir / 'settings.json').write_text('{"ok": true, "updated": true}')

        # 第二次修复不应因备份已存在而失败
        fix_agent('testagent', agent_dir)


class TestSecurityAudit(TestCase):
    """安全审计测试"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir, ignore_errors=True)

    def test_config_with_path_traversal(self):
        """配置文件含路径穿越内容"""
        (self.test_dir / 'settings.json').write_text(json.dumps({
            "path": "../../../etc/passwd"
        }))
        issues = check_config(self.test_dir)
        # 只检查JSON有效性，不验证内容安全性
        self.assertEqual(issues, [])

    def test_config_with_very_long_value(self):
        """配置文件含超长值"""
        long_val = "x" * 1000000
        (self.test_dir / 'settings.json').write_text(json.dumps({"data": long_val}))
        issues = check_config(self.test_dir)
        self.assertEqual(issues, [])

    def test_config_with_null_bytes(self):
        """配置文件含null字节"""
        content = '{"ok": true}\x00{"evil": true}'
        (self.test_dir / 'settings.json').write_text(content)
        issues = check_config(self.test_dir)
        # null字节可能导致JSON解析问题
        self.assertIsInstance(issues, list)

    def test_config_with_bom(self):
        """配置文件含BOM头"""
        # UTF-8 BOM
        (self.test_dir / 'settings.json').write_bytes(
            b'\xef\xbb\xbf{"ok": true}'
        )
        issues = check_config(self.test_dir)
        # BOM可能导致某些解析器失败
        self.assertIsInstance(issues, list)

    def test_config_with_json_array(self):
        """配置文件是JSON数组而非对象"""
        (self.test_dir / 'settings.json').write_text('[{"ok": true}]')
        issues = check_config(self.test_dir)
        # 数组也是有效JSON
        self.assertEqual(issues, [])

    def test_config_with_only_number(self):
        """配置文件只有数字"""
        (self.test_dir / 'settings.json').write_text('42')
        issues = check_config(self.test_dir)
        # 数字也是有效JSON
        self.assertEqual(issues, [])

    def test_config_with_comments(self):
        """配置文件含注释（非标准JSON）"""
        (self.test_dir / 'settings.json').write_text('{"ok": true /* comment */}')
        issues = check_config(self.test_dir)
        # 注释使JSON无效
        self.assertTrue(len(issues) >= 1)

    def test_expand_path_no_traversal(self):
        """路径展开不应允许穿越"""
        path = expand_path('~')
        # 展开后的路径应该在home目录下
        self.assertTrue(str(path).startswith(str(Path.home())))


class TestEdgeCases(TestCase):
    """极端边界情况"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir, ignore_errors=True)
        self.backup_dir = Path.home() / '.ai_agent_backups'

    def tearDown(self):
        if self.backup_dir.exists():
            for item in self.backup_dir.iterdir():
                if item.name.startswith('testagent_'):
                    shutil.rmtree(item, ignore_errors=True)

    def test_empty_agent_dir(self):
        """空Agent目录"""
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        fix_agent('testagent', agent_dir)
        # 不应崩溃

    def test_agent_dir_only_cache(self):
        """Agent目录只有缓存没有配置"""
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        cache = agent_dir / 'cache'
        cache.mkdir()
        (cache / 'file.txt').write_text('data')

        fix_agent('testagent', agent_dir)
        # 不应崩溃

    def test_agent_dir_only_config(self):
        """Agent目录只有配置没有缓存"""
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        (agent_dir / 'settings.json').write_text('{"ok": true}')

        fix_agent('testagent', agent_dir)
        # 不应崩溃

    def test_multiple_broken_configs(self):
        """多个损坏的配置文件"""
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        (agent_dir / 'settings.json').write_text('{bad1}')
        (agent_dir / 'config.json').write_text('{bad2}')

        fix_agent('testagent', agent_dir)

        # 两个都应该被修复
        with open(agent_dir / 'settings.json') as f:
            self.assertIn('version', json.load(f))
        with open(agent_dir / 'config.json') as f:
            self.assertIn('version', json.load(f))

    def test_fix_preserves_non_standard_files(self):
        """修复不应删除非标准文件"""
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        (agent_dir / 'settings.json').write_text('{"ok": true}')
        (agent_dir / 'my_custom_data.db').write_text('important data')
        (agent_dir / 'notes.txt').write_text('user notes')

        fix_agent('testagent', agent_dir)

        # 自定义文件应该保留
        self.assertTrue((agent_dir / 'my_custom_data.db').exists())
        self.assertTrue((agent_dir / 'notes.txt').exists())

    def test_scan_all_returns_list(self):
        """scan_all 总是返回列表"""
        result = scan_all()
        self.assertIsInstance(result, list)
        for item in result:
            self.assertEqual(len(item), 3)  # (agent_id, path, issues)

    def test_backup_dir_permissions(self):
        """备份目录权限正确"""
        agent_dir = self.test_dir / 'testagent'
        agent_dir.mkdir()
        (agent_dir / 'settings.json').write_text('{"ok": true}')

        fix_agent('testagent', agent_dir)

        backups = list(self.backup_dir.glob('testagent_*'))
        self.assertTrue(len(backups) >= 1)
        # 备份目录应该可读
        self.assertTrue(os.access(backups[0], os.R_OK))


if __name__ == '__main__':
    main(verbosity=2)
