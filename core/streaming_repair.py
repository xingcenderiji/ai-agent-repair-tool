"""
流式修复系统
支持增量备份、大文件处理、进度显示、异步操作
"""

import os
import json
import shutil
import hashlib
import threading
from pathlib import Path
from typing import Callable, Optional, Iterator, Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import time


@dataclass
class ProgressInfo:
    """进度信息"""
    stage: str  # 当前阶段
    current: int  # 当前进度
    total: int  # 总进度
    message: str  # 描述信息
    
    @property
    def percentage(self) -> float:
        if self.total == 0:
            return 100.0
        return (self.current / self.total) * 100


class IncrementalBackup:
    """增量备份管理器"""
    
    def __init__(self, backup_dir: Path):
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = backup_dir / ".backup_manifest.json"
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> Dict:
        """加载备份清单"""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_manifest(self):
        """保存备份清单"""
        with open(self.manifest_file, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2)
    
    def _calculate_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        try:
            hash_obj = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except:
            return ""
    
    def _get_file_info(self, file_path: Path) -> Dict:
        """获取文件信息"""
        try:
            stat = file_path.stat()
            return {
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "hash": self._calculate_hash(file_path)
            }
        except:
            return {}
    
    def should_backup(self, source_path: Path, relative_path: str) -> bool:
        """判断文件是否需要备份"""
        current_info = self._get_file_info(source_path)
        
        if relative_path not in self.manifest:
            return True
        
        stored_info = self.manifest[relative_path]
        
        # 检查大小或修改时间是否变化
        if current_info.get("size") != stored_info.get("size"):
            return True
        if current_info.get("mtime") != stored_info.get("mtime"):
            return True
        
        return False
    
    def backup_incremental(self, source_dir: Path, backup_name: str, 
                          progress_callback: Optional[Callable[[ProgressInfo], None]] = None) -> Path:
        """
        执行增量备份
        """
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 统计文件
        all_files = list(source_dir.rglob('*'))
        files_to_backup = []
        
        for f in all_files:
            if f.is_file():
                relative_path = str(f.relative_to(source_dir))
                if self.should_backup(f, relative_path):
                    files_to_backup.append((f, relative_path))
        
        total_files = len(files_to_backup)
        
        # 执行备份
        for idx, (source_file, relative_path) in enumerate(files_to_backup):
            # 更新进度
            if progress_callback:
                progress = ProgressInfo(
                    stage="backup",
                    current=idx + 1,
                    total=total_files,
                    message=f"备份: {relative_path}"
                )
                progress_callback(progress)
            
            # 复制文件
            target_file = backup_path / relative_path
            target_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                shutil.copy2(source_file, target_file)
                # 更新清单
                self.manifest[relative_path] = self._get_file_info(source_file)
            except Exception as e:
                print(f"  [!] 备份失败 {relative_path}: {e}")
        
        self._save_manifest()
        
        if progress_callback:
            progress = ProgressInfo(
                stage="backup_complete",
                current=total_files,
                total=total_files,
                message=f"增量备份完成: {len(files_to_backup)} 个文件"
            )
            progress_callback(progress)
        
        return backup_path


class StreamingCacheCleaner:
    """流式缓存清理器"""
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.cleaned_count = 0
        self.failed_items: List[str] = []
    
    def clean_streaming(self, cache_dir: Path, 
                       progress_callback: Optional[Callable[[ProgressInfo], None]] = None) -> Iterator[ProgressInfo]:
        """
        流式清理缓存，生成进度信息
        """
        if not cache_dir.exists():
            return
        
        # 统计文件数
        all_items = list(cache_dir.iterdir())
        total_items = len(all_items)
        
        for idx, item in enumerate(all_items):
            progress = ProgressInfo(
                stage="cleaning",
                current=idx + 1,
                total=total_items,
                message=f"清理: {item.name}"
            )
            
            try:
                if item.is_file() or item.is_symlink():
                    item.unlink()
                    self.cleaned_count += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    self.cleaned_count += 1
            except Exception as e:
                self.failed_items.append(str(item))
                progress.message = f"清理失败: {item.name} ({e})"
            
            yield progress
        
        # 完成
        yield ProgressInfo(
            stage="clean_complete",
            current=total_items,
            total=total_items,
            message=f"清理完成: {self.cleaned_count}/{total_items}"
        )
    
    def get_summary(self) -> Dict:
        """获取清理摘要"""
        return {
            "cleaned": self.cleaned_count,
            "failed": len(self.failed_items),
            "failed_items": self.failed_items
        }


class ParallelScanner:
    """并行扫描器"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.results: Dict[str, List[str]] = {}
        self._lock = threading.Lock()
    
    def scan_agent(self, agent_id: str, agent_path: Path, 
                   check_functions: List[Callable[[Path], List[str]]]) -> Dict[str, List[str]]:
        """
        并行扫描Agent
        """
        self.results = {}
        threads = []
        
        # 为每个检查函数创建线程
        for idx, check_func in enumerate(check_functions):
            thread_name = f"check_{idx}"
            t = threading.Thread(
                target=self._run_check,
                args=(thread_name, agent_path, check_func)
            )
            threads.append(t)
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        return self.results
    
    def _run_check(self, name: str, agent_path: Path, check_func: Callable[[Path], List[str]]):
        """运行单个检查"""
        try:
            issues = check_func(agent_path)
            with self._lock:
                self.results[name] = issues
        except Exception as e:
            with self._lock:
                self.results[name] = [f"检查失败: {e}"]


def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def print_progress_bar(progress: ProgressInfo, width: int = 50):
    """打印进度条"""
    filled = int(width * progress.current / max(progress.total, 1))
    bar = '█' * filled + '░' * (width - filled)
    percentage = progress.percentage
    
    print(f"\r[{bar}] {percentage:.1f}% {progress.message}", end='', flush=True)
    
    if progress.current >= progress.total:
        print()  # 换行


# 使用示例
if __name__ == "__main__":
    # 测试增量备份
    backup = IncrementalBackup(Path.home() / ".test_backup")
    
    def on_progress(p: ProgressInfo):
        print_progress_bar(p)
    
    # backup.backup_incremental(Path("/path/to/agent"), "test_backup_001", on_progress)
    
    # 测试流式清理
    cleaner = StreamingCacheCleaner()
    # for progress in cleaner.clean_streaming(Path("/path/to/cache"), on_progress):
    #     pass
