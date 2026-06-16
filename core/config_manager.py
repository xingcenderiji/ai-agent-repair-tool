"""
模块化配置管理系统
支持版本检测、远程配置下载、本地缓存
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import fnmatch


@dataclass
class AgentConfig:
    """Agent配置数据类"""
    agent_id: str
    agent_name: str
    version: str
    min_supported_version: str = "1.0.0"
    config_files: List[str] = None
    cache_dirs: List[str] = None
    log_files: List[str] = None
    critical_files: List[str] = None
    default_config: Dict[str, Any] = None
    repair_strategies: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.config_files is None:
            self.config_files = ["settings.json", "config.json"]
        if self.cache_dirs is None:
            self.cache_dirs = ["cache", "Cache", "temp", "Temp", "CachedData"]
        if self.log_files is None:
            self.log_files = ["*.log", "logs/*.log"]
        if self.critical_files is None:
            self.critical_files = []
        if self.default_config is None:
            self.default_config = {"version": "1.0.0", "settings": {}}
        if self.repair_strategies is None:
            self.repair_strategies = {}


class ConfigManager:
    """配置管理器"""
    
    # 远程配置仓库地址
    REMOTE_REPO_URL = "https://raw.githubusercontent.com/xingcenderiji/ai-agent-repair-tool/main/configs"
    
    def __init__(self, local_config_dir: Optional[Path] = None):
        self.local_config_dir = local_config_dir or Path(__file__).parent.parent / "configs"
        self.cache_dir = Path.home() / ".ai_agent_repair" / "config_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._config_cache: Dict[str, AgentConfig] = {}
        
    def detect_version(self, agent_path: Path) -> str:
        """
        检测Agent版本
        通过多种方式尝试获取版本号
        """
        version = "unknown"
        
        # 1. 尝试从 package.json 读取
        package_file = agent_path / "package.json"
        if package_file.exists():
            try:
                with open(package_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    version = data.get("version", "unknown")
            except Exception:
                pass
        
        # 2. 尝试从 version 文件读取
        if version == "unknown":
            for vf in ["version", "VERSION", ".version"]:
                version_file = agent_path / vf
                if version_file.exists():
                    try:
                        version = version_file.read_text().strip()
                        break
                    except Exception:
                        pass
        
        # 3. 尝试从配置文件读取
        if version == "unknown":
            for cf in ["settings.json", "config.json"]:
                config_file = agent_path / cf
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            version = data.get("version", "unknown")
                            if version != "unknown":
                                break
                    except Exception:
                        pass
        
        return version
    
    def _get_cache_path(self, agent_id: str, version: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{agent_id}_{version}.json"
    
    def _is_cache_valid(self, cache_path: Path, max_age_hours: int = 24) -> bool:
        """检查缓存是否有效"""
        if not cache_path.exists():
            return False
        
        # 检查缓存时间
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        return age < timedelta(hours=max_age_hours)
    
    def download_remote_config(self, agent_id: str, version: str) -> Optional[Dict]:
        """
        从远程仓库下载配置
        尝试下载版本特定配置，失败则下载默认配置
        """
        urls_to_try = [
            f"{self.REMOTE_REPO_URL}/{agent_id}/{version}.json",
            f"{self.REMOTE_REPO_URL}/{agent_id}/default.json",
        ]
        
        for url in urls_to_try:
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        'User-Agent': 'AI-Agent-Repair-Tool/1.0',
                        'Accept': 'application/json'
                    }
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        # 保存到缓存
                        cache_path = self._get_cache_path(agent_id, version)
                        with open(cache_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2)
                        return data
            except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError):
                continue
        
        return None
    
    def load_local_config(self, agent_id: str, version: str) -> Optional[Dict]:
        """加载本地配置"""
        # 尝试加载版本特定配置
        version_file = self.local_config_dir / agent_id / f"{version}.json"
        if version_file.exists():
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # 尝试加载默认配置
        default_file = self.local_config_dir / agent_id / "default.json"
        if default_file.exists():
            try:
                with open(default_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return None
    
    def get_config(self, agent_id: str, agent_path: Path) -> AgentConfig:
        """
        获取Agent配置
        优先级：缓存 > 远程 > 本地 > 内置默认
        """
        # 检测版本
        version = self.detect_version(agent_path)
        
        # 检查内存缓存
        cache_key = f"{agent_id}:{version}"
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        config_data = None
        
        # 1. 尝试从缓存加载
        cache_path = self._get_cache_path(agent_id, version)
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except Exception:
                pass
        
        # 2. 尝试从远程下载
        if config_data is None:
            config_data = self.download_remote_config(agent_id, version)
        
        # 3. 尝试加载本地配置
        if config_data is None:
            config_data = self.load_local_config(agent_id, version)
        
        # 4. 使用内置默认配置
        if config_data is None:
            config_data = self._get_builtin_config(agent_id)
        
        # 创建配置对象
        config = AgentConfig(
            agent_id=agent_id,
            agent_name=config_data.get("agent_name", agent_id),
            version=version,
            min_supported_version=config_data.get("min_supported_version", "1.0.0"),
            config_files=config_data.get("config_files", ["settings.json", "config.json"]),
            cache_dirs=config_data.get("cache_dirs", ["cache", "Cache", "temp", "Temp"]),
            log_files=config_data.get("log_files", ["*.log"]),
            critical_files=config_data.get("critical_files", []),
            default_config=config_data.get("default_config", {"version": "1.0.0", "settings": {}}),
            repair_strategies=config_data.get("repair_strategies", {})
        )
        
        # 存入缓存
        self._config_cache[cache_key] = config
        
        return config
    
    def _get_builtin_config(self, agent_id: str) -> Dict:
        """获取内置默认配置"""
        return {
            "agent_name": agent_id.capitalize(),
            "config_files": ["settings.json", "config.json", "config.yaml"],
            "cache_dirs": ["cache", "Cache", "temp", "Temp", "CachedData"],
            "log_files": ["*.log", "logs/*.log"],
            "default_config": {"version": "1.0.0", "settings": {}},
            "repair_strategies": {
                "config_corrupted": "replace_with_default",
                "cache_oversized": "clean_all",
                "permission_denied": "skip_and_report"
            }
        }
    
    def match_version(self, detected_version: str, config_version: str) -> bool:
        """
        版本匹配
        支持通配符匹配，如 1.x 匹配 1.0, 1.1, 1.2 等
        """
        if config_version.endswith(".x"):
            prefix = config_version[:-2]
            return detected_version.startswith(prefix + ".")
        return fnmatch.fnmatch(detected_version, config_version)


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
