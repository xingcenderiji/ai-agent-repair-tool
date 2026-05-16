"""
下载管理器模块
支持自动下载和获取链接两种模式，让用户选择最快的下载方式
"""

import os
import json
import time
import threading
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Tuple
from enum import Enum


class DownloadMode(Enum):
    AUTO = "auto"        # 自动下载
    LINK_ONLY = "link"  # 仅获取链接


class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadItem:
    """下载项"""
    id: str
    name: str
    url: str
    size_bytes: int = 0
    size_display: str = ""
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0  # 0-100
    downloaded_bytes: int = 0
    speed_bps: int = 0  # bytes per second
    local_path: Optional[str] = None
    error: Optional[str] = None
    checksum: Optional[str] = None  # MD5/SHA256
    mode: DownloadMode = DownloadMode.AUTO


@dataclass
class DownloadResult:
    """下载结果"""
    success: bool
    file_path: Optional[str] = None
    error: Optional[str] = None
    message: str = ""


class DownloadManager:
    """下载管理器"""
    
    def __init__(self):
        self.items: Dict[str, DownloadItem] = {}
        self._lock = threading.Lock()
        self._callbacks: List[Callable] = []
        
        # 下载目录
        self.download_dir = Path.home() / ".ai_agent_repair" / "downloads"
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def register_callback(self, callback: Callable):
        """注册状态更新回调"""
        self._callbacks.append(callback)
    
    def _notify(self, item: DownloadItem):
        """通知状态更新"""
        for cb in self._callbacks:
            try:
                cb(item)
            except:
                pass
    
    def add_download(self, item_id: str, name: str, url: str, 
                    size_bytes: int = 0, mode: DownloadMode = DownloadMode.AUTO) -> DownloadItem:
        """添加下载项"""
        item = DownloadItem(
            id=item_id,
            name=name,
            url=url,
            size_bytes=size_bytes,
            size_display=self._format_size(size_bytes),
            mode=mode
        )
        with self._lock:
            self.items[item_id] = item
        return item
    
    def get_download_links(self, item_ids: List[str] = None) -> List[Dict]:
        """
        获取下载链接列表（不下载，只返回链接供用户自行下载）
        """
        links = []
        with self._lock:
            items = self.items.values() if item_ids is None else [
                self.items[i] for i in item_ids if i in self.items
            ]
            for item in items:
                links.append({
                    "id": item.id,
                    "name": item.name,
                    "url": item.url,
                    "size": item.size_display,
                    "status": item.status.value
                })
        return links
    
    def get_all_links_markdown(self, item_ids: List[str] = None) -> str:
        """获取所有链接的Markdown格式文本"""
        links = self.get_download_links(item_ids)
        if not links:
            return "没有待下载的文件"
        
        lines = ["# 下载链接列表\n", 
                "> 可以使用IDM、ADM、迅雷等工具加速下载\n\n",
                "| 文件名 | 链接 | 大小 |", 
                "|--------|------|------|"]
        
        for link in links:
            lines.append(f"| {link['name']} | `{link['url']}` | {link['size']} |")
        
        return "\n".join(lines)
    
    def start_download(self, item_id: str) -> DownloadResult:
        """
        开始下载单个文件
        """
        with self._lock:
            if item_id not in self.items:
                return DownloadResult(False, error="下载项不存在")
            item = self.items[item_id]
        
        if item.status == DownloadStatus.DOWNLOADING:
            return DownloadResult(False, error="正在下载中")
        
        # 更新状态
        item.status = DownloadStatus.DOWNLOADING
        item.progress = 0
        item.downloaded_bytes = 0
        item.error = None
        self._notify(item)
        
        try:
            # 根据模式下载
            if item.mode == DownloadMode.LINK_ONLY:
                # 仅获取链接模式不需要实际下载
                item.status = DownloadStatus.SUCCESS
                item.progress = 100
                self._notify(item)
                return DownloadResult(True, message="链接已准备好")
            
            # 实际下载
            result = self._download_file(item)
            
            if result.success:
                item.status = DownloadStatus.SUCCESS
                item.progress = 100
                item.local_path = result.file_path
            else:
                item.status = DownloadStatus.FAILED
                item.error = result.error
            
            self._notify(item)
            return result
            
        except Exception as e:
            item.status = DownloadStatus.FAILED
            item.error = str(e)
            self._notify(item)
            return DownloadResult(False, error=str(e))
    
    def _download_file(self, item: DownloadItem) -> DownloadResult:
        """执行文件下载"""
        
        # 目标路径
        filename = item.name
        if not filename:
            # 从URL提取文件名
            filename = item.url.split('/')[-1].split('?')[0] or "download"
        dest_path = self.download_dir / filename
        
        try:
            # 创建请求
            req = urllib.request.Request(item.url, headers={
                'User-Agent': 'Mozilla/5.0 (AI Agent Repair Tool)'
            })
            
            # 获取文件大小
            with urllib.request.urlopen(req, timeout=10) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                item.size_bytes = total_size
                item.size_display = self._format_size(total_size)
            
            # 下载
            req = urllib.request.Request(item.url, headers={
                'User-Agent': 'Mozilla/5.0 (AI Agent Repair Tool)'
            })
            
            with urllib.request.urlopen(req) as response:
                with open(dest_path, 'wb') as f:
                    downloaded = 0
                    last_update = time.time()
                    chunk_size = 8192
                    
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 更新进度
                        if total_size > 0:
                            item.progress = (downloaded / total_size) * 100
                            item.downloaded_bytes = downloaded
                            
                            # 计算速度
                            now = time.time()
                            if now - last_update >= 0.5:
                                item.speed_bps = int((downloaded - item.downloaded_bytes) / (now - last_update)) if now > last_update else 0
                                last_update = now
                                self._notify(item)
            
            item.local_path = str(dest_path)
            return DownloadResult(True, file_path=str(dest_path))
            
        except urllib.error.URLError as e:
            return DownloadResult(False, error=f"网络错误: {e}")
        except Exception as e:
            return DownloadResult(False, error=str(e))
    
    def cancel_download(self, item_id: str):
        """取消下载"""
        with self._lock:
            if item_id in self.items:
                self.items[item_id].status = DownloadStatus.CANCELLED
                self._notify(self.items[item_id])
    
    def get_status(self, item_id: str = None) -> Dict:
        """获取下载状态"""
        with self._lock:
            if item_id:
                item = self.items.get(item_id)
                if not item:
                    return {}
                return self._item_to_dict(item)
            else:
                return {k: self._item_to_dict(v) for k, v in self.items.items()}
    
    def _item_to_dict(self, item: DownloadItem) -> Dict:
        """转换为字典"""
        return {
            "id": item.id,
            "name": item.name,
            "url": item.url,
            "size": item.size_display,
            "status": item.status.value,
            "progress": item.progress,
            "downloaded": self._format_size(item.downloaded_bytes),
            "speed": self._format_speed(item.speed_bps),
            "local_path": item.local_path,
            "error": item.error,
            "mode": item.mode.value
        }
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    @staticmethod
    def _format_speed(bps: int) -> str:
        """格式化下载速度"""
        if bps <= 0:
            return ""
        if bps < 1024:
            return f"{bps} B/s"
        elif bps < 1024 * 1024:
            return f"{bps / 1024:.1f} KB/s"
        else:
            return f"{bps / (1024 * 1024):.1f} MB/s"
    
    def clear_completed(self):
        """清除已完成的下载项"""
        with self._lock:
            completed = [k for k, v in self.items.items() 
                        if v.status in [DownloadStatus.SUCCESS, DownloadStatus.FAILED, DownloadStatus.CANCELLED]]
            for k in completed:
                del self.items[k]


# 全局下载管理器实例
download_manager = DownloadManager()
