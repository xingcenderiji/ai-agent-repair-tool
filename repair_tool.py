#!/usr/bin/env python3
"""
Tiangong - AI Agent Repair Tool
全自动识别并修复 AI 开发工具问题 - 无需用户干预
支持: Cursor, Claude Code, OpenCode, Windsurf, Cline, Aider, Copilot, Continue, Roo Code, Augment Code, Hermes-Agent
"""

import os
import sys
import json
import shutil
import platform
import stat
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Windows 终端强制 UTF-8 编码
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

from agent_registry import AGENT_PATHS
from core.audit_logger import get_audit_logger, OperationType, OperationStatus
from core.i18n import _, set_language, get_language, get_available_languages

# 全局审计日志实例
audit = get_audit_logger()


class RepairResult:
    """修复结果记录"""
    def __init__(self, agent_id: str, agent_path: Path):
        self.agent_id = agent_id
        self.agent_path = agent_path
        self.agent_name = AGENT_PATHS.get(agent_id, {}).get('name', agent_id)
        self.backup_created = False
        self.backup_path: Optional[Path] = None
        self.cache_cleaned = 0
        self.config_fixed = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def add_error(self, msg: str):
        self.errors.append(msg)
        
    def add_warning(self, msg: str):
        self.warnings.append(msg)
        
    def is_success(self) -> bool:
        """修复是否成功（没有错误）"""
        return len(self.errors) == 0
        
    def has_changes(self) -> bool:
        """是否有实际修复操作"""
        return self.backup_created or self.cache_cleaned > 0 or self.config_fixed > 0


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


def check_config(agent_path: Path) -> List[str]:
    """检查配置文件，返回问题列表"""
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
            except UnicodeDecodeError:
                issues.append(f"配置文件编码错误: {cf}")
            except PermissionError:
                issues.append(f"配置文件无读取权限: {cf}")
            except OSError as e:
                issues.append(f"配置文件读取错误({e.errno}): {cf}")

    return issues


def check_cache(agent_path: Path) -> List[str]:
    """检查缓存，返回问题列表"""
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


def scan_all() -> List[Tuple[str, Path, List[str]]]:
    """扫描所有Agent，返回 (agent_id, path, issues) 列表"""
    # 开始审计会话
    session_id = audit.start_session()
    print("=" * 60)
    print(_("app_name") + " - " + _("app_description"))
    print("=" * 60)
    print(f"{_('gui_language')}: {get_language().upper()}")
    print(f"{platform.system()} {platform.release()}")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Session ID: {session_id}")
    print("=" * 60)

    found_agents = []

    for agent_id, config in AGENT_PATHS.items():
        path = find_agent(agent_id)
        if path:
            print(f"\n[{config['name']}]")
            print(f"  Path: {path}")

            issues = []
            issues.extend(check_config(path))
            issues.extend(check_cache(path))

            if issues:
                print(f"  Status: ! {_('scan_found_issues', count=len(issues))}")
                for issue in issues:
                    print(f"    - {issue}")
                found_agents.append((agent_id, path, issues))
                # 记录发现问题
                audit.log_operation(
                    operation=OperationType.SCAN,
                    agent_id=agent_id,
                    target_path=path,
                    status=OperationStatus.WARNING,
                    details={"issues_found": len(issues), "issues": issues}
                )
            else:
                print(f"  Status: ✓ {_('agent_status_healthy')}")
                # 记录正常扫描
                audit.log_operation(
                    operation=OperationType.SCAN,
                    agent_id=agent_id,
                    target_path=path,
                    status=OperationStatus.SUCCESS,
                    details={"issues_found": 0}
                )

    return found_agents


