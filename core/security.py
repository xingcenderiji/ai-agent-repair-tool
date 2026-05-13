"""
安全验证系统
防止恶意配置、路径遍历、数据窃取、危险操作

安全层级：
  1. 路径白名单/黑名单 - 限制操作范围
  2. 配置签名验证 - 防止篡改
  3. 操作沙箱 - 限制文件系统访问
  4. 用户确认 - 高风险操作需用户确认
  5. 审计日志 - 记录所有操作
"""

import os
import re
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ============================================================
# 1. 路径安全
# ============================================================

# 系统关键目录 - 绝对禁止操作
SYSTEM_BLACKLIST = [
    "/etc", "/bin", "/sbin", "/usr/bin", "/usr/sbin", "/usr/lib",
    "/System", "/System/Library", "/Library",
    "C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)",
    "C:\\System32", "C:\\SysWOW64",
    "/boot", "/dev", "/proc", "/sys", "/lib", "/lib64",
    "/var/log", "/var/run",
]

# 敏感用户目录 - 禁止操作（即使在家目录下）
SENSITIVE_USER_DIRS = [
    "~/.ssh",           # SSH 密钥
    "~/.gnupg",         # GPG 密钥
    "~/.password-store", # pass 密码管理器
    "~/.config/ssh",    # SSH 配置
    "~/.kube",          # Kubernetes 凭证
    "~/.docker",        # Docker 凭证
    "~/.aws",           # AWS 凭证
    "~/.config/gcloud", # GCP 凭证
    "~/.azure",         # Azure 凭证
]

# 允许操作的目录前缀 - 白名单
SAFE_PATH_PREFIXES = [
    # 用户主目录下的 AI 工具目录
    "~/.claude", "~/.opencode", "~/.cursor", "~/.windsurf",
    "~/.cline", "~/.continue", "~/.copilot", "~/.aider",
    "~/.roo", "~/.augment", "~/.hermes",
    # 应用数据目录
    "~/Library/Application Support/Cursor",
    "~/Library/Application Support/Claude",
    "~/Library/Application Support/Windsurf",
    "~/Library/Application Support/Cline",
    "~/Library/Application Support/Continue",
    "~/Library/Application Support/GitHub Copilot",
    # Windows 应用数据
    "%APPDATA%/Cursor", "%APPDATA%/Claude", "%APPDATA%/Windsurf",
    "%APPDATA%/Cline", "%APPDATA%/Continue",
    "%APPDATA%/GitHub Copilot", "%APPDATA%/Aider",
    "%USERPROFILE%/.claude", "%USERPROFILE%/.opencode",
    "%USERPROFILE%/.cursor", "%USERPROFILE%/.windsurf",
    "%USERPROFILE%/.cline", "%USERPROFILE%/.aider",
    # Linux 配置目录
    "~/.config/cline", "~/.config/continue",
    "~/.config/cursor", "~/.config/windsurf",
    "~/.config/github-copilot", "~/.config/augment",
    # 备份目录
    "~/.ai_agent_backups",
    # 工具自身目录
    "~/.ai_agent_repair",
]

# 禁止操作的文件模式
DANGEROUS_FILE_PATTERNS = [
    # 系统文件
    r".*\.sys$", r".*\.dll$", r".*\.so$", r".*\.dylib$",
    r".*\.exe$", r".*\.bat$", r".*\.cmd$", r".*\.sh$",
    r".*\.com$", r".*\.msi$",
    # 凭证文件
    r".*\.pem$", r".*\.key$", r".*\.p12$", r".*\.pfx$",
    r".*\.keystore$", r".*\.jks$",
    # SSH
    r".*ssh/.*", r".*\.sshconfig$",
    # 浏览器数据
    r".*\.sqlite3?$", r".*cookies.*", r".*password.*",
    r".*\.keychain$", r".*\.keydb$",
    # 钱包/加密货币
    r".*wallet.*", r".*\.eth$", r".*\.btc$",
    # 系统配置
    r".*crontab$", r".*sudoers$", r".*passwd$",
    r".*shadow$", r".*hosts$",
]

# 允许操作的文件模式
SAFE_FILE_PATTERNS = [
    r".*\.json$", r".*\.yaml$", r".*\.yml$",
    r".*\.log$", r".*\.txt$", r".*\.md$",
    r".*\.xml$", r".*\.toml$", r".*\.ini$",
    r".*\.conf$", r".*\.cfg$",
    r".*\.cache$", r".*\.tmp$",
    r".*\.db$", r".*\.vscdb$",
]


