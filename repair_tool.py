#!/usr/bin/env python3
"""
AI Agent Repair Tool
自动检测并修复 AI 开发工具问题
支持: OpenCode, Claude Code, Cursor, Windsurf, Hermes-Agent
"""

import os
import sys
import json
import shutil
import platform
from pathlib import Path
from datetime import datetime

# 支持的Agent及其常见安装路径
AGENT_PATHS = {
    "opencode": {
        "name": "OpenCode",
        "paths": {
            "win": ["%USERPROFILE%/.opencode", "%APPDATA%/OpenCode"],
            "mac": ["~/.opencode", "~/Library/Application Support/OpenCode"],
            "linux": ["~/.opencode", "~/.config/opencode"]
        }
    },
    "claude": {
        "name": "Claude Code", 
        "paths": {
            "win": ["%USERPROFILE%/.claude", "%APPDATA%/Claude"],
            "mac": ["~/.claude", "~/Library/Application Support/Claude"],
            "linux": ["~/.claude", "~/.config/claude"]
        }
    },
    "cursor": {
        "name": "Cursor",
        "paths": {
            "win": ["%APPDATA%/Cursor", "%USERPROFILE%/.cursor"],
            "mac": ["~/Library/Application Support/Cursor", "~/.cursor"],
            "linux": ["~/.config/Cursor", "~/.cursor"]
        }
    },
    "windsurf": {
        "name": "Windsurf",
        "paths": {
            "win": ["%APPDATA%/Windsurf", "%USERPROFILE%/.windsurf"],
            "mac": ["~/Library/Application Support/Windsurf", "~/.windsurf"],
            "linux": ["~/.config/Windsurf", "~/.windsurf"]
        }
    },
    "hermes": {
        "name": "Hermes-Agent",
        "paths": {
            "win": ["%USERPROFILE%/.hermes", "%APPDATA%/Hermes"],
            "mac": ["~/.hermes", "~/Library/Application Support/Hermes"],
            "linux": ["~/.hermes", "~/.config/hermes"]
        }
    }
}

def get_os():
    """获取操作系统类型"""
    system = platform.system().lower()
    if system == "windows":
        return "win"
    elif system == "darwin":
        return "mac"
    else:
        return "linux"

def expand_path(path):
    """展开路径中的环境变量"""
    return os.path.expandvars(os.path.expanduser(path))

def find_agent(agent_id):
    """查找Agent安装路径"""
    config = AGENT_PATHS.get(agent_id)
    if not config:
        return None
    
    os_type = get_os()
    for path_template in config["paths"].get(os_type, []):
        path = Path(expand_path(path_template))
        if path.exists():
            return path
    return None

def check_config(agent_path):
    """检查配置文件"""
    issues = []
    config_files = ["settings.json", "config.json", "config.yaml"]
    
    for cf in config_files:
        config_file = agent_path / cf
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    if cf.endswith('.json'):
                        json.load(f)
            except json.JSONDecodeError:
                issues.append(f"配置文件损坏: {cf}")
            except Exception as e:
                issues.append(f"配置文件读取错误: {e}")
    
    return issues

def check_cache(agent_path):
    """检查缓存"""
    issues = []
    cache_dirs = ["cache", "Cache", "temp", "Temp", "CachedData"]
    
    for cd in cache_dirs:
        cache_path = agent_path / cd
        if cache_path.exists():
            try:
                total_size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
                size_mb = total_size / (1024 * 1024)
                if size_mb > 500:
                    issues.append(f"缓存过大: {size_mb:.1f}MB")
            except:
                pass
    
    return issues

def scan_all():
    """扫描所有Agent"""
    print("=" * 60)
    print("AI Agent 智能修复工具")
    print("=" * 60)
    print(f"系统: {platform.system()} {platform.release()}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    found_agents = []
    
    for agent_id, config in AGENT_PATHS.items():
        path = find_agent(agent_id)
        if path:
            print(f"\n【{config['name']}】")
            print(f"  路径: {path}")
            
            issues = []
            issues.extend(check_config(path))
            issues.extend(check_cache(path))
            
            if issues:
                print(f"  状态: ⚠ 发现问题")
                for issue in issues:
                    print(f"    - {issue}")
                found_agents.append((agent_id, path, issues))
            else:
                print(f"  状态: ✓ 正常")
    
    return found_agents

def fix_agent(agent_id, agent_path):
    """修复Agent"""
    print(f"\n正在修复 {AGENT_PATHS[agent_id]['name']}...")
    
    # 1. 备份
    backup_dir = Path.home() / ".ai_agent_backups"
    backup_dir.mkdir(exist_ok=True)
    backup_name = f"{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_path = backup_dir / backup_name
    
    try:
        shutil.copytree(agent_path, backup_path, ignore=shutil.ignore_patterns('cache', 'Cache', 'temp', 'Temp'))
        print(f"  ✓ 已创建备份: {backup_path}")
    except Exception as e:
        print(f"  ✗ 备份失败: {e}")
    
    # 2. 清理缓存
    cache_dirs = ["cache", "Cache", "temp", "Temp", "CachedData"]
    cleaned = 0
    for cd in cache_dirs:
        cache_path = agent_path / cd
        if cache_path.exists():
            try:
                for item in cache_path.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                cleaned += 1
            except:
                pass
    if cleaned > 0:
        print(f"  ✓ 已清理 {cleaned} 个缓存目录")
    
    # 3. 修复配置文件
    config_files = ["settings.json", "config.json"]
    fixed = 0
    for cf in config_files:
        config_file = agent_path / cf
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    json.load(f)
            except json.JSONDecodeError:
                broken = config_file.with_suffix('.json.broken')
                shutil.copy2(config_file, broken)
                default = {"version": "1.0.0", "settings": {}}
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(default, f, indent=2)
                fixed += 1
                print(f"  ✓ 已修复配置文件: {cf}")
    
    print(f"  ✓ 修复完成")

def main():
    """主函数"""
    found = scan_all()
    
    if not found:
        print("\n✓ 未发现需要修复的Agent")
        return
    
    print(f"\n发现 {len(found)} 个Agent需要修复")
    response = input("\n是否立即修复? (y/n): ").strip().lower()
    
    if response == 'y':
        for agent_id, path, _ in found:
            fix_agent(agent_id, path)
        print("\n" + "=" * 60)
        print("✓ 所有修复已完成！")
        print(f"备份保存在: {Path.home() / '.ai_agent_backups'}")
        print("=" * 60)

if __name__ == "__main__":
    main()