def _remove_readonly(func, path, excinfo):
    """Windows下强制删除只读文件"""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def fix_agent(agent_id: str, agent_path: Path) -> RepairResult:
    """
    修复Agent，返回详细结果
    """
    import time
    result = RepairResult(agent_id, agent_path)
    print(f"\n  >>> {_('repairing_agent', agent_name=result.agent_name)}")

    # 1. 备份
    print(f"      {_('repair_step_backup')}")
    backup_start = time.time()
    backup_dir = Path.home() / ".ai_agent_backups"
    backup_dir.mkdir(exist_ok=True)
    backup_name = f"{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_path = backup_dir / backup_name

    if backup_path.exists():
        try:
            shutil.rmtree(backup_path)
        except Exception as e:
            result.add_error(f"Failed to clean old backup: {e}")

    try:
        shutil.copytree(
            agent_path, backup_path,
            ignore=shutil.ignore_patterns('cache', 'Cache', 'temp', 'Temp')
        )
        result.backup_created = True
        result.backup_path = backup_path
        print(f"          ✓ {_('backup_created', path=backup_path)}")
        # 记录成功备份
        audit.log_operation(
            operation=OperationType.BACKUP,
            agent_id=agent_id,
            target_path=backup_path,
            status=OperationStatus.SUCCESS,
            details={"backup_name": backup_name, "source": str(agent_path)},
            duration_ms=int((time.time() - backup_start) * 1000)
        )
    except PermissionError as e:
        result.add_error(_('backup_failed', error=str(e)))
        audit.log_operation(
            operation=OperationType.BACKUP,
            agent_id=agent_id,
            target_path=backup_path,
            status=OperationStatus.FAILED,
            error_message=str(e),
            details={"error_type": "PermissionError"}
        )
    except OSError as e:
        result.add_error(_('backup_failed', error=str(e)))
        audit.log_operation(
            operation=OperationType.BACKUP,
            agent_id=agent_id,
            target_path=backup_path,
            status=OperationStatus.FAILED,
            error_message=str(e),
            details={"error_type": "OSError"}
        )

    # 2. 清理缓存
    print(f"      {_('repair_step_cache')}")
    cache_start = time.time()
    cache_dirs = ["cache", "Cache", "temp", "Temp", "CachedData"]
    cleaned = 0
    failed_caches = []

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
                        failed_caches.append(str(item))
                    except OSError:
                        failed_caches.append(str(item))
                cleaned += 1
            except PermissionError:
                result.add_warning(f"Cannot access cache directory: {cd}")
    
    result.cache_cleaned = cleaned
    cache_status = OperationStatus.SUCCESS if not failed_caches else OperationStatus.WARNING
    audit.log_operation(
        operation=OperationType.CACHE_CLEAN,
        agent_id=agent_id,
        target_path=agent_path,
        status=cache_status,
        details={
            "cleaned_dirs": cleaned,
            "failed_items": len(failed_caches),
            "cache_dirs": cache_dirs
        },
        duration_ms=int((time.time() - cache_start) * 1000)
    )
    if cleaned > 0:
        print(f"          ✓ 已清理 {cleaned} 个缓存目录")
    if failed_caches:
        result.add_warning(f"部分缓存文件无法清理: {len(failed_caches)}个")

    # 3. 修复配置文件
    print(f"      [3/3] 修复配置文件...")
    config_start = time.time()
    config_files = ["settings.json", "config.json"]
    fixed = 0
    failed_configs = []
    
    for cf in config_files:
        config_file = agent_path / cf
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    json.load(f)
                # 文件正常，无需修复
            except json.JSONDecodeError:
                # 配置文件损坏，需要修复
                try:
                    # 备份损坏的文件
                    broken = config_file.with_suffix('.json.broken')
                    shutil.copy2(config_file, broken)
                    # 生成默认配置
                    default = {"version": "1.0.0", "settings": {}}
                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump(default, f, indent=2)
                    fixed += 1
                    print(f"          ✓ 已修复: {cf}")
                except OSError as e:
                    failed_configs.append(f"{cf}({e})")
            except OSError as e:
                failed_configs.append(f"{cf}({e})")
    
    result.config_fixed = fixed
    config_status = OperationStatus.SUCCESS if not failed_configs else OperationStatus.FAILED
    audit.log_operation(
        operation=OperationType.CONFIG_FIX,
        agent_id=agent_id,
        target_path=agent_path,
        status=config_status,
        details={
            "fixed_files": fixed,
            "failed_files": len(failed_configs),
            "config_files": config_files
        },
        error_message="; ".join(failed_configs) if failed_configs else None,
        duration_ms=int((time.time() - config_start) * 1000)
    )
    if fixed > 0:
        print(f"          ✓ 已修复 {fixed} 个配置文件")
    if failed_configs:
        result.add_error(f"配置文件修复失败: {', '.join(failed_configs)}")

    # 修复完成报告
    if result.is_success():
        print(f"      ✓ {result.agent_name} 修复完成")
    else:
        print(f"      ⚠ {result.agent_name} 修复完成，但有 {len(result.errors)} 个错误")
    
    return result


def verify_fix(agent_path: Path, original_issues: List[str]) -> Tuple[bool, List[str]]:
    """
    验证修复是否成功
    返回: (是否全部修复, 仍存在的问题)
    """
    remaining_issues = []
    
    # 重新检查配置
    config_issues = check_config(agent_path)
    remaining_issues.extend(config_issues)
    
    # 重新检查缓存
    cache_issues = check_cache(agent_path)
    remaining_issues.extend(cache_issues)
    
    # 检查是否还有原来的问题
    fixed_count = len(original_issues) - len(remaining_issues)
    
    return len(remaining_issues) == 0, remaining_issues


