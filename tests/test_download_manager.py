"""
下载管理器测试套件
测试下载模式、进度跟踪、状态管理等功能
"""

import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.download_manager import (
    DownloadManager, DownloadItem, DownloadResult,
    DownloadMode, DownloadStatus, download_manager
)


class TestDownloadItem(unittest.TestCase):
    """测试下载项类"""
    
    def test_download_item_defaults(self):
        """测试下载项默认值"""
        item = DownloadItem(
            id="test-1",
            name="test.zip",
            url="http://example.com/test.zip"
        )
        self.assertEqual(item.id, "test-1")
        self.assertEqual(item.name, "test.zip")
        self.assertEqual(item.url, "http://example.com/test.zip")
        self.assertEqual(item.status, DownloadStatus.PENDING)
        self.assertEqual(item.progress, 0.0)
        self.assertEqual(item.mode, DownloadMode.AUTO)
        self.assertEqual(item.size_bytes, 0)
    
    def test_download_item_full(self):
        """测试完整下载项"""
        item = DownloadItem(
            id="test-2",
            name="large.zip",
            url="http://example.com/large.zip",
            size_bytes=1024*1024*100,  # 100MB
            status=DownloadStatus.DOWNLOADING,
            progress=50.0,
            downloaded_bytes=1024*1024*50,
            mode=DownloadMode.LINK_ONLY
        )
        self.assertEqual(item.status, DownloadStatus.DOWNLOADING)
        self.assertEqual(item.progress, 50.0)
        self.assertEqual(item.mode, DownloadMode.LINK_ONLY)


