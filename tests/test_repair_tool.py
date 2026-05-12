#!/usr/bin/env python3
"""
AI Agent Repair Tool 测试
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest import TestCase, main

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from repair_tool import (
    get_os, expand_path, find_agent, check_config, check_cache,
    AGENT_PATHS
)


class TestBasicFunctions(TestCase):
    """测试基础函数"""

    def test_get_os(self):
        """测试操作系统检测"""
        result = get_os()
        self.assertIn(result, ['win', 'mac', 'linux'])

    def test_expand_path_home(self):
        """测试路径展开 - home目录"""
        path = expand_path('~')
        self.assertTrue(Path(path).exists())

    def test_expand_path_relative(self):
        """测试路径展开 - 相对路径"""
        path = expand_path('.')
        self.assertEqual(Path(path).resolve(), Path.cwd())


class TestAgentDetection(TestCase):
    """测试Agent检测功能"""

    def setUp(self):
        """创建临时测试目录"""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_find_agent_not_exists(self):
        """测试查找不存在的Agent"""
        result = find_agent('nonexistent_agent')
        self.assertIsNone(result)


class TestConfigCheck(TestCase):
    """测试配置检查功能"""

    def setUp(self):
        """创建临时测试目录"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_check_config_no_files(self):
        """测试配置检查 - 无配置文件"""
        issues = check_config(self.test_dir)
        self.assertEqual(len(issues), 0)

    def test_check_config_valid_json(self):
        """测试配置检查 - 有效JSON"""
        config_file = self.test_dir / 'settings.json'
        config_file.write_text('{"version": "1.0.0"}')
        
        issues = check_config(self.test_dir)
        self.assertEqual(len(issues), 0)

    def test_check_config_invalid_json(self):
        """测试配置检查 - 无效JSON"""
        config_file = self.test_dir / 'settings.json'
        config_file.write_text('{"version": "1.0.0", invalid}')
        
        issues = check_config(self.test_dir)
        self.assertEqual(len(issues), 1)
        self.assertIn('损坏', issues[0])


class TestCacheCheck(TestCase):
    """测试缓存检查功能"""

    def setUp(self):
        """创建临时测试目录"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_check_cache_no_cache(self):
        """测试缓存检查 - 无缓存目录"""
        issues = check_cache(self.test_dir)
        self.assertEqual(len(issues), 0)

    def test_check_cache_small_cache(self):
        """测试缓存检查 - 小缓存（<500MB）"""
        cache_dir = self.test_dir / 'cache'
        cache_dir.mkdir()
        
        # 创建一个小文件（1KB）
        test_file = cache_dir / 'test.cache'
        test_file.write_bytes(b'x' * 1024)
        
        issues = check_cache(self.test_dir)
        self.assertEqual(len(issues), 0)


class TestIntegration(TestCase):
    """集成测试"""

    def setUp(self):
        """创建完整的测试环境"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir)

    def test_full_workflow(self):
        """测试完整工作流程"""
        agent_dir = self.test_dir / 'test_agent'
        agent_dir.mkdir()
        
        # 创建配置文件
        config_file = agent_dir / 'settings.json'
        config_file.write_text(json.dumps({
            "version": "1.0.0",
            "settings": {"auto_update": True}
        }))
        
        # 创建缓存目录
        cache_dir = agent_dir / 'cache'
        cache_dir.mkdir()
        
        # 测试配置检查
        config_issues = check_config(agent_dir)
        self.assertEqual(len(config_issues), 0)
        
        # 测试缓存检查
        cache_issues = check_cache(agent_dir)
        self.assertEqual(len(cache_issues), 0)


if __name__ == '__main__':
    main(verbosity=2)