def print_summary(results: List[RepairResult]):
    """打印修复摘要报告"""
    print("\n" + "=" * 60)
    print("修复摘要报告")
    print("=" * 60)
    
    total = len(results)
    success = sum(1 for r in results if r.is_success())
    with_changes = sum(1 for r in results if r.has_changes())
    total_errors = sum(len(r.errors) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)
    
    print(f"\n总体统计:")
    print(f"  修复Agent数: {total}")
    print(f"  完全成功: {success}/{total}")
    print(f"  有实际修复: {with_changes}")
    print(f"  错误数: {total_errors}")
    print(f"  警告数: {total_warnings}")
    
    # 详细报告
    for result in results:
        print(f"\n[{result.agent_name}]")
        print(f"  路径: {result.agent_path}")
        print(f"  状态: {'✓ 成功' if result.is_success() else '⚠ 有错误'}")
        print(f"  备份: {'✓ ' + str(result.backup_path) if result.backup_created else '✗ 失败'}")
        print(f"  清理缓存: {result.cache_cleaned}个目录")
        print(f"  修复配置: {result.config_fixed}个文件")
        
        if result.errors:
            print(f"  错误:")
            for err in result.errors:
                print(f"    - {err}")
        if result.warnings:
            print(f"  警告:")
            for warn in result.warnings:
                print(f"    - {warn}")
    
    print("\n" + "=" * 60)
    print(f"备份位置: {Path.home() / '.ai_agent_backups'}")
    print("=" * 60)


def _wait_for_exit():
    """等待用户按键退出，非交互环境自动跳过"""
    if '--no-wait' in sys.argv or '--batch' in sys.argv:
        return
    try:
        if sys.stdin.isatty():
            input()
        else:
            time.sleep(2)
    except (EOFError, OSError):
        time.sleep(2)


def main():
    """主函数 - 全自动模式"""
    try:
        found = scan_all()
    except Exception as e:
        print(f"扫描出错: {e}")
        import traceback
        audit.log_operation(
            operation=OperationType.SCAN,
            status=OperationStatus.FAILED,
            error_message=str(e),
            stack_trace=traceback.format_exc()
        )
        audit.end_session({"error": str(e)})
        return

    if not found:
        print("\n[OK] 未发现需要修复的Agent")
        audit.end_session({"agents_found": 0, "agents_repaired": 0})
        batch_mode = '--no-wait' in sys.argv or '--batch' in sys.argv
        if not batch_mode:
            print("\n按任意键退出...")
            _wait_for_exit()
        return

    print(f"\n[!] 发现 {len(found)} 个Agent需要修复")

    # 批量模式跳过倒计时
    batch_mode = '--no-wait' in sys.argv or '--batch' in sys.argv
    if not batch_mode:
        print("[!] 3秒后开始自动修复...")
        print("    (按 Ctrl+C 取消)")

        # 倒计时
        try:
            for i in range(3, 0, -1):
                print(f"    {i}...")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n已取消修复")
            audit.log_operation(
                operation=OperationType.SCAN,
                status=OperationStatus.SKIPPED,
                details={"reason": "user_cancelled"}
            )
            audit.end_session({"cancelled": True})
            return
    
    print("\n" + "-" * 60)
    print("开始自动修复...")
    print("-" * 60)

    # 执行修复
    results: List[RepairResult] = []
    for agent_id, path, issues in found:
        result = fix_agent(agent_id, path)
        results.append(result)
        
        # 验证修复
        if result.is_success() and result.has_changes():
            print(f"      [验证] 检查修复结果...")
            fully_fixed, remaining = verify_fix(path, issues)
            if fully_fixed:
                print(f"          ✓ 所有问题已修复")
                audit.log_operation(
                    operation=OperationType.VALIDATION,
                    agent_id=agent_id,
                    target_path=path,
                    status=OperationStatus.SUCCESS,
                    details={"all_issues_fixed": True}
                )
            else:
                print(f"          ⚠ 仍有 {len(remaining)} 个问题未解决")
                for issue in remaining:
                    print(f"            - {issue}")
                audit.log_operation(
                    operation=OperationType.VALIDATION,
                    agent_id=agent_id,
                    target_path=path,
                    status=OperationStatus.WARNING,
                    details={"all_issues_fixed": False, "remaining_issues": remaining}
                )
    
    # 打印摘要
    print_summary(results)
    
    # 结束审计会话
    summary = {
        "agents_found": len(found),
        "agents_repaired": len(results),
        "successful_repairs": sum(1 for r in results if r.is_success()),
        "total_errors": sum(len(r.errors) for r in results),
        "total_warnings": sum(len(r.warnings) for r in results),
        "backups_created": sum(1 for r in results if r.backup_created),
        "caches_cleaned": sum(r.cache_cleaned for r in results),
        "configs_fixed": sum(r.config_fixed for r in results)
    }
    audit.end_session(summary)
    
    # 显示审计日志位置
    print(f"\n审计日志位置: {Path.home() / '.ai_agent_repair' / 'audit_logs'}")
    print("=" * 60)

    batch_mode = '--no-wait' in sys.argv or '--batch' in sys.argv
    if not batch_mode:
        print("\n按任意键退出...")
        _wait_for_exit()


if __name__ == "__main__":
    main()