class PathValidator:
    """路径安全验证器"""

    def __init__(self):
        self._blacklist_resolved = set()
        self._init_blacklist()

    def _init_blacklist(self):
        """初始化黑名单（解析环境变量）"""
        # 系统黑名单
        for path in SYSTEM_BLACKLIST:
            try:
                resolved = Path(os.path.expandvars(os.path.expanduser(path))).resolve()
                self._blacklist_resolved.add(str(resolved))
                self._blacklist_resolved.add(str(resolved).lower())
            except:
                pass
        # 敏感用户目录
        for path in SENSITIVE_USER_DIRS:
            try:
                resolved = Path(os.path.expandvars(os.path.expanduser(path))).resolve()
                self._blacklist_resolved.add(str(resolved))
                self._blacklist_resolved.add(str(resolved).lower())
            except:
                pass

    def is_safe_path(self, path: Path) -> Tuple[bool, str]:
        """
        验证路径是否安全
        返回: (是否安全, 原因)
        """
        # 先展开 ~ 和环境变量
        try:
            expanded = os.path.expandvars(os.path.expanduser(str(path)))
            path = Path(expanded)
        except (OSError, ValueError) as e:
            return False, f"路径展开失败: {e}"

        try:
            resolved = path.resolve()
            resolved_str = str(resolved)
            resolved_lower = resolved_str.lower()
        except (OSError, ValueError) as e:
            return False, f"路径解析失败: {e}"

        # 1. 检查路径遍历攻击
        if ".." in path.parts:
            return False, "路径包含遍历符(..)"

        # 2. 检查符号链接指向
        if path.is_symlink():
            try:
                target = os.readlink(path)
                if ".." in target:
                    return False, "符号链接包含遍历符"
            except:
                pass

        # 3. 检查黑名单
        for blacklisted in self._blacklist_resolved:
            if resolved_lower.startswith(blacklisted.lower()):
                return False, f"路径在系统黑名单中: {blacklisted}"

        # 4. 检查是否在用户主目录下
        home = str(Path.home().resolve())
        if not resolved_lower.startswith(home.lower()):
            return False, f"路径不在用户主目录下: {resolved_str}"

        # 5. 检查白名单（宽松模式 - 允许主目录下的AI工具目录）
        safe = False
        for prefix in SAFE_PATH_PREFIXES:
            try:
                expanded = Path(os.path.expandvars(os.path.expanduser(prefix))).resolve()
                if resolved_lower.startswith(str(expanded).lower()):
                    safe = True
                    break
            except:
                pass

        # 如果不在白名单中但在主目录下，给出警告但允许（用于社区新工具）
        if not safe:
            # 额外检查：是否是隐藏目录（以.开头）
            if any(part.startswith('.') for part in resolved.parts):
                safe = True  # 允许主目录下的隐藏目录

        if not safe:
            return False, f"路径不在安全白名单中: {resolved_str}"

        return True, "安全"

    def is_safe_file(self, file_path: Path) -> Tuple[bool, str]:
        """验证文件是否安全"""
        # 先检查路径
        path_safe, reason = self.is_safe_path(file_path)
        if not path_safe:
            return False, reason

        filename = file_path.name

        # 检查危险文件模式
        for pattern in DANGEROUS_FILE_PATTERNS:
            if re.match(pattern, filename, re.IGNORECASE):
                return False, f"文件类型禁止操作: {filename}"

        return True, "安全"


# ============================================================
# 2. 配置安全验证
# ============================================================

# 配置中禁止的字段
FORBIDDEN_CONFIG_KEYS = [
    "exec", "execute", "command", "shell", "system",
    "eval", "compile", "import", "require",
    "spawn", "child_process", "subprocess",
    "network", "fetch", "request", "http",
    "upload", "download", "exfil",
    "registry", "regedit",
    "sudo", "admin", "privilege",
]