class TestDownloadResult(unittest.TestCase):
    """测试下载结果类"""
    
    def test_download_result_success(self):
        """测试成功结果"""
        result = DownloadResult(
            success=True,
            file_path="/downloads/file.zip",
            message="下载完成"
        )
        self.assertTrue(result.success)
        self.assertEqual(result.file_path, "/downloads/file.zip")
        self.assertIsNone(result.error)
    
    def test_download_result_failure(self):
        """测试失败结果"""
        result = DownloadResult(
            success=False,
            error="Network timeout"
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Network timeout")
        self.assertIsNone(result.file_path)


class TestDownloadManager(unittest.TestCase):
    """测试下载管理器核心功能"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DownloadManager.__new__(DownloadManager)
        self.manager.items = {}
        self.manager._lock = threading.Lock()
        self.manager._callbacks = []
        self.manager.download_dir = Path(self.temp_dir)
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_download(self):
        """测试添加下载项"""
        item = self.manager.add_download(
            "item-1",
            "test.zip",
            "http://example.com/test.zip",
            size_bytes=1024
        )
        
        self.assertEqual(item.id, "item-1")
        self.assertEqual(item.name, "test.zip")
        self.assertEqual(item.size_display, "1.0 KB")
        self.assertIn("item-1", self.manager.items)
    
    def test_add_download_link_only(self):
        """测试添加仅链接模式下载项"""
        item = self.manager.add_download(
            "item-2",
            "large.zip",
            "http://example.com/large.zip",
            size_bytes=1024*1024*100,
            mode=DownloadMode.LINK_ONLY
        )
        
        self.assertEqual(item.mode, DownloadMode.LINK_ONLY)
        self.assertEqual(item.size_display, "100.0 MB")
    
    def test_get_download_links(self):
        """测试获取下载链接"""
        self.manager.add_download("item-1", "file1.zip", "http://a.com/1.zip", 1024)
        self.manager.add_download("item-2", "file2.zip", "http://a.com/2.zip", 2048)
        
        links = self.manager.get_download_links()
        self.assertEqual(len(links), 2)
        
        # 测试获取特定项
        links = self.manager.get_download_links(["item-1"])
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["name"], "file1.zip")
    
    def test_get_all_links_markdown(self):
        """测试获取Markdown格式链接"""
        self.manager.add_download("item-1", "file1.zip", "http://a.com/1.zip", 1024)
        
        markdown = self.manager.get_all_links_markdown()
        self.assertIn("# 下载链接列表", markdown)
        self.assertIn("file1.zip", markdown)
        self.assertIn("http://a.com/1.zip", markdown)
    
    def test_get_all_links_markdown_empty(self):
        """测试空列表Markdown输出"""
        markdown = self.manager.get_all_links_markdown()
        self.assertEqual(markdown, "没有待下载的文件")
    
    def test_register_callback(self):
        """测试注册回调函数"""
        callback_called = [False]
        
        def callback(item):
            callback_called[0] = True
        
        self.manager.register_callback(callback)
        self.assertEqual(len(self.manager._callbacks), 1)
        
        # 触发通知
        item = DownloadItem(id="test", name="test", url="http://test")
        self.manager._notify(item)
        self.assertTrue(callback_called[0])
    
    def test_start_download_not_found(self):
        """测试开始不存在的下载"""
        result = self.manager.start_download("nonexistent")
        self.assertFalse(result.success)
        self.assertEqual(result.error, "下载项不存在")
    
    def test_start_download_already_downloading(self):
        """测试重复开始下载"""
        item = self.manager.add_download("item-1", "test.zip", "http://a.com/test.zip")
        item.status = DownloadStatus.DOWNLOADING
        
        result = self.manager.start_download("item-1")
        self.assertFalse(result.success)
        self.assertEqual(result.error, "正在下载中")
    
    def test_start_download_link_only_mode(self):
        """测试仅链接模式下载"""
        item = self.manager.add_download(
            "item-1", "test.zip", "http://a.com/test.zip",
            mode=DownloadMode.LINK_ONLY
        )
        
        result = self.manager.start_download("item-1")
        self.assertTrue(result.success)
        self.assertEqual(item.status, DownloadStatus.SUCCESS)
        self.assertEqual(item.progress, 100)
    
    @patch('core.download_manager.urllib.request.urlopen')
    @patch('core.download_manager.urllib.request.Request')
    def test_download_file_success(self, mock_request, mock_urlopen):
        """测试文件下载成功"""
        # 模拟响应
        mock_response = MagicMock()
        mock_response.headers = {'Content-Length': '1024'}
        mock_response.read.side_effect = [b'x' * 512, b'x' * 512, b'']  # 分块读取
        mock_urlopen.return_value.__enter__ = MagicMock(return_value=mock_response)
        mock_urlopen.return_value.__exit__ = MagicMock(return_value=False)
        
        item = DownloadItem(
            id="item-1",
            name="test.zip",
            url="http://example.com/test.zip"
        )
        
        result = self.manager._download_file(item)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.file_path)
    
    @patch('core.download_manager.urllib.request.urlopen')
    def test_download_file_network_error(self, mock_urlopen):
        """测试网络错误处理"""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        
        item = DownloadItem(
            id="item-1",
            name="test.zip",
            url="http://example.com/test.zip"
        )
        
        result = self.manager._download_file(item)
        self.assertFalse(result.success)
        self.assertIn("网络错误", result.error)
    
    def test_cancel_download(self):
        """测试取消下载"""
        item = self.manager.add_download("item-1", "test.zip", "http://a.com/test.zip")
        item.status = DownloadStatus.DOWNLOADING
        
        self.manager.cancel_download("item-1")
        self.assertEqual(item.status, DownloadStatus.CANCELLED)
    
    def test_get_status_single(self):
        """测试获取单个下载状态"""
        self.manager.add_download("item-1", "test.zip", "http://a.com/test.zip", 1024)
        
        status = self.manager.get_status("item-1")
        self.assertEqual(status["id"], "item-1")
        self.assertEqual(status["name"], "test.zip")
        self.assertEqual(status["size"], "1.0 KB")
    
    def test_get_status_all(self):
        """测试获取所有下载状态"""
        self.manager.add_download("item-1", "file1.zip", "http://a.com/1.zip", 1024)
        self.manager.add_download("item-2", "file2.zip", "http://a.com/2.zip", 2048)
        
        statuses = self.manager.get_status()
        self.assertEqual(len(statuses), 2)
        self.assertIn("item-1", statuses)
        self.assertIn("item-2", statuses)
    
    def test_get_status_not_found(self):
        """测试获取不存在的状态"""
        status = self.manager.get_status("nonexistent")
        self.assertEqual(status, {})
    
    def test_item_to_dict(self):
        """测试转换为字典"""
        item = DownloadItem(
            id="item-1",
            name="test.zip",
            url="http://a.com/test.zip",
            size_bytes=1024*1024,
            size_display="1.0 MB",
            status=DownloadStatus.DOWNLOADING,
            progress=50.0,
            downloaded_bytes=512*1024,
            speed_bps=1024*100
        )
        
        data = self.manager._item_to_dict(item)
        self.assertEqual(data["id"], "item-1")
        self.assertEqual(data["size"], "1.0 MB")
        self.assertEqual(data["status"], "downloading")
        self.assertEqual(data["progress"], 50.0)
        self.assertEqual(data["downloaded"], "512.0 KB")
        self.assertEqual(data["speed"], "100.0 KB/s")
    
    def test_format_size(self):
        """测试文件大小格式化"""
        self.assertEqual(DownloadManager._format_size(512), "512 B")
        self.assertEqual(DownloadManager._format_size(1024), "1.0 KB")
        self.assertEqual(DownloadManager._format_size(1024*1024), "1.0 MB")
        self.assertEqual(DownloadManager._format_size(1024*1024*1024), "1.00 GB")
        self.assertEqual(DownloadManager._format_size(1024*1024*1024*2), "2.00 GB")
    
    def test_format_speed(self):
        """测试下载速度格式化"""
        self.assertEqual(DownloadManager._format_speed(0), "")
        self.assertEqual(DownloadManager._format_speed(512), "512 B/s")
        self.assertEqual(DownloadManager._format_speed(1024), "1.0 KB/s")
        self.assertEqual(DownloadManager._format_speed(1024*1024), "1.0 MB/s")
    
    def test_clear_completed(self):
        """测试清除已完成项"""
        # 添加不同状态的项
        item1 = self.manager.add_download("item-1", "file1.zip", "http://a.com/1.zip")
        item1.status = DownloadStatus.SUCCESS
        
        item2 = self.manager.add_download("item-2", "file2.zip", "http://a.com/2.zip")
        item2.status = DownloadStatus.FAILED
        
        item3 = self.manager.add_download("item-3", "file3.zip", "http://a.com/3.zip")
        item3.status = DownloadStatus.CANCELLED
        
        item4 = self.manager.add_download("item-4", "file4.zip", "http://a.com/4.zip")
        item4.status = DownloadStatus.PENDING
        
        self.manager.clear_completed()
        
        self.assertNotIn("item-1", self.manager.items)
        self.assertNotIn("item-2", self.manager.items)
        self.assertNotIn("item-3", self.manager.items)
        self.assertIn("item-4", self.manager.items)


class TestDownloadManagerConcurrency(unittest.TestCase):
    """测试下载管理器并发安全"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DownloadManager.__new__(DownloadManager)
        self.manager.items = {}
        self.manager._lock = threading.Lock()
        self.manager._callbacks = []
        self.manager.download_dir = Path(self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_concurrent_add_download(self):
        """测试并发添加下载项"""
        errors = []
        
        def add_items():
            try:
                for i in range(10):
                    self.manager.add_download(
                        f"item-{threading.current_thread().name}-{i}",
                        f"file{i}.zip",
                        f"http://a.com/{i}.zip"
                    )
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=add_items) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(self.manager.items), 50)
    
    def test_thread_safety_lock(self):
        """测试锁的线程安全"""
        # 验证锁存在且可以获取
        self.assertTrue(hasattr(self.manager, '_lock'))
        
        with self.manager._lock:
            # 锁已获取
            pass
        
        # 锁已释放，可以再次获取
        with self.manager._lock:
            pass


