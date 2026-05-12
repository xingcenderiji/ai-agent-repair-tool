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
import stat
from pathlib import Path
from datetime import datetime

# Windows 终端强制 UTF-8 编码
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

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
    """展开路径中的环境变量和~"""
    if not path or not path.strip():
        return Path.cwd()
    return Path(os.path.expandvars(os.path.expanduser(path.strip())))


def find_agent(agent_id):
    """查找Agent安装路径"""
    config = AGENT_PATHS.get(agent_id)
    if not config:
        return None

    os_type = get_os()
    for path_template in config["paths"].get(os_type, []):
        try:
            path = expand_path(path_template)
            if path.exists():
                return path
        except (OSError, ValueError):
            continue
    return None


def _safe_get_size(path):
    """安全获取文件大小，处理权限问题和符号链接"""
    try:
        if path.is_symlink():
            return 0
        return path.stat().st_size
    except (OSError, PermissionError):
        return 0


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
                    # .yaml 文件暂不验证内容，只检查可读性
            except json.JSONDecodeError:
                issues.append(f"配置文件损坏: {cf}")
            except UnicodeDecodeError:
                issues.append(f"配置文件编码错误: {cf}")
            except PermissionError:
                issues.append(f"配置文件无读取权限: {cf}")
            except OSError as e:
                issues.append(f"配置文件读取错误({e.errno}): {cf}")

    return issues


def check_cache(agent_path):
    """检查缓存，安全处理符号链接和权限问题"""
    issues = []
    cache_dirs = ["cache", "Cache", "temp", "Temp", "CachedData"]

    for cd in cache_dirs:
        cache_path = agent_path / cd
        if cache_path.exists():
            try:
                total_size = 0
                for f in cache_path.rglob('*'):
                    if f.is_file() and not f.is_symlink():
                        total_size += _safe_get_size(f)
                size_mb = total_size / (1024 * 1024)
                if size_mb > 500:
                    issues.append(f"缓存过大: {size_mb:.1f}MB")
            except PermissionError:
                issues.append(f"缓存目录无访问权限: {cd}")
            except OSError:
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
            print(f"\n[{config['name']}]")
            print(f"  路径: {path}")

            issues = []
            issues.extend(check_config(path))
            issues.extend(check_cache(path))

            if issues:
                print(f"  状态: ! 发现问题")
                for issue in issues:
                    print(f"    - {issue}")
                found_agents.append((agent_id, path, issues))
            else:
                print(f"  状态: OK 正常")

    return found_agents


def _remove_readonly(func, path, excinfo):
    """Windows下强制删除只读文件"""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def fix_agent(agent_id, agent_path):
    """修复Agent"""
    agent_name = AGENT_PATHS.get(agent_id, {}).get('name', agent_id)
    print(f"\n正在修复 {agent_name}...")

    # 1. 备份
    backup_dir = Path.home() / ".ai_agent_backups"
    backup_dir.mkdir(exist_ok=True)
    backup_name = f"{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_path = backup_dir / backup_name

    if backup_path.exists():
        shutil.rmtree(backup_path)

    try:
        shutil.copytree(
            agent_path, backup_path,
            ignore=shutil.ignore_patterns('cache', 'Cache', 'temp', 'Temp')
        )
        print(f"  [OK] 已创建备份: {backup_path}")
    except PermissionError:
        print(f"  [!] 备份失败: 权限不足")
    except OSError as e:
        print(f"  [!] 备份失败: {e}")

    # 2. 清理缓存
    cache_dirs = ["cache", "Cache", "temp", "Temp", "CachedData"]
    cleaned = 0
    for cd in cache_dirs:
        cache_path = agent_path / cd
        if cache_path.exists():
            try:
                for item in cache_path.iterdir():
                    try:
                        if item.is_file() or item.is_symlink():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item, onerror=_remove_readonly)
                    except PermissionError:
                        pass
                    except OSError:
                        pass
                cleaned += 1
            except PermissionError:
                pass
    if cleaned > 0:
        print(f"  [OK] 已清理 {cleaned} 个缓存目录")

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
                try:
                    broken = config_file.with_suffix('.json.broken')
                    shutil.copy2(config_file, broken)
                    default = {"version": "1.0.0", "settings": {}}
                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump(default, f, indent=2)
                    fixed += 1
                    print(f"  [OK] 已修复配置文件: {cf}")
                except OSError:
                    print(f"  [!] 修复配置文件失败: {cf}")

    print(f"  [OK] 修复完成")


def main():
    """主函数"""
    try:
        found = scan_all()
    except Exception as e:
        print(f"扫描出错: {e}")
        return

    if not found:
        print("\n[OK] 未发现需要修复的Agent")
        return

    print(f"\n发现 {len(found)} 个Agent需要修复")

    try:
        response = input("\n是否立即修复? (y/n): ").strip().lower()
    except EOFError:
        # 无终端环境（如CI），自动跳过修复
        print("(非交互环境，跳过修复)")
        return

    if response == 'y':
        for agent_id, path, _ in found:
            fix_agent(agent_id, path)
        print("\n" + "=" * 60)
        print("[OK] 所有修复已完成！")
        print(f"备份保存在: {Path.home() / '.ai_agent_backups'}")
        print("=" * 60)


if __name__ == "__main__":
    main()