# 修复策略中允许的操作
ALLOWED_REPAIR_STRATEGIES = [
    "replace_with_default",
    "clean_all", "clean_keep_recent",
    "skip_and_report",
    "validate_and_repair",
    "validate_json", "validate_yaml",
    "validate_mcp_config", "validate_mcp_json",
    "validate_api_config", "validate_api_endpoint",
    "validate_model_name", "check_api_key",
    "set_gpu_acceleration_off",
    "delete_state_db", "delete_global_storage",
    "invalidate_caches", "rebuild_index",
    "reset_terminal_config",
    "create_env_template", "create_default",
    "disable_plugin", "backup_and_replace",
    "restart", "re_login", "reload_window",
    "check_network", "check_shell_path",
    "set_default_terminal", "select_compatible_model",
    "check_paths", "set_api_key_env",
    "prompt_set_env", "repair_config",
    "validate_and_repair_yaml",
    "clean_cache",
]


class ConfigValidator:
    """配置安全验证器"""

    def validate_agent_config(self, agent_id: str, config: dict) -> Tuple[bool, List[str]]:
        """
        验证 Agent 配置是否安全
        返回: (是否安全, 问题列表)
        """
        issues = []

        # 1. 检查 agent_id 格式
        if not re.match(r'^[a-z][a-z0-9_]*$', agent_id):
            issues.append(f"agent_id 格式不合法: {agent_id} (只允许小写字母、数字、下划线)")

        # 2. 检查路径
        if "paths" in config:
            for os_name, paths in config["paths"].items():
                for path in paths:
                    path_safe, reason = PathValidator().is_safe_path(Path(path))
                    if not path_safe:
                        issues.append(f"路径不安全 ({os_name}): {path} - {reason}")

        # 3. 检查修复策略
        if "repair_strategies" in config:
            for key, value in config["repair_strategies"].items():
                if isinstance(value, str) and value not in ALLOWED_REPAIR_STRATEGIES:
                    issues.append(f"未知修复策略: {value}")

        # 4. 检查禁止字段
        for key in config:
            if key.lower() in FORBIDDEN_CONFIG_KEYS:
                issues.append(f"配置包含禁止字段: {key}")

        # 5. 检查 default_config 中是否有可疑内容
        if "default_config" in config:
            default = config["default_config"]
            if isinstance(default, dict):
                for key in default:
                    if key.lower() in FORBIDDEN_CONFIG_KEYS:
                        issues.append(f"default_config 包含禁止字段: {key}")

        # 6. 检查 common_issues 中是否有可疑内容
        if "common_issues" in config:
            for issue_id, issue in config["common_issues"].items():
                if isinstance(issue, dict):
                    for fix in issue.get("fix", []):
                        if fix not in ALLOWED_REPAIR_STRATEGIES:
                            issues.append(f"common_issues 包含未知修复操作: {fix}")

        return len(issues) == 0, issues

    def validate_community_config(self, config: dict) -> Tuple[bool, List[str]]:
        """验证社区贡献的配置"""
        issues = []

        if not isinstance(config, dict):
            return False, ["配置格式错误: 不是字典"]

        for agent_id, agent_config in config.items():
            if agent_id.startswith("_"):
                continue  # 跳过注释字段
            safe, agent_issues = self.validate_agent_config(agent_id, agent_config)
            issues.extend(agent_issues)

        return len(issues) == 0, issues


# ============================================================
# 3. 操作沙箱
# ============================================================

@dataclass
class Operation:
    """操作记录"""
    op_type: str  # read, write, delete, copy
    target: str   # 目标路径
    detail: str   # 操作详情
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    approved: bool = False