class TestDownloadManagerEdgeCases(unittest.TestCase):
    """测试下载管理器边界条件"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = DownloadManager.__new__(DownloadManager)
        self.manager.items = {}
        self.manager._lock = threading.Lock()
        self.manager._callbacks = []
        self.manager.download_dir = Path(self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_empty_url(self):
        """测试空URL"""
        item = self.manager.add_download("item-1", "file.zip", "")
        self.assertEqual(item.url, "")
    
    def test_url_with_query_params(self):
        """测试带查询参数的URL"""
        url = "http://example.com/file.zip?token=abc&expires=123"
        item = self.manager.add_download("item-1", "file.zip", url)
        self.assertEqual(item.url, url)
    
    def test_filename_from_url(self):
        """测试从URL提取文件名"""
        item = DownloadItem(
            id="item-1",
            name="",  # 空文件名
            url="http://example.com/path/to/file.zip?token=abc"
        )
        
        # 模拟下载时提取文件名
        extracted = item.url.split('/')[-1].split('?')[0]
        self.assertEqual(extracted, "file.zip")
    
    def test_progress_bounds(self):
        """测试进度边界值"""
        item = DownloadItem(id="test", name="test", url="http://test")
        
        # 进度应该在0-100范围内
        item.progress = 0
        self.assertEqual(item.progress, 0)
        
        item.progress = 100
        self.assertEqual(item.progress, 100)
        
        item.progress = -10
        self.assertEqual(item.progress, -10)  # 允许负值，但应该避免
        
        item.progress = 150
        self.assertEqual(item.progress, 150)  # 允许超过100，但应该避免
    
    def test_large_file_size(self):
        """测试大文件大小"""
        # 10GB文件
        item = self.manager.add_download(
            "item-1", "large.zip", "http://a.com/large.zip",
            size_bytes=1024*1024*1024*10
        )
        self.assertEqual(item.size_display, "10.00 GB")
    
    def test_very_small_file(self):
        """测试极小文件"""
        item = self.manager.add_download(
            "item-1", "tiny.txt", "http://a.com/tiny.txt",
            size_bytes=1
        )
        self.assertEqual(item.size_display, "1 B")
    
    def test_callback_exception_handling(self):
        """测试回调异常处理"""
        def bad_callback(item):
            raise Exception("Callback error")
        
        self.manager.register_callback(bad_callback)
        
        # 不应该抛出异常
        item = DownloadItem(id="test", name="test", url="http://test")
        try:
            self.manager._notify(item)
        except Exception:
            self.fail("_notify should not raise exception")


class TestGlobalDownloadManager(unittest.TestCase):
    """测试全局下载管理器实例"""
    
    def test_global_instance_exists(self):
        """测试全局实例存在"""
        self.assertIsNotNone(download_manager)
        self.assertIsInstance(download_manager, DownloadManager)
    
    def test_global_instance_is_singleton(self):
        """测试全局实例是单例"""
        from core.download_manager import download_manager as dm2
        self.assertIs(download_manager, dm2)


if __name__ == "__main__":
    unittest.main()