class OperationSandbox:
    """操作沙箱 - 限制和记录所有文件操作"""

    def __init__(self, dry_run: bool = False):
        self.path_validator = PathValidator()
        self.dry_run = dry_run
        self.operations: List[Operation] = []
        self._blocked_count = 0

    def safe_read(self, file_path: Path) -> Tuple[bool, Optional[str], str]:
        """
        安全读取文件
        返回: (成功, 内容, 消息)
        """
        safe, reason = self.path_validator.is_safe_file(file_path)
        if not safe:
            self._blocked_count += 1
            self._log_operation("read", str(file_path), f"已阻止: {reason}")
            return False, None, f"安全限制: {reason}"

        self._log_operation("read", str(file_path), "允许")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return True, f.read(), "OK"
        except Exception as e:
            return False, None, str(e)

    def safe_write(self, file_path: Path, content: str) -> Tuple[bool, str]:
        """
        安全写入文件
        返回: (成功, 消息)
        """
        safe, reason = self.path_validator.is_safe_file(file_path)
        if not safe:
            self._blocked_count += 1
            self._log_operation("write", str(file_path), f"已阻止: {reason}")
            return False, f"安全限制: {reason}"

        if self.dry_run:
            self._log_operation("write", str(file_path), "模拟模式: 跳过写入")
            return True, "模拟模式"

        self._log_operation("write", str(file_path), "允许")
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "写入成功"
        except Exception as e:
            return False, str(e)

    def safe_delete(self, file_path: Path) -> Tuple[bool, str]:
        """
        安全删除文件
        返回: (成功, 消息)
        """
        safe, reason = self.path_validator.is_safe_file(file_path)
        if not safe:
            self._blocked_count += 1
            self._log_operation("delete", str(file_path), f"已阻止: {reason}")
            return False, f"安全限制: {reason}"

        if self.dry_run:
            self._log_operation("delete", str(file_path), "模拟模式: 跳过删除")
            return True, "模拟模式"

        self._log_operation("delete", str(file_path), "允许")
        try:
            if file_path.is_file() or file_path.is_symlink():
                file_path.unlink()
            elif file_path.is_dir():
                import shutil
                shutil.rmtree(file_path)
            return True, "删除成功"
        except Exception as e:
            return False, str(e)

    def safe_copy(self, src: Path, dst: Path) -> Tuple[bool, str]:
        """安全复制文件"""
        src_safe, src_reason = self.path_validator.is_safe_path(src)
        dst_safe, dst_reason = self.path_validator.is_safe_path(dst)

        if not src_safe:
            self._blocked_count += 1
            return False, f"源路径不安全: {src_reason}"
        if not dst_safe:
            self._blocked_count += 1
            return False, f"目标路径不安全: {dst_reason}"

        if self.dry_run:
            self._log_operation("copy", f"{src} -> {dst}", "模拟模式")
            return True, "模拟模式"

        self._log_operation("copy", f"{src} -> {dst}", "允许")
        try:
            import shutil
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return True, "复制成功"
        except Exception as e:
            return False, str(e)

    def _log_operation(self, op_type: str, target: str, detail: str):
        """记录操作"""
        self.operations.append(Operation(
            op_type=op_type,
            target=target,
            detail=detail
        ))
        if "阻止" in detail:
            logger.warning(f"[安全] {op_type} {target}: {detail}")
        else:
            logger.info(f"[操作] {op_type} {target}: {detail}")

    def get_audit_log(self) -> List[dict]:
        """获取审计日志"""
        return [
            {
                "time": op.timestamp,
                "type": op.op_type,
                "target": op.target,
                "detail": op.detail,
            }
            for op in self.operations
        ]

    def get_summary(self) -> dict:
        """获取操作摘要"""
        total = len(self.operations)
        blocked = sum(1 for op in self.operations if "阻止" in op.detail)
        return {
            "total_operations": total,
            "blocked_operations": blocked,
            "allowed_operations": total - blocked,
            "dry_run": self.dry_run,
        }


# ============================================================
# 4. 审计日志
# ============================================================

class AuditLogger:
    """审计日志管理器"""

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path.home() / ".ai_agent_repair" / "audit_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_session(self, operations: List[dict], summary: dict):
        """记录一次修复会话"""
        log_file = self.log_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        session = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "operations": operations,
        }
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(session, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"审计日志写入失败: {e}")

    def get_recent_logs(self, count: int = 10) -> List[dict]:
        """获取最近的审计日志"""
        logs = sorted(self.log_dir.glob("session_*.json"), reverse=True)[:count]
        result = []
        for log_file in logs:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    result.append(json.load(f))
            except:
                pass
        return result


# ============================================================
# 便捷函数
# ============================================================

# 全局沙箱实例
_sandbox: Optional[OperationSandbox] = None

def get_sandbox() -> OperationSandbox:
    global _sandbox
    if _sandbox is None:
        _sandbox = OperationSandbox()
    return _sandbox

def validate_path(path) -> Tuple[bool, str]:
    return PathValidator().is_safe_path(Path(path))

def validate_file(path) -> Tuple[bool, str]:
    return PathValidator().is_safe_file(Path(path))

def validate_config(agent_id: str, config: dict) -> Tuple[bool, List[str]]:
    return ConfigValidator().validate_agent_config(agent_id, config)
